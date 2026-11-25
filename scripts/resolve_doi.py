#!/usr/bin/env python3
"""查询 Crossref 书目记录，并在本机比对可选字段。"""

# 实现依据：本仓库的 references/citation_evidence.md。
from __future__ import annotations

import argparse
import json
import math
import sys
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from validate_literature_table import normalize_doi, normalized_text


def positive_seconds(value: str) -> float:
    try:
        seconds = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("超时秒数须为正数。") from error
    if not math.isfinite(seconds) or seconds <= 0:
        raise argparse.ArgumentTypeError("超时秒数须为正数。")
    return seconds


def lookup(doi: str, timeout: float) -> dict:
    encoded_doi = quote(doi, safe="")
    request = Request(
        f"https://api.crossref.org/works/{encoded_doi}",
        headers={"User-Agent": "research-review-skill/1.0", "Accept": "application/json"},
    )
    with urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    if not isinstance(payload, dict) or not isinstance(payload.get("message"), dict):
        raise ValueError("响应缺少作品记录。")
    return payload["message"]


def publication_years(work: dict) -> set[int]:
    years = set()
    for field in ("published", "published-print", "published-online", "issued"):
        event = work.get(field) or {}
        parts = event.get("date-parts") or []
        if parts and parts[0] and isinstance(parts[0][0], int) and parts[0][0] > 0:
            years.add(parts[0][0])
    return years


def author_names(record: dict) -> tuple[str, ...]:
    given = record.get("given") or ""
    family = record.get("family") or ""
    organization = record.get("name") or ""
    return (f"{given} {family}".strip(), f"{family} {given}".strip(), family, organization)


def compare(work: dict, title: str | None, authors: list[str], year: int | None) -> bool:
    titles = [value for value in (work.get("title") or []) if value]
    records = work.get("author") or []
    years = publication_years(work)
    printed_authors = [author_names(record)[0] or author_names(record)[3] for record in records]
    print(f"Crossref 题名 {' / '.join(titles) or '未报告'}")
    print(f"Crossref 作者 {'；'.join(printed_authors) or '未报告'}")
    print(f"Crossref 发表年份 {'、'.join(map(str, sorted(years))) or '未报告'}")

    results = []
    if title is not None:
        normalized_titles = {normalized_text(value) for value in titles}
        expected = normalized_text(title)
        results.append(("题名", bool(expected) and expected in normalized_titles))
    if authors:
        expected_authors = [normalized_text(author) for author in authors]
        matches = len(records) >= len(authors) and all(
            expected and expected in {normalized_text(name) for name in author_names(record)}
            for expected, record in zip(expected_authors, records)
        )
        results.append(("作者", matches))
    if year is not None:
        results.append(("年份", year in years))

    for label, matched in results:
        print(f"{label}比对 {'一致' if matched else '不一致或记录缺失'}")
    if not results:
        print("未提供本地比对字段。")
    print("本结果覆盖 Crossref 书目信息。")
    return all(matched for _, matched in results)


def main() -> int:
    parser = argparse.ArgumentParser(description="查询公开 DOI，并比对 Crossref 题名、作者或年份。")
    parser.add_argument("doi", help="DOI、doi: 标识或 doi.org 链接")
    parser.add_argument("--title", help="要在本机比对的题名")
    parser.add_argument("--author", action="append", default=[], help="从首位作者起依序填写，可重复传入全名或姓")
    parser.add_argument("--year", type=int, help="要在本机比对的发表年份")
    parser.add_argument("--timeout", type=positive_seconds, default=10.0, help="一次请求的超时秒数")
    parser.add_argument("--offline", action="store_true", help="跳过在线查询")
    args = parser.parse_args()
    doi = normalize_doi(args.doi)
    if doi is None:
        parser.error("DOI 格式无效。")
    if args.year is not None and args.year < 1:
        parser.error("年份须为正整数。")
    if args.offline:
        print("离线模式，已跳过 Crossref 查询。该 DOI 仍待核验。")
        return 3

    try:
        work = lookup(doi, args.timeout)
        returned_doi = normalize_doi(work.get("DOI") or "")
        if returned_doi != doi:
            raise ValueError("返回记录中的 DOI 与查询标识不一致。")
        print(f"DOI https://doi.org/{quote(doi, safe='/')}")
        return 0 if compare(work, args.title, args.author, args.year) else 1
    except HTTPError as error:
        if error.code == 404:
            print("Crossref 未找到此 DOI。可查其他注册机构或出版方。", file=sys.stderr)
            return 4
        print(f"Crossref 请求未完成，HTTP {error.code}。保留待核验状态。", file=sys.stderr)
        return 3
    except (URLError, OSError, HTTPException, ValueError, AttributeError, TypeError, IndexError) as error:
        print(f"Crossref 查询或读取响应失败。保留待核验状态。{error}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
