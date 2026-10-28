# kb-platform — 知识库基盘（Phase 0）

把「公司级共通知识 + 项目级固有知识」放在同一个仓库里管理，并以检索 API 的形式提供的最小实现。
不依赖任何外部服务（仅 Python + numpy + SQLite），`git clone` 之后即可运行。

Phase 0 的目的是**验证方案**，不追求生产级的性能与精度。
走向生产的改造点见「[生产化迁移](#生产化迁移)」。

---

## 设计铁律

1. **Git 是唯一正本**。`repo/` 下的 Markdown 才是事实来源，索引随时可以丢弃重建。
2. **索引是派生物**。`data/kb.sqlite3` 已被 gitignore；损坏时用 `--reset` 重建。
3. **权限必须在 SQL 里先收窄**。不允许对检索结果做事后过滤（防止信息泄露）。
4. **只做增量入库**。文档 sha256 没变化就不重新索引。

---

## 环境要求

| 项目 | 要求 |
|---|---|
| Python | 3.10 以上（实测 3.14.3） |
| 依赖 | 仅 `numpy`（实测 2.4.6） |
| Shell | Git Bash / bash / PowerShell 均可 |
| 可选 | `fastapi` + `uvicorn`（仅在需要使用 `api.py` 时） |

```bash
python -c "import numpy; print(numpy.__version__)"
```

---

## 目录结构

```text
kb-platform/
├── README.md               日文版说明
├── readme_cn.md            本文件（中文版）
├── run.py                  CLI（lint / ingest / search / eval / stats）
├── api.py                  可选的 FastAPI 包装（需先安装 fastapi）
├── .gitignore
│
├── kbkit/
│   ├── fm.py               front matter（YAML 子集）解析器
│   ├── chunker.py          按标题 / 表行 / 代码块切分
│   ├── embedder.py         向量化（hash = 默认 / bge-m3 = 生产）
│   ├── store.py            SQLite 表结构与访问器
│   ├── retrieval.py        权限过滤 + RRF 融合 + rerank
│   ├── pipeline.py         lint / ingest / prune
│   └── eval.py             黄金集评估
│
├── repo/                   ★ 知识本体（Git 管理的正本）
│   ├── company/            全项目共通
│   │   ├── standards/      规范・标准
│   │   ├── glossary/       术语集
│   │   └── patterns/       设计模式
│   ├── projects/
│   │   └── <项目ID>/        项目固有（例: P-DEMO-001）
│   │       ├── requirements/
│   │       ├── design/basic/
│   │       ├── design/detail/
│   │       └── test/
│   └── eval/golden.yaml    检索质量黄金集
│
└── data/
    └── kb.sqlite3          索引（派生物 / gitignore）
```

`repo/eval/` 不参与索引。它被当作评估数据，而不是知识文档。

---

## 快速开始

```bash
cd d:/kb-platform

python run.py lint                                  # 1. 检查书写规则
python run.py ingest --all                          # 2. 建立索引
python run.py search "在庫不足のときのエラーコードは？" \
       --project P-DEMO-001 --context               # 3. 检索
python run.py eval --project P-DEMO-001             # 4. 质量评估
```

`run.py` 在任何目录下执行都可以（路径以 `run.py` 所在位置为基准解析）。

### 执行示例

```text
$ python run.py ingest --all
追加=7 更新=0 スキップ=0 チャンク=74
索引: 文書7 / チャンク74 / model=['hash-ngram-1024']

$ python run.py eval --project P-DEMO-001
cases=12  top_k=5  recall@5=1.000  MRR=0.917
...
しきい値 recall@5 >= 0.85: PASS
```

> CLI 的输出信息目前是日文。若需中文化，改 `run.py` / `kbkit/eval.py` 中的字符串即可，不影响逻辑。

---

## 命令参考

通用选项（所有子命令都可使用）:

| 选项 | 默认值 | 说明 |
|---|---|---|
| `--db` | `data/kb.sqlite3` | 索引文件 |
| `--repo` | `repo` | 知识库根目录 |
| `--embedder` | `hash` | `hash`（无依赖） / `bge`（需 sentence-transformers） |

### `lint` — 书写规则检查

```bash
python run.py lint
```

检查 front matter 必填项、枚举值、doc_id 唯一性，以及项目 ID 与存放目录是否一致。
只要发现 1 个问题就以退出码 1 结束（可直接放进 CI / pre-commit）。

### `ingest` — 写入索引

```bash
python run.py ingest              # 只处理有变更的文档
python run.py ingest --all        # 全量重建索引
python run.py ingest --reset      # 清空索引后重建
python run.py ingest --prune      # 仓库中已删除的文档同步从索引删除
```

`ingest` 对每篇文档执行「删除旧 chunk → 插入新 chunk」，并在同一个事务里完成。
中途失败也不会留下半截数据。

### `search` — 检索

```bash
python run.py search "楽観ロックに使うカラムは？" --project P-DEMO-001
python run.py search "..." --project P-DEMO-001 --top-k 10 --level 20
python run.py search "..." --project P-DEMO-001 --context   # 同时输出 LLM 用上下文
python run.py search "..." --json                            # 便于程序处理
```

| 选项 | 默认值 | 说明 |
|---|---|---|
| `--project` | 无 | 项目 ID。指定后检索范围为「公司共通 + 该项目」；不指定则只检索公司共通 |
| `--level` | `30` | 用户权限等级。只有 `conf_level <= level` 的文档会进入候选 |
| `--top-k` | `5` | 返回条数 |
| `--context` | off | 额外输出带引用的上下文文本 |

### `eval` — 黄金集评估

```bash
python run.py eval --project P-DEMO-001
python run.py eval --project P-DEMO-001 --top-k 10 --threshold 0.9
```

输出 `recall@k` 与 `MRR`。低于默认阈值 `recall@5 >= 0.85` 时以退出码 1 结束。

### `stats` — 索引状态

```bash
python run.py stats
```

显示文档数、chunk 数、按 scope 的分布、当前使用的向量模型，以及文档清单。

---

## 知识条目的写法

### front matter

每个 Markdown 文件开头必须写。

```yaml
---
doc_id: REQ-001                    # 唯一。仅限英数字与连字符
scope: project                     # company | project
project_id: P-DEMO-001             # scope=project 时必填
title: 受注・在庫引当システム 要件定義書
doc_type: requirement              # 见下方枚举值
phase: requirement                 # 可选（工程）
version: "1.0"                     # 建议加引号
status: active                     # draft | review | active | deprecated
conf_level: 30                     # 10 公开 / 20 公司内 / 30 项目内 / 40 机密
owner: 要件定義チーム
updated_at: 2026-09-02
tags: [order, allocation]
---
```

| 键 | 必填 | 内容 |
|---|---|---|
| `doc_id` | ○ | chunk ID 与引用的基准，之后不要再改 |
| `scope` | ○ | `company` / `project` |
| `project_id` | △ | `scope=project` 时必填，且必须与目录名一致 |
| `title` | ○ | 4 个字符以上，用于检索结果引用 |
| `doc_type` | ○ | 见下方枚举值 |
| `version` | ○ | 设计书版本 |
| `status` | ○ | 非 `active` 的文档不参与检索 |
| `conf_level` | ○ | 10 / 20 / 30 / 40 |
| `updated_at` | ○ | `YYYY-MM-DD` |
| `phase` / `owner` / `tags` | - | 可选 |

`doc_type` 枚举值:

`standard` / `pattern` / `glossary` / `requirement` / `design-basic` /
`design-detail` / `test` / `decision` / `incident` / `howto`

### 存放规则

| scope | 存放位置 | 示例 |
|---|---|---|
| `company` | `repo/company/<类别>/<任意>/` | `repo/company/standards/coding/general.md` |
| `project` | `repo/projects/<项目ID>/<工程>/` | `repo/projects/P-DEMO-001/design/basic/BS-001.md` |

`lint` 会检测 `project_id` 与存放目录是否一致。

### 正文的写法

chunk 的质量取决于正文结构。

- **1 个标题 = 1 个主题**。标题本身也参与检索，要把业务词写进去。
- **表格是 1 行 = 1 个 chunk**。科目、错误码、项目定义一律做成表格。
  表头行会被复制进每个 chunk，所以列名要有语义（例: `| コード | 内容 | 発生箇所 |`）。
- **每条列表项写 1 句话**。过长的段落会被切分。
- 图、Excel、PDF 不要原样放进来：先把内容文本化成 Markdown 摘要，并在正文里留下原文件路径。

---

## 索引构建机制

```text
扫描 *.md（排除 repo/eval）
  → 解析 front matter
  → 计算 sha256 → 与上次相同则跳过
  → 切分 chunk（标题 / 表行 / 代码块）
  → 向量化
  → 删除旧 chunk → 插入（1 个事务）
```

chunk 切分规则:

| 单位 | 条件 | 备注 |
|---|---|---|
| 标题章节 | `#` 〜 `######` | 过长时按 700 字符再切段 |
| 表格行 | 表头 + 1 行 | 对术语集、错误码表最有效 |
| 代码块 | 由代码围栏包围的范围 | 不切分 |

更换 chunker 或向量模型后，必须用 `--all` 重建索引
（sha256 是正文的哈希，代码改动不会被识别为文档变更）。

---

## 检索机制

```text
查询
  → 在 SQL 里收窄候选（status / conf_level / scope / project_id）
  → dense（余弦相似度）
  → sparse（字符 bigram 的 IDF 加权覆盖率）
  → RRF 融合（k=60）
  → rerank（正文覆盖 +0.30 / 标题 +0.10 / 文档名 +0.05）
  → 返回带引用的 top_k
```

**权限过滤写在取候选的 SQL 的 WHERE 子句里**。
不是排序之后再剔除，因此越权文档根本不会参与打分。

当前向量化使用字符 n-gram 哈希（`hash-ngram-1024`），对同义词、换种说法比较弱。
这个短板在生产环境换成 bge-m3 后即可解决。

---

## 评估（黄金集）

在 `repo/eval/golden.yaml` 里写「问题 → 期望命中的文档 ID」。

```yaml
- id: Q002
  question: 在庫不足を表すエラーコードは何番か
  expect: [REQ-001, BS-001]
  project: P-DEMO-001        # 省略时使用 --project 的值
```

| 指标 | 含义 | 目标 |
|---|---|---|
| `recall@k` | 期望文档至少 1 篇进入 top-k 的问题占比 | **0.85 以上** |
| `MRR` | 首次命中排名的倒数平均值 | 参考值（0.8 以上为宜） |

运用规则:

- 每个项目准备 **10 条以上**，覆盖需求、设计、测试、术语各个层次。
- 黄金集是为了**暴露检索短板**。禁止删掉答不对的问题来「通过」。
- 新增文档就要新增问题。评估落后于实际内容就失去意义了。

---

## 新项目启动步骤

| # | 作业 | 完成条件 |
|---|---|---|
| 1 | 创建 `repo/projects/<项目ID>/` | 具备 `requirements` / `design/basic` / `design/detail` / `test` 四个目录 |
| 2 | 用 Markdown + front matter 放入 kickoff 资料 | 需求、基本设计、术语、非功能四项齐全 |
| 3 | `python run.py lint` | 0 个问题 |
| 4 | `python run.py ingest` | 0 个错误 |
| 5 | 在 `repo/eval/golden.yaml` 增加 10 条以上该项目的问题 | 每条都有 `expect` |
| 6 | `python run.py eval --project <项目ID>` | `recall@5 >= 0.85` |
| 7 | 之后文档有更新就执行 `ingest` | 增量处理，数秒完成 |

### 日常运用

- 文档变更走 Pull Request，CI 上跑 `lint` 与 `eval`。
- 把「同一个问题问两次得到同一个答案」作为最低质量线。
- 项目结束时，可复用到其他项目的文档升格到 `company/`。
  升格时把专有名词、客户名、真实数据泛化，并下调 `conf_level`。

---

## 生产化迁移

| 项目 | Phase 0 | 生产 |
|---|---|---|
| 向量化 | `hash-ngram-1024` | `bge-m3`（日英中，dense + sparse） |
| 向量库 | SQLite + 全量扫描 | Oracle 23ai `VECTOR` 或 Qdrant |
| API | CLI / `api.py` | 用 `build_router()` 合入既有 FastAPI |
| 权限 | `conf_level` 数值比较 | 文档级 ACL（对接项目成员表） |
| CI | 本地执行 | 合并前强制 `lint` + `eval` |

迁移时不要变的东西:

- `repo/` 的目录结构与 front matter 的 schema
- 「先用 SQL 收窄候选」这一检索形态（换成 `VECTOR_DISTANCE` 后 WHERE 里的权限条件仍要保留）
- 黄金集与评估指标

### 更换向量模型

```bash
pip install sentence-transformers
python run.py ingest --all --embedder bge
python run.py eval --embedder bge --project P-DEMO-001
```

`hash` 与 `bge` 的索引不能混用。切换后必须 `--all`（或 `--reset`）。

---

## API（可选）

未安装 `fastapi` 的环境无法 import `api.py`（不影响 `run.py`）。

```bash
pip install fastapi uvicorn
uvicorn api:app --host 127.0.0.1 --port 8000
```

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/kb/search` | 检索（`query`, `project_id`, `user_level`, `top_k`, `with_context`） |
| GET | `/kb/stats` | 索引状态 |

合入既有应用时:

```python
from api import build_router
app.include_router(build_router("d:/kb-platform/data/kb.sqlite3"))
```

`api.py` 不带认证。务必部署在公司内网认证之后，并且 `user_level` 要由服务端根据
已认证用户信息决定（不要直接采用客户端传来的值）。

---

## 故障排查

| 症状 | 原因与处理 |
|---|---|
| `front matter が '---' で閉じられていません` | 检查开头 `---` 与结尾 `---` 是否成对 |
| `doc_id 'X' が ... と重複` | 有两篇文档用了同一个 doc_id，改掉其中一个 |
| `project_id '...' と配置先ディレクトリが不一致` | 移到 `repo/projects/<项目ID>/` 下，或修正 front matter |
| `scope=project には project_id が必須です` | 在 front matter 里补 `project_id` |
| 检索结果为 0 条 | 未执行 ingest / `--project` 指定不同 / `conf_level` 大于 `--level` |
| 改了文档但结果没变 | 没执行 `ingest`，或改过 chunker 后没做 `--all` |
| 引用里的标题不对 | 检查标题层级（`#` 的级数）后执行 `ingest --all` |
| `ModuleNotFoundError: fastapi` | 只有用 `api.py` 时才需要 `pip install fastapi uvicorn` |

---

## 已知限制（Phase 0）

- 向量化是字符 n-gram 哈希，对表述差异、同义词、改写比较弱。
- SQLite 全量扫描，实用上限约 1 万个 chunk。
- 文档级 ACL、审计日志、向量增量更新尚未实现。
- `api.py` 没有认证与限流。

---

## 参考

- 构建指南（案件起点）: `d:/JET/doc/03_AI/知識ベース構築ガイド_案件起点.md`
- 黄金集: `repo/eval/golden.yaml`
