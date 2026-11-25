#!/usr/bin/env python3
"""检查研究综述文献表的结构和引用字段。"""

# 实现依据：本仓库的 assets/literature_table_template.csv。
from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlsplit


METADATA_FIELDS = ("# 主题", "# 检索日期", "# 数据源", "# 范围", "# 假设")
COLUMNS = (
    "id", "作者", "年份", "标题", "期刊/会议", "文献类型", "研究内容", "研究方法",
    "样本/数据/对象", "主要观点或结论", "不足", "所属理论假设或流派", "证据等级",
    "核验状态", "DOI/URL", "与其他文献的关系备注",
)
STATUSES = ("[全文核验]", "[摘要/元数据核验]", "[待核验]")
DOI_HOSTS = {"doi.org", "dx.doi.org"}
DOI_PATTERN = re.compile(r"10\.[0-9]{4,9}(?:\.[0-9]+)*/[^\s\x00-\x1f\x7f]+")
UNDATED = {"未载年份", "n.d."}
PLACEHOLDERS = {"…", "……", "...", "待填", "待填充", "todo", "tbd"}


def normalized_text(value: str) -> str:
    """为标题及姓名的比较保留文字与数字。"""
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum())


def normalize_doi(value: str) -> str | None:
    """将 DOI 字符串或 DOI 链接转换为可比较的标识。"""
    doi = value.strip()
    if doi[:4].casefold() == "doi:":
        doi = doi[4:].strip()
    if doi.casefold().startswith(("https://", "http://")):
        try:
            url = urlsplit(doi)
        except ValueError:
            return None
        if url.hostname not in DOI_HOSTS or url.username is not None:
            return None
        doi = unquote(url.path[1:])
    if DOI_PATTERN.fullmatch(doi):
        return doi.casefold()
    return None


def has_valid_locator(value: str) -> bool:
    if normalize_doi(value):
        return True
    if any(character.isspace() or ord(character) < 32 for character in value):
        return False
    try:
        url = urlsplit(value)
        if url.scheme in {"http", "https"}:
            return (
                bool(url.hostname)
                and url.hostname not in DOI_HOSTS
                and url.username is None
                and url.port != 0
            )
        return (
            url.scheme == "file"
            and url.netloc in {"", "localhost"}
            and url.path.startswith("/")
        )
    except ValueError:
        return False


@dataclass
class TableReport:
    row_count: int = 0
    undated_count: int = 0
    status_counts: Counter = field(default_factory=Counter)
    errors: list[str] = field(default_factory=list)


def read_header(reader, report: TableReport) -> list[str]:
    row = next(reader, [])
    if row and row[0].strip().startswith("#"):
        for field_name in METADATA_FIELDS:
            if len(row) != 2 or row[0].strip() != field_name or not row[1].strip():
                report.errors.append(f"元信息前缀需要填写 {field_name!r} 的两列记录。")
            row = next(reader, [])

    header = [value.strip() for value in row]
    if len(header) != len(set(header)):
        report.errors.append("列头含重复字段。")
    if "" in header:
        report.errors.append("列头含无名称的字段。")
    absent = [name for name in COLUMNS if name not in header]
    if absent:
        report.errors.append(f"缺少必填列 {'、'.join(absent)}。")
    return header


def record_identity(
    value: str | None, label: str, line: int, seen: dict[str, int], report: TableReport
) -> None:
    if not value:
        return
    first_line = seen.setdefault(value, line)
    if first_line != line:
        report.errors.append(f"第 {line} 行的{label}重复，首次出现于第 {first_line} 行。")


def validate_table(path: Path, current_year: int) -> TableReport:
    report = TableReport()
    seen_ids: dict[str, int] = {}
    seen_titles: dict[str, int] = {}
    seen_dois: dict[str, int] = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        header = read_header(reader, report)
        if report.errors:
            return report

        for row in reader:
            if not row:
                continue
            line = reader.line_num
            report.row_count += 1
            if len(row) != len(header):
                report.errors.append(f"第 {line} 行有 {len(row)} 个字段，应有 {len(header)} 个。")
                continue

            entry = {column: value.strip() for column, value in zip(header, row)}
            empty = [name for name in COLUMNS if not entry[name] or entry[name].casefold() in PLACEHOLDERS]
            if empty:
                report.errors.append(f"第 {line} 行缺少有效字段 {'、'.join(empty)}。")

            year = entry["年份"]
            if year.casefold() in UNDATED:
                report.undated_count += 1
            elif not re.fullmatch(r"[0-9]{1,4}", year) or not 1 <= int(year) <= current_year:
                report.errors.append(f"第 {line} 行年份 {year!r} 不在 1–{current_year} 内，也未填无日期标记。")

            status = entry["核验状态"]
            if status in STATUSES:
                report.status_counts[status] += 1
            if status not in STATUSES:
                report.errors.append(f"第 {line} 行核验状态 {status!r} 无效。")
            elif status == STATUSES[2]:
                report.errors.append(f"第 {line} 行是待核验线索，请移至待核验清单。")

            locator = entry["DOI/URL"]
            if not has_valid_locator(locator):
                report.errors.append(f"第 {line} 行 DOI/URL {locator!r} 格式无效。")

            record_identity(entry["id"].casefold(), "编号", line, seen_ids, report)
            record_identity(normalized_text(entry["标题"]), "标题", line, seen_titles, report)
            record_identity(normalize_doi(locator), "DOI", line, seen_dois, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="检查文献 CSV 的必填字段、重复项、年份、DOI/URL 和核验状态。"
    )
    parser.add_argument("csv_file", type=Path, metavar="CSV", help="文献表路径，可包含模板中的五条元信息")
    args = parser.parse_args()

    try:
        report = validate_table(args.csv_file, date.today().year)
    except (OSError, UnicodeError, csv.Error) as error:
        print(f"无法读取 CSV {args.csv_file!s}。{error}", file=sys.stderr)
        return 2

    print(f"记录 {report.row_count} 条，无日期 {report.undated_count} 条。")
    for status in STATUSES:
        print(f"{status} {report.status_counts[status]} 条")
    for error in report.errors:
        print(error, file=sys.stderr)
    if report.errors:
        print(f"校验未通过，共 {len(report.errors)} 项问题。", file=sys.stderr)
        return 1

    print("格式校验通过。引文内容与来源须另行核验。")
    if report.row_count == 0:
        print("数据表为空，目前没有可计数的纳入证据。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
