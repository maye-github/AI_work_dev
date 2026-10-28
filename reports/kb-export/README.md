# reports/kb-export/ — 给 kb-platform 的导出件

## 这是什么

把本仓库 `docs/90_knowledge/legacy-r60/` 的 22 篇知识 `.md`，转成社内知识库
`D:\AI_platform\kb-platform` 能直接吃进去的格式。**这里是中转站，不是正本。**

- **正本**：`docs/90_knowledge/legacy-r60/**/*.md`（本仓库，git 管理）
- **派生物**：本目录下的 `projects/P-R60-001/`（**已在 `.gitignore` 里，不进 git**）

`projects/` 下的文件**不要手改**——下次导出会整目录删掉重写。

## 怎么生成

```bash
py -3 -m tools.kb_export                        # 只看会导出什么，不写盘
py -3 -m tools.kb_export --out reports/kb-export --check   # 写盘并做规则检查
```

`--check` 跑的是 kb-platform `kbkit/pipeline.py` 的 lint 规则（8 个必填字段、枚举值、
`project_id` 与目录一致性、正文非空）。**本机没装 numpy，跑不了 kb-platform 自己的 lint**，
所以这边照着它的规则写了一份等价检查。装了 numpy 的机器可以跑本家的：

```bash
py -3 -m tools.kb_export --out reports/kb-export --kb D:/AI_platform/kb-platform
```

## 字段怎么对应（这是唯一需要人看一眼的地方）

| kb-platform 要的 | 本仓库给的 | 怎么来的 |
|---|---|---|
| `doc_id` | `id` | 原样（`KNOW-LEGACY-R60-*`） |
| `scope` | — | 固定 `project` |
| `project_id` | — | 固定 `P-R60-001`（`--project-id` 可改） |
| `title` | 正文第一个 `# ` 标题 | 自动取 |
| `doc_type` | — | 按路径决定：`screens/*`→`design-basic`、`03-conventions`→`standard`、`08-deviations`→`decision`… |
| `version` | `version` | 原样 |
| `status` | `status` | `draft→draft`、`baselined/done→active`、`changed→review`、`void→deprecated` |
| `conf_level` | `sensitivity` | `internal→30`（案件级）。**没有一篇是 10（公开）** |
| `updated_at` | — | **git 里该文件的最后提交日**，不是今天。同样的仓库状态导出多少次都一样 |

22 篇的 `status` 全是 `draft`。这是事实：它们都还是草稿，没有一篇经过人承认。

## 还没做的事（需要你点头）

**把导出件拷进 `D:\AI_platform\kb-platform\repo\` 并跑 `ingest`——我没有做。**
理由：那是另一个项目，写进去就等于改了它的知识库正本，撤不回来。
要做的时候是一步：

```bash
py -3 -m tools.kb_export --out D:/AI_platform/kb-platform/repo --check
cd /d/AI_platform/kb-platform && py -3 run.py ingest
```

> 导出只删改 `repo/projects/P-R60-001/` 这一棵子树，**其他案件（如 P-DEMO-001）不会被动到**。

## 两件不要搞混的事

1. **这些知识只有 `build_mode: migration` 的案件才用**（R60 是既有系统改造）。
   默认的 `greenfield`（从无到有）案件不该参考它。
2. **`reports/legacy-raw/` 的 263 个原始抽取文件不在导出范围**。
   那是旧系统设计书的生文本，里面有案件可识别的实数据，
   不是消化过的知识，也不该进共享知识库。
