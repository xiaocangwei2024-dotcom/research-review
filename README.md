# research-review

面向 Claude Code 和 Codex 的文献综述技能。从一个研究问题或一批已有材料开始，设计检索、筛选文献、比较证据，并把研究空白转成可检验的问题。可以只做一个环节，也可以交付一套从检索日志到综述正文的文件。〔功能依据：[SKILL.md](SKILL.md)〕

## 安装

在 GitHub 仓库页打开 **Code**，下载 ZIP 或复制 Git 地址进行克隆。取得仓库后，按使用范围选择下表中的目录。〔操作来源：[GitHub 下载说明](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives)〕

| 使用环境 | 仅用于当前研究项目 | 用于本机多个项目 |
| --- | --- | --- |
| Claude Code | 项目根目录下的 `.claude/skills/research-review/` | `~/.claude/skills/research-review/` |
| Codex | 项目根目录下的 `.agents/skills/research-review/` | `~/.agents/skills/research-review/` |

将 `SKILL.md`、`README.md`、`references/`、`assets/` 和 `scripts/` 放到所选目录，保留相对结构。下面是在 macOS 或 Linux 中从下载后的仓库根目录执行的个人级安装示例。要安装到某个研究项目，将第一行替换成该项目的实际技能目录。复制完成后，从研究项目开启新会话。〔目录与加载依据：[Claude Code 技能文档](https://code.claude.com/docs/en/skills) · [Codex 技能文档](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)〕

```bash
skill_target="$HOME/.claude/skills/research-review"
# Codex 个人级安装可将上行改为 skill_target="$HOME/.agents/skills/research-review"
mkdir -p "$skill_target"
cp -R SKILL.md README.md references assets scripts "$skill_target/"
```

技能通过宿主已有的检索和文件工具工作。文献表校验和 DOI 比对脚本使用 Python 3，无需安装第三方 Python 库。〔实现依据：[访问和证据边界](SKILL.md#访问和证据边界) · [本地脚本](scripts/)〕

## 使用

在 Claude Code 中输入 `/research-review`。在 Codex CLI 或 IDE 扩展中，键入 `$` 并选择 `research-review`，也可通过 `/skills` 找到它。描述综述任务时，宿主也可根据技能说明自动选择。〔调用依据：[Claude Code 技能文档](https://code.claude.com/docs/en/skills) · [Codex 技能文档](https://learn.chatgpt.com/docs/build-skills#how-chatgpt-and-codex-use-skills)〕

### 示例一 · 先拟检索策略

```text
/research-review 请为「校园共享单车站点的步行距离与使用频率」制定检索策略。
先给四类中英文关键词、布尔检索式和纳入排除标准。本轮只拟方案。
```

这类请求走快速档，先交付可执行的检索方案，并标明编制日期及检索执行状态。〔示例与输出依据：[检索策略](references/search_strategy.md)〕

### 示例二 · 用已有材料做比较

```text
$research-review 请根据我已提供的 PDF 和题录，比较研究对象、测量方式和主要结论。
标出哪些结果存在分歧、有哪些可核对的解释，并列出两条可检验的研究问题。
本轮仅使用我提供的材料。
```

同样可以从初稿开始，请技能按研究阶段和主题重组文献，并标明原稿里待核验的引文。〔示例与输出依据：[批判性评估](references/critical_appraisal.md) · [综述写作](references/review_writing.md)〕

### 示例三 · 交付完整综述

```text
用 research-review 完整档梳理「校园共享单车站点的步行距离与使用频率」。
以高校学生为主要对象，检索中英文研究。记录检索日期、来源、筛选规则和纳排理由。
按中文学术综述写作，交付文献表、学术地图、研究空白、正文和质检报告。
```

最低输入是一个研究问题或主题。也可以指定时间范围、语种、目标读者、综述类型、引用体例，或提供 PDF、DOCX、BibTeX 和初稿。默认采用叙述性综述，输出跟随提问语言，中文引文使用 GB/T 7714，英文引文使用 APA 7。〔输入与默认值依据：[入口与假设](SKILL.md#入口与假设) · [引用与证据](references/citation_evidence.md)〕

## 交付结果

快速档直接回复所选环节的结果。完整档在研究项目下写入 `research_review_output/<主题-slug>/`，按下表组织文件。〔依据：[交付契约](SKILL.md#交付契约)〕

| 文件 | 内容 |
| --- | --- |
| `01_search_plan.md` | 关键词、实际或拟执行的检索式、数据源、时间和纳排标准 |
| `02_screening_log.md` | 候选记录、去重和版本关系、筛选决定及理由 |
| `03_literature_table.csv` | 16 个字段，含文献编号、方法、结论、证据等级和核验状态 |
| `04_academic_map.md` | Mermaid 时间线、主要议题、共享假设、分歧与归因 |
| `05_gap_analysis.md` | 证据局限、支持各空白的文献编号及可检验问题 |
| `06_review_draft.md` | 四部分的综述正文、Mermaid 理论框架图和参考文献 |
| `07_qa_report.md` | 引文与结构复核、文献表校验结果、检索局限和未决事项 |

## 工作流程

1. 先明确问题、时间边界和交付档位，再将检索词拆成对象、变量、概念与情境。〔依据：[检索策略](references/search_strategy.md)〕
2. 记录实际查询与筛选决定。沿着已纳入文献的参考文献和被引记录补查，核对重复版本。〔依据：[检索与筛选约定](references/search_strategy.md#记录与追溯)〕
3. 用稳定编号连接文献笔记、关系图和正文。比较研究假设、对象、方法及语境，给每项成立的空白写明证据和可检验的问题。〔依据：[批判性评估](references/critical_appraisal.md)〕
4. 依次写研究背景、按主题组织的主体、批判性总结和展望，再核对引用编号、原文位置和表格结构。〔依据：[综述写作](references/review_writing.md) · [引用与证据](references/citation_evidence.md)〕

## 证据与质检

用 `[全文核验]`、`[摘要/元数据核验]` 或 `[待核验]` 记录实际读取层级。只有元数据时，所能确认的是书目信息。待核验线索单独列出。离线模式只使用用户提供的材料，在线检索只发送所需的非敏感检索词。〔依据：[引用与证据](references/citation_evidence.md) · [访问和证据边界](SKILL.md#访问和证据边界)〕

以下命令从仓库或技能目录运行。文献表脚本检查字段、重复、年份、定位符和核验状态。替换示例路径为实际生成的文献表。填写时可从模板开始。〔依据：[校验脚本](scripts/validate_literature_table.py) · [文献表模板](assets/literature_table_template.csv)〕

```bash
python3 scripts/validate_literature_table.py --help
python3 scripts/validate_literature_table.py "/path/to/03_literature_table.csv"
```

DOI 对照脚本向 Crossref 查询公开 DOI，在本地比较题名、作者与发表年。给出的示例来自 PLOS Medicine 的书目记录。离线使用时可加 `--offline`。〔依据：[DOI 比对脚本](scripts/resolve_doi.py) · [Ioannidis（2005）出版记录](https://doi.org/10.1371/journal.pmed.0020124)〕

```bash
python3 scripts/resolve_doi.py --help
python3 scripts/resolve_doi.py 10.1371/journal.pmed.0020124 \
  --title "Why Most Published Research Findings Are False" \
  --author "Ioannidis" --year 2005
```

## 仓库结构

```text
research-review/
├── README.md
├── SKILL.md
├── .gitignore
├── references/
│   ├── search_strategy.md
│   ├── review_writing.md
│   ├── critical_appraisal.md
│   └── citation_evidence.md
├── assets/
│   ├── literature_table_template.csv
│   ├── review_outline_template.md
│   └── framework_diagram_template.md
└── scripts/
    ├── validate_literature_table.py
    └── resolve_doi.py
```

入口定义阶段、输出格式与适用范围。参考资料提供对应阶段的细则，模板供生成文件使用。〔依据：[技能入口](SKILL.md) · [参考资料](references/) · [模板](assets/)〕

## 文档参考

README 的安装、调用和示例编排参考了 Academic Humanizer 的说明。〔文档参考：[Academic Humanizer README](https://github.com/AIScientists-Dev/academic-humanizer/blob/main/README.md)〕
