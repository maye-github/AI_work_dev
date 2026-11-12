# AI 全流程开发步骤正式落地（朝日ビール R60 共通マスタ实战化） - Implementation Plan

> **★状態（2026-10-28 追記）**: 本文件は**建設記録**である。ここに並ぶタスクは**すべて 2026-10 に落地済み**で、
> 受入の判定は `reports/AC-selfcheck.md`（全緑）と `py -3 -m tools.trace_check --strict`（Exit 0）で行う。
> 下の `- [ ]` は**原稿のまま残している**（完了後に一括で書き換えると、当時の作業順序の記録が失われるため）。
> **「未着手の計画」と読まないこと。** 現在の計画は `docs/00_plan/spec.md` と `使用手册.md` の「分期」にある。

> **⚠ 訂正注記（2026-10-12 追記）** — 本文件は旧 Trae 期の実施計画書である。計画時点の記述を
> 歴史的記録として残しつつ、**実際と食い違う箇所のみ**以下を訂正した。混同すると誤った場所に
> 資産を作る／存在しないファイルを探すため、訂正箇所を先に列挙する。
>
> 1. **落地先**: 原文の `D:\AI_work` は **R60/JET の歴史案件（参照元）** であり落地先ではない。
>    本骨架の実際の落地先は **`D:\AI_work_dev`**。落地先として書かれた記述のみ訂正した。
>    （`doc/02_INPUT/` 等、参照元としての記述はそのまま維持）
> 2. **trace_check の実体**: 原文は「単一ファイル `tools/trace_check.py`」を実体として書いているが、
>    **実体は `tools/trace_check/` パッケージ**（`__init__.py` + `__main__.py` + `secret_patterns.example.json`）。
>    `tools/trace_check.py` は**後方互換の薄いランチャー**として残置されており、パッケージへ委譲する
>    だけの 18 行である。両形式とも動作するが、**正規の呼び出しは `py -3 -m tools.trace_check`** とし、
>    ランチャーは旧表記の互換のためだけに存在する（削除も可、ただし本訂正では触らない）。
> 3. **コマンド統一**: ローカル（Windows／社内網）は **`py -3 -m tools.xxx`**、CI（ubuntu-latest）は
>    **`python -m tools.xxx`** を用いる。裸の `python`（Windows）は Microsoft Store スタブに
>    解決される場合があり起動しない。原文の `python tools/xxx.py` および `python -m tools.xxx`
>    表記は、この規則に合わせて統一した（CI 文脈の 1 箇所のみ `python -m` を残置）。
> 4. **失効参照**: 原文の `project_memory.md §18-§26（241 行·26 章）` は失効。知識庫は
>    `D:\TraeWork_memory\`（`project_memory.md` は現在 11 行）。`D:\maye\*` は実在しない。
> 5. **Non-Goals の遵守**: 本計画は計画であり、実施済み／未実施の区別は
>    `reports/AC-selfcheck.md` と `reports/DELIVERY_MEMO.md` を正とする。本ファイルは更新しない。

## Task 1: 初始化骨架目录与忽略配置
- **Status**: `pending`
- **Priority**: high
- **Depends On**: None
- **Description**:
  - 在 `D:\AI_work_dev` 项目根创建本次骨架所需的全部空目录：`.claude/rules/`、`.claude/skills/code-from-design-trans-cosmos-ai/`、`docs/00_registry/`、`docs/01_context/`、`docs/10_requirements/`、`docs/20_basic_design/`、`docs/30_detail_design/`、`docs/40_framework/`、`docs/50_unit_test/`、`docs/60_integration_test/`、`docs/70_release/`、`docs/80_operation/`、`tools/kb-platform/repo/projects/P-R60-001/review/R60Area/`、`tools/kb-platform/repo/projects/P-R60-001/review/R60Code/`、`tools/kb-platform/repo/projects/P-R60-001/review/R60Item/`、`tools/trace_check/`、`tools/gen_formal/`、`tools/masking/`、`.github/workflows/`、`reports/`
  - 在项目根 `.gitignore` 追加「AI骨架可选忽略块」，使所有新文件默认不入库，设置环境变量 `AI_FULL_LIFECYCLE=1` 时才纳入；确认 `tools/masking/masking_dict.json` 被忽略
  - 在 `.gitignore` 追加 `reports/` 与 `docs/00_plan/*.bak` 忽略规则
- **Acceptance Criteria Addressed**: AC-1, NFR-5
- **Test Requirements**:
  - `rule` TR-1.1: `Test-Path` 或 `ls -d` 枚举 19 个目录全部存在，退出码 0
  - `rule` TR-1.2: `.gitignore` 中同时存在「AI_FULL_LIFECYCLE 条件块」与「masking_dict.json 忽略行」两条，`grep -c` 命中 >= 2
  - `rule` TR-1.3: `src/`、`api/fastapi_oracle_pjt/app/routers/` 目录未发生任何文件新增或修改（git diff --name-only 无该路径）

## Task 2: 产出 .claude/rules 七份规则文档
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1
- **Description**:
  - 编写 7 份规则 Markdown，每份均包含 YAML front-matter（id/type/req_ids/status/sensitivity/owner/version）七字段
  - `06-knowledge-flywheel.md`（**2026-10-22 追加**。当初計画は 6 份だった。社内実績 PPT の「踩坑 → 規則化 → 検査追加 → 全隊免疫」を規則層へ写像したもの。**紅线は 7 条のまま増やさず、横断規則は rules 側へ置く**という判断の受け皿でもある）
  - `00-project-global.md`：10 条项目级硬约束（暗号化方式は案件ごとに確定 / Oracle NLS / PrimeVue Select / Blob 拦截 / ROWID 分页 / ID 严禁野号 / 7 种 commit 格式 / 不造 parallel 共通库 / trace_check 必跑 / Phase1 基线），每条引用 spec.md Constraints 行号
  - `02-requirements.md`：8 工程·R-ID 发号 SOP·Q-ID 确认票·front-matter 七字段检查·status 状态机（draft→open→baselined→changed→done）·void 作废标记使用时机
  - `03-design-coding.md`：BaseCamelModel 4 行 model_config 固定写法 · R60Common.ts 54+ 函数调用签名映射表 · snake/camel 命名分区规则（snake=Python/定义层 / camel=TS/接口层）·SQL 白名单注入防护（ALLOWED_SORT_FIELDS）
  - `04-testing.md`：TC 正常 3/境界 2/异常 3 比例最低标准 · 入出力 I-ID 必须在 design_ids 列出 · trace_check 双向闭环不缺 · AB_Reports 健康度阈值记录位置
  - `05-commit-messages.md`：7 种 commit（req/design/feat/test/fix/rel/chore）示例 · Trace: R-ID/F-ID/L-ID 必带 · AI: skill@ver · Review: reviewer 三段式 · Tag baseline/R-xxx/basic-v1.0 命名约定
  - `01-security-redlines.md`：3 级机密清单（公开可 / 需脱敏 / 禁止外投）覆盖 13 敏感点：Oracle DB 连接串/Auth0 Domain/Audience/AWS S3 Bucket/AWS Profile/员工代码加密 Key/日付規約 .env 中的所有密码/内部 IP 段（IP_1/16 段）/社内メールアドレス/データベーススキーマオブジェクト名/R60 实际 32 模块业务数据值/緊急配信トリガー条件（条件式として書かれた形のみ検出対象。規則 01 §11）/R60_DECRYPTION_FNC 调用参数；每条禁止外投项附一句「脱敏替代占位规则」
- **Acceptance Criteria Addressed**: AC-1, AC-4, FR-1, FR-4, NFR-2
- **Test Requirements**:
  - `rule` TR-2.1: 7 份 md 都存在，且每份 `head -10` 中 7 字段 front-matter 齐全，`grep -c "^id: "` == 7
  - `rule` TR-2.2: `01-security-redlines.md` 中 `Level: 禁止外投` 条目数 >= 13，每条包含「脱敏占位」子段落
  - `rule` TR-2.3: `03-design-coding.md` 中 BaseCamelModel alias_generator=to_camel 示例存在；snake/camel 分区表列出 >= 8 条示例（如 cmp_cd vs cmpCd）

## Task 3: 产出 code-from-design-trans-cosmos-ai Skill 与双工具桥梁文件
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 2
- **Description**:
  - `.claude/skills/code-from-design-trans-cosmos-ai/SKILL.md`：完整 4 件套 Skill（R-ID 受理→BD/DD 双向生成→制造→trace_check 验证闭环），每条 skill step 引用 R60Common.ts 具体函数名或 r60const.py ACTION_ID；包含 R60Area 最简贯通示例（从 spec 读 F-042→调用 R60AreaService.ts 7 个 HTTP 方法签名）
  - `CLAUDE.md`（单工具真源，Claude Code 唯一入口，长度≥40行）：第 1 段必含关键词「落地篇 30 页」「7 条红线」；8 工程すべて Claude Code が実行し、人はレビュー・承認ゲート（要件合意・設計評審・合否判定・リリース判定）で拍板する分工红线明确；Git 仓库 + CLAUDE.md 連携手順；禁止事项 5 条（案件固有）を列挙（不得修改 R60Common.ts / 不得改变 BaseCamelModel / 不得引入未登记 ID / 不得跳过 trace_check / 不得外抛敏感值）；commit 7 种格式样例；R60Area L-014/L-015 两条 SQL 模板摘要位置指向
  - `AGENTS.md`：列出 trans-cosmos-ai 案件全体 AI Agent 角色（上流 SE/下流 PG/测试设计/AI 推進/机密点检/Review 独立検査）与对应 Claude Code Skill；标明 6 角色全部由 Claude Code 执行、人持评审门（RACI：人=A/I，AI=R/C）；含每个角色「启动 Prompt 模板」一段
- **Acceptance Criteria Addressed**: AC-1, FR-1
- **Test Requirements**:
  - `rule` TR-3.1: `CLAUDE.md` 前 10 行同时包含「落地篇 30 页」「7 条红线」两个关键词，`grep -c` 命中 2
  - `rule` TR-3.2: SKILL.md 中引用 `R60Common.ts` 的函数名列表长度 >= 10，`r60const.py` ACTION_ID 引用 >= 5
  - `rule` TR-3.3: `AGENTS.md` 列出角色数 >= 6，每个角色含启动 Prompt 模板段

## Task 4: レジストリ三 YAML と Git 運用文書群
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1
- **Description**:
  - `docs/00_registry/ids.yml`：R60Area/R60Code/R60Item 三模块 开球周 ID 发号本，前缀 10 类（R/Q/F/I/D/L/E/TC/CR/BUG）三位起步不复用；至少登记：R-101 R60Areaマスタ検索登録修正削除 / F-042 R60Area全画面機能 / I-201~256（56件、名称与 DB 列 56 字段对应，名称列表从实际 R60_AREA_M_TBL 抽出）/ D-043 R60Area詳細設計 / L-014（search 业务）/ L-015（initEdit/edit/delete 排他+参照+重複）/ E-001~E-005（R60W0010/R60W0006/R60W0014/R60W0024/R60E0025）/ TC-001~TC-008 / CR-001（初期 Phase1 申请）/ BUG-001 void（示例作废标记）；每条 id 含 status 和 used_by 字段
  - `docs/00_registry/glossary.yml`：中日英三语用語集，至少收录 30 核心术语（エリアマスタ/Area Master/区域主数据；排他制御/Optimistic Lock/乐观锁；被参照チェック/Referential Check/引用检查；ROWID 分页/ROWID Paging/ROWID 分页；当日鍵（yyyymmdd）/...）
  - `docs/00_registry/traceability.yml`：R-101 → F-042 → I-201..256 → D-043 → L-014/L-015 → E-001..005 → TC-001..008 双向链 map（forward_links + back_links 双字段）
  - `CODEOWNERS`：分 11 块（当初計画は 7 块。実物は `.claude/agents/`・`.claude/settings.json`・`docs/00_plan/` を追加して 11 块になった。`.claude/rules/` = AI推進担当 / `.claude/skills/`・`.claude/agents/` = SE+PG / `.claude/settings.json` = AI推進担当 / `docs/10_requirements/` = 上流 SE / `docs/20_basic_design/`・`docs/30_detail_design/` = 設計 PG / `docs/00_plan/` = 上流 SE / `tools/` = AI 推進 + PG / `tools/kb-platform/repo/` = 全員 / `.github/workflows/` = Git管理者）
  - `CONTRIBUTING.md`：分支模型（req/R-xxx 集成分支 + R-xxx/01-req 到 07-release 七层子分支）·工作流 8 工程 S9-S17 日数概算·7 种 commit 完整样例 3 条·Tag 命名 baseline/R-xxx/basic-v1.0 + 对应验收·baseline 後变更走 CR-xxx 流程
  - `.github/workflows/ai-gate.yml`：占位空 workflow（on: pull_request → runs-on: ubuntu-latest → 3 steps：checkout / setup-python / run: python -m tools.trace_check --strict --gate 6 2>&1 || echo "Phase1 local run only" ）；不配置实际 runner，注释写「用户可按需复制到内网 GitLab/Jenkinsfile」
  - `docs/_samples/01_context/R-101-R60Area.md`：R-101 需求背景 5 条（朝日ビール調達生産/エリアマスタ 56 項目/ cmpCd+jigCd+araCd 三键/排他 ksn_dat+rev_no/検索 OFFSET-FETCH ROWID ページング）
- **Acceptance Criteria Addressed**: AC-1, AC-2, FR-1, FR-6, NFR-1, NFR-3
- **Test Requirements**:
  - `rule` TR-4.1: ids.yml 中前缀计数：R>=1 Q>=0 F>=1 I>=56 D>=1 L>=2 E>=5 TC>=8 CR>=1 BUG>=1，I 前缀条目 == 56，`python -c "yaml.safe_load(open(x))['ids'] | len([i for i in ids if i.startswith('I-')])"` == 56
  - `rule` TR-4.2: traceability.yml 中 R-101 forward_links 递归可达 TC-008，且 TC-008 back_links 能回到 R-101，脚本自检测试 Exit 0
  - `rule` TR-4.3: CONTRIBUTING.md 中 7 种 commit 类型示例存在，`grep -E "^- (req|design|feat|test|fix|rel|chore):"` 命中 >= 3
  - `rule` TR-4.4: CODEOWNERS 块数 >= 7，每块用 /path 语法

## Task 5: 8 大工程 YAML 模板 × 8 份空骨架
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1
- **Description**:
  - `docs/10_requirements/req-template.yaml`：7 字段 front-matter 头 + body 字段（background[3条]/business_rules[5条]/non_goals[3]/stakeholders[3]/acceptance_summary）
  - `docs/20_basic_design/bd-template.yaml`：7 字段 + body（function_overview/screen_list/input_ids/output_ids/db_tables_used/common_functions_used/error_ids_ref）；每项均支持列表
  - `docs/30_detail_design/dd-template.yaml`：7 字段 + body（logic_ids 列表含 description/sql 位置/エラー分岐表 列 error_id, condition, msg_placeholder, next_action / 境界値表）
  - `docs/40_framework/framework-record.yaml`：7 字段 + body（选型 6 顺序：机密→成果物→工具→AI 服务→KPI→迁移脚本 / 栈清单 Vue 版/PrimeVue 版/FastAPI 版/Oracle 版/Auth0 版/S3 版 · 每个版本号 实际从 package.json + requirements.txt 读取）
  - `docs/50_unit_test/tc-template.yaml`：7 字段 + body（viewpoint/design_ids/req_ids/preconditions/input_spec/expected_output/assertion_rules）
  - `docs/60_integration_test/integration-template.yaml`：7 字段 + body（api_sequence/前端调用链/后端 DB 事务边界/commit 点/A/B 比较断言字段清单）
  - `docs/70_release/release-template.md`：7 字段 front-matter + release_note + rollback_procedure + baseline_tag + 健康度记录（引用 doc/03_AI/AB_Reports 目录）
  - `docs/80_operation/operation-runbook.md`：7 字段 + oracle 连接池健康检查 SQL / trace_check 跑法 / 机密スキャン手順 / 緊急配信 SEND_STS='9' 切り戻し手順
- **Acceptance Criteria Addressed**: AC-2, FR-2
- **Test Requirements**:
  - `rule` TR-5.1: 8 份模板文件都存在，7 字段 front-matter 用 yaml 解析无异常，`python -c "yaml.safe_load_all(open(x)).send(None) in ..."` 对 8 文件全通过 Exit 0
  - `rule` TR-5.2: bd-template.yaml 内 input_ids/output_ids/error_ids_ref 三键存在且值为列表
  - `rule` TR-5.3: dd-template.yaml 内 logic_ids / エラー分岐表 / 境界値表 三部分存在

## Task 6: R-101 需求文書 × F-042 基本設計 × D-043 詳細設計 3 份
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 4 (ids.yml), Task 5 (templates)
- **Description**:
  - `docs/_samples/10_requirements/R-101-R60Area.yaml`：用 req-template.yaml 填充，背景 5 条（cmpCd,jigCd,araCd 3 键/56 項目/排他 ksn_dat rev_no/検索 CSV ダウンロード/モード 1/2/3 新規複製修正）；business_rules 5 条（REG_STS 設定=15項目 NotEmpty→REG_STS_ON，否则 OFF/集中購買 cmpCd+jigCd concatWithComma 规则/ロケ未登録 error_flg 1 原材料 2 半製品/排他 ksn_dat 不一致 R60W0006/被参照削除 R60W0024）
  - `docs/_samples/20_basic_design/F-042-R60Area.yaml`：用 bd-template.yaml 填，function_overview=2 画面（一覧検索 + 登録修正複製ダイアログ）/ screen_list=R60Area.vue + R60AreaEdit.vue / input_ids=I-201..I-256（列表形式 56 ID 引用 ids.yml 不重定义）/ output_ids=同 I 一覧（同じ field_count 等于 56）/ db_tables_used=R60_AREA_M_TBL,R60_COMPANY_M_TBL,R60_JIG_M_TBL,R60_UKH_PLC_M_TBL,R60_HIYO_KEIJ_BSY_M_TBL,R60_CODE_MES_M_TBL,R60_PLC_M_TBL 共 7 テーブル / common_functions_used=R60Common 至少 10 条（subCheckSubmit/resetErrors/showErrorAndFocus/byteCheck/subCheckKanaByte/chkHanEngNum3/subCheckAlphabetNumber/subListBtnDisabled/subDownload/showMessageDialog/subInitSubmitFlg/spreadResults 12 条） / error_ids_ref=E-001..E-005 + R60W0033 error_flg 1/2 两个
  - `docs/_samples/30_detail_design/D-043-R60Area.yaml`：用 dd-template.yaml 填，logic_ids 两条 L-014, L-015；L-014 description=検索处理 OFFSET-FETCH ROWID（含 ALLOWED_SORT_FIELDS={CMP_CD,JIG_CD,ARA_CD} 白名单 + 其余走 HYJ_SEQ 排序），sql_location=R60AreaController.py L1499-L1647；L-015 description=initEdit/edit/delete 三件套 排他+重複+被参照+REG_STS 設定，sql_location=R60AreaController.py L1713-L2915；エラー分岐表 8 行（E-001~E-005 + R60W0033×2 + R60W0010 検索 0 件）；境界値表 10 行（cmpCd 最小 4 桁・jigCd split ',' 件数 2 チェック・araCd 先頭 % ワイルドカード不可・REG_STS 15 项 empty チェック・SEND_STS=9 緊急配信・DEL_FLG 切り替え時被参照・ロケ存在チェック count=0・排他 KSN_DAT 不一致・REV_NO int+1 溢れ・KSN_DAT フォーマット YYYY/MM/DD HH24:MI:SS）
- **Acceptance Criteria Addressed**: AC-2, AC-3, FR-2, NFR-1
- **Test Requirements**:
  - `rule` TR-6.1: `py -3 -m tools.trace_check --only-check id-chain --root R-101` Exit 0，I-ID 数统计 = 56
  - `rule` TR-6.2: `grep -rn "受払場所コード" docs/10_requirements docs/20_basic_design docs/30_detail_design` 仅在 docs/30_detail_design 定义处命中 1 行（重复定义禁止，单一源 NFR-1 验证）
  - `rule` TR-6.3: F-042 db_tables_used 列表项数 == 7，common_functions_used 项数 >= 10

## Task 7: L-014/L-015 逻辑文書 × E-ID エラー × TC-001~008 テスト 5 份
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 6
- **Description**:
  - `docs/_samples/30_detail_design/L-014-R60Area-search.yaml`：7 字段 front-matter，body 记述 5 步骤（chk_onl_flg→WHERE 条件组み立て（cmpCd exact / jigCd split[1] / araCd LIKE prefix 且 escape '\' / DEL_FLG filter）→ count(*) ページ計算→select_column dynamic 取得→OFFSET-FETCH+ROWID sort→56 item assignment）；每条步骤对应实际代码行行号范围（L1430..L1647 从实际 Controller 记录）
  - `docs/_samples/30_detail_design/L-015-R60Area-edit.yaml`：7 字段，body 记述 8 步骤（mode 1/2 INSERT 前重複→mode 3 UPDATE 前 排他→被参照 DEL_FLG=1 時参照→ロケーション 2 件存在→set_reg_sts 15 项目判定→INSERT VALUES 42 列绑定 / UPDATE SET 32 列绑定 / 削除 UPDATE DEL_FLG=1→SEND_STS=9 緊急配信→conn.commit()）；每条行号
  - `docs/_samples/30_detail_design/E-001-E005-R60Area.yaml`：7 字段，表形式列（eid/error_id/level/発生箇所/condition/msg_template_placeholder/recovery_action/关联 R-ID/关联 TC-ID），至少 8 行（E-001:R60W0010/E-002:R60W0006/E-003:R60W0014/E-004:R60W0024/E-005:R60E0025/E-006:R60W0033 flg1/E-007:R60W0033 flg2/E-008:R60A0039-0040 確認）
  - `docs/_samples/50_unit_test/TC-001-TC-008-R60Area.yaml`：用 tc-template 展开 8 条 TC，TC-001 通常検索（正常）/TC-002 新規登録（正常）/TC-003 既存修正（正常）/TC-004 0 件検索（境界）/TC-005 KSN_DAT 不一致排他（境界）/TC-006 重複キー登録（異常，E-003）/TC-007 被参照 DEL_FLG=1 削除（異常，E-004）/TC-008 ロケーション未登録 idoDfltPlcCdGzr（異常，E-006）；每条 TC 必带 design_ids=[D-043,L-xxx] + req_ids=[R-101] + preconditions + input_spec 全字段表 + expected_output error_id 列
  - `docs/_samples/60_integration_test/IT-001-R60Area-e2e.yaml`：7 字段，API シーケンス（/R60Area/init → /R60Area/search → /R60Area/initEdit mode=1 → /R60Area/edit mode=1 → /R60Area/initEdit mode=3 → /R60Area/edit mode=3 → /R60Area/delete → /R60Area/download）8 接口順；A/B 比較断言列表 cmp_cd/jig_cd/ara_cd 3 键 + 32 业务字段一致性；A/B Reports 目录指向实际 doc/03_AI/AB_Reports/reports/R60Area/summary.md 路径
- **Acceptance Criteria Addressed**: AC-2, FR-2, NFR-3
- **Test Requirements**:
  - `rule` TR-7.1: trace_check 双向闭环：TC-001..008 design_ids 列出的 L-ID/D-ID 实际存在于 ids.yml 且 L-ID 反向能回到 I-ID
  - `rule` TR-7.2: E-001~E-008 每条含発生箇所 = R60AreaController.py 具体路由名（search/edit/delete/initEdit 之一）
  - `rule` TR-7.3: TC-001..008 分类统计 正常 3 + 境界 2 + 异常 3，`python -c "分类计数"` == (3,2,3)

## Task 8: 开球周评审差分资产三模块目录结构 + R60Area 10 条実例
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 1, Task 6
- **Description**:
  - 为 R60Area / R60Code / R60Item 三模块各建标准三目录：`{module}/review_before/`（评审前设计或代码骨架占位）、`{module}/review_after/`（评审后修正版占位）、`{module}/review_comments.md`（5 模板分类的评论）
  - R60Area/review_comments.md 充实 10 条评论（从 doc/00_管理/【QA票】共通マスタ.xlsx 的公开字段抽 10 个典型指摘），每条包含 5 模板：問題点 / 根本原因 / 修正方針 / 予防策（防止再発规则化）/ 关联 R-ID（固定 R-101）；模拟新人猜中率实验表（review_before vs review_after 对照，列出 10 条中 ≥7 条「新人盲 review 可还原指摘」还原率 >= 70% 记录段落）
  - R60Code/review_comments.md 和 R60Item/review_comments.md 仅填 3 条示例 + SOP 指示段落（如何补全、新人猜中率验收步骤），不强行造 10 条（符合 Open Questions #1 默认口径）
  - `tools/kb-platform/repo/company/patterns/review/sop-review-diff.md`：开球周资产盘点操作手順 10 步（Git clone→识别简/中/难三模块→准备 review_before 历史评审版本→准备 review_after 最终版→人工填 review_comments 5 模板→新人盲猜验证→猜中率 ≥70% 合格→失败重投→归档到 ids.yml→升阶 4 级规则化）
- **Acceptance Criteria Addressed**: AC-5, FR-5
- **Test Requirements**:
  - `rubric` TR-8.1: R60Area review_comments.md 结构完整度；scale 1-5；anchors 1=无分类 2=只有问题/原因 2 项 3=5 模板齐全但无举例 4=5 模板 + 10 条完整且每条有关联 R-ID 5=5 模板+10 条+新人猜中率模拟段落给出统计；threshold >= 4
  - `rule` TR-8.2: R60Code R60Item 各 review_comments.md 条数 >= 3 且含 SOP 段落
  - `rule` TR-8.3: 三模块目录 review_before/review_after/review_comments.md 三件套全部存在

## Task 9: trace_check.py 6 重門番本地 CI 脚本
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 4 (ids.yml), Task 7
- **Description**:
  - 纯标准库 + `pip install pyyaml`（若缺）实现。**実際の構成**: 実体は `tools/trace_check/` パッケージ（`__init__.py` に gate 実装 + `__main__.py`）。`tools/trace_check.py` は後方互換の薄いランチャー（実体へ委譲）。正規の呼び出しは `py -3 -m tools.trace_check` に統一（原文の「双配置」構想は、パッケージ + 委譲ランチャーという形で結果的に成立している）
  - 实现 6 个 gate：gate1 ID 合法性（读 ids.yml → 扫描 docs/**/*.yaml *.md front-matter → 野号或 void 号未标记立即报告）；gate2 追溯双向闭环（按 traceability.yml forward/back 递归 R→F→I→D→L→TC→反向，孤儿 ID 报告）；gate3 front-matter 7 字段齐全（id/type/req_ids/status/sensitivity/owner/version，status 值必须在 {draft,open,baselined,changed,done,void}）；gate4 生成一致（gen_formal --dry-run 字段计数 == I-ID 数 56）；gate5 snake/camel 命名分区合规（YAML/MD 定义层 snake case 合法、TS 接口层 camel case 合法，混写 定义层出现 cmpCd 打回；YAML 模板文件内部 I-ID 定义用 snake 字段，front-matter 7 字段全部 snake）；gate6 机密ゼロヒットスキャン（**通用规则只検出「機密の形」，不内置任何项目固有实值**：復号ファンクション呼出 / AES 当日キー実値 / 内部 IP（RFC1918）/ 資格情報付き接続 URL / 社内メール / 環境変数パスワード等。项目固有識別子（接続ユーザ・テナント・バケット・プロファイル名）は `.gitignore` 済みの `tools/trace_check/secret_patterns.local.json` にのみ置く。命中即 Exit 1。走査対象に `docs/00_plan/**` を含める）
  - CLI 参数：--strict（Exit 非零失败）/ --gate N（只跑到第 N 门）/ --only-check {id-chain|secrets|front-matter} 单项 / --report <path> 输出 JSON 报告（键 gate1~gate6 pass(bool) stats(dict) orphan_ids(list)）
  - Exit 0 条件：所有启用门全 pass；stdout summary 行 `[trace_check] gate1=PASS ... gate6=PASS | total_ids=xxx orphans=0`
- **Acceptance Criteria Addressed**: AC-2, AC-4, AC-6, FR-3, NFR-1, NFR-2, NFR-3, NFR-6
- **Test Requirements**:
  - `rule` TR-9.1: `py -3 -m tools.trace_check --strict --gate 6 --report reports/gate6_report.json` Exit 0，gate6_report.json 中 pass 数=6 fail=0，orphan_ids=[]
  - `rule` TR-9.2: 人为注入一个野号 I-9999 到某 YAML → 运行 trace_check → Exit 非 0 且 stderr 出现 "野号" 关键词 → 回滚注入
  - `rule` TR-9.3: 人为注入字符串 `TBL_1:PWD_1@IP_1` 形式の資格情報付き URL 到某 docs yaml（非 security 文档）→ --only-check secrets Exit 非 0 → 回滚
  - `rule` TR-9.4: 运行不依赖任何外部 HTTP/DB 服务，`python -c "import sys; sys.path.insert(...); import tools.trace_check"` 在无网络 Oracle 内网机可 import 成功（stdout 无 import 错误）

## Task 10: gen_formal 二重化 Excel スクリプト
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 6, Task 9 (gate4 reference)
- **Description**:
  - 目录 `tools/gen_formal/__init__.py` + `gen_excel.py` + `templates/` 空模板目录
  - 实现 dry-run：`py -3 -m tools.gen_formal.gen_excel --dry-run --module R-101` 从 ids.yml I-201..I-256（56 个）→ 输出 JSON 行 `[gen_formal] field_count=56 | output_columns=ara_cmp_list_56_items.csv`，并把列名列表写入 `reports/gen_formal_columns_R101.json`（真实 Excel 生成留 Phase2，dry-run 仅验证列数对应）
  - 列名映射表硬编码但注明「单一源：docs/_samples/30_detail_design/D-043-R60Area.yaml 定义」（引用 NFR-1）
  - `README.txt` 简短说明：Phase1 仅 dry-run；Phase2 接入 openpyxl 或实际客户模板后替换 dry-run 逻辑，不允许手改日文 Excel
- **Acceptance Criteria Addressed**: AC-3, FR-3, NFR-1
- **Test Requirements**:
  - `rule` TR-10.1: dry-run Exit 0，stdout field_count=56
  - `rule` TR-10.2: reports/gen_formal_columns_R101.json 列表长度 == 56，与 I-ID 数一致（trace_check gate4 引用此数据验证）
  - `rule` TR-10.3: 不生成任何实际 .xlsx 文件（Phase2 限制，dry-run 仅 JSON/日志）
    - **2026-10-21 改订**：`docs/**` 零生成的条件不变；`reports/` 配下允许 `tools.gen_formal.book` 生成目视/对客草稿用 .xlsx（规则 00 §12）。

## Task 11: masking 双向脱敏スクリプト
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 2 (01-security-redlines), Task 9
- **Description**:
  - `tools/masking/__init__.py` + `mask_demo.py` + `masking_dict.example.json`（真实 masking_dict.json 加 .gitignore）
  - masking_dict.example.json 结构：`{ "TBL_1": ["sensitive_table_name_TBL_1"], "COL_1": ["cmp_cd", "jig_cd", ...], "PWD_1": ["<接続ユーザ>", "<パスワード>"], "IP_1": ["<内部 IP 1>", "<内部 IP 2>"], "DOM_1": ["<テナントドメイン>"], "BUCKET_1": ["<バケット名>"], "PROFILE_1": ["<AWS プロファイル名>"] }`（**必ず占位のままコミットする**。実値は `.gitignore` 済み `masking_dict.json` にのみ置く — 規則 01 §L3 第 1/2/3/4/6/7 条）
  - mask_demo.py 两个功能：① `--self-test`：内部硬编码**虚构**测试串 `oracle+oracledb://TBL_1:PWD_1@IP_1:PORT_1/SID_1` + 3 行样例 → mask → 验证 TBL_*/COL_*/PWD_*/IP_* 出现且可逆还原回 original → Exit 0（**测试数据必须为架空值，不得引用真实环境**）；② `--mask <in> <out>` 与 `--unmask <in> <out>` 双向转换用 masking_dict.json
  - `--self-test` 打印 summary：mask_hits=xxx unmask_ok=true exit=0
- **Acceptance Criteria Addressed**: AC-4, FR-4, NFR-2
- **Test Requirements**:
  - `rule` TR-11.1: `py -3 -m tools.masking.mask_demo --self-test` Exit 0，stdout 同时出现 `TBL_` 或 `COL_` 或 `PWD_` 占位 + `unmask_ok=true`
  - `rule` TR-11.2: masking_dict.example.json 键 TBL_1/COL_1/PWD_1/IP_1/DOM_1/BUCKET_1/PROFILE_1 七键齐全
  - `rule` TR-11.3: `.gitignore` grep masking_dict.json 命中 1 行（禁止入库）

## Task 12: platform-map.md 7 層アーキ
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 3 (CLAUDE.md), Task 4, Task 5, Task 8, Task 9
- **Description**:
  - `tools/kb-platform/repo/company/standards/platform-map.md`：7 層毎に 3 列（已有/本次新建/Phase 2+ 予定）表格；七層：①利用層（Claude Code IDE 統合＋CLI）②編成層（req/R-xxx 分支 + 8 工程 pipeline + trace_check 門番）③能力層（4 件套 Skill code-from-design-trans-cosmos-ai / trace_check.py / gen_formal / mask_demo）④知識層（`D:\TraeWork_memory\` の 4 文書 / doc/02_INPUT 規約 / doc/03_AI AB_Reports / review_diff_assets 开球周 / glossary.yml 30 用語）⑤データ層（Git 仓库 + ids.yml 发号 + traceability.yml 链 + .claude/rules 7 份）⑥統制層（01-security-redlines 3 级清单 / gitleaks 等价 gate6 / CODEOWNERS 11 块 / CONTRIBUTING 基线 Tag）⑦基盤層（Oracle RDS / Auth0 RS256 / AWS S3 SQS / 内网 IP 段 IP_1）
  - 每层「本次新建」条目不得少于 2 条（对应 AC-7 第①子条件）；每条 3 列标注「来源 PPT 第 x 页」（S25-27 平台篇）
- **Acceptance Criteria Addressed**: AC-7, FR-7
- **Test Requirements**:
  - `rule` TR-12.1: 7 層毎の「本次新建」列计数 >= 2，合计本次新建条目 >= 14
  - `rule` TR-12.2: 7 層名称完全一致（利用/編成/能力/知識/データ/統制/基盤）
  - `rule` TR-12.3: 每层至少 1 条引用「PPT 第 Sxx 页」

## Task 13: ROADMAP_3PHASE.md 3 段階計画
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 12
- **Description**:
  - `ROADMAP_3PHASE.md`（项目根，不进 docs 以便快速查阅）：Phase1（1~2 ヶ月，本次实现的 16 条）/ Phase2（3~6 ヶ月，12 条）/ Phase3（6~12 ヶ月，8 条）
  - Phase1 16 条每条含「负责人位（AI推進/SE/PG/全员/全+AI）」「预计完成日占位 2026-10-31」「验收公式/阈值」（例如 16 条的第 14 条：trace_check gate6 全通 Exit 0 / 16 条 12：新人 Walkthrough ≤ 90 分 10 条全通过 7/10）
  - Phase2 12 条（gen_formal 真实 Excel 对接客户模板/内网 GitLab runner 接入 ai-gate.yml/Phase1 KPI 基线实測更新/R60Code R60Item 全链路 ID 登记 10 review_comments 补全/新人 onboarding 实测视频/AB Reports 1308 用例 健康度 赤黄 自动埋め込み/32 模块 开球周资产盘点全量/gitleaks 真实 CLI 替换 gate6 内置/自动 Skill 4 件套 V2 升级/Oracle ROWID 分页 32 模块 切换自动化/R60Common 10 新函数 Skill 映射/機密文書 自動分類 器），每条引用「PPT 第 Sxx 页 → 对应条目」
  - Phase3 8 条（Harmony 酒税 SDS 全社 同构项目 复制骨架/CICD 本格稼働/A/B 比較自動実行 Jenkins/KPI 6 项 S29 月次レポート自動生成/AI 平台プロダクト化 7 层架构 后端化/AI Skill Store 社内公開/新人 60 分 Walkthrough 达标率 >=90%/対日案件 横展開 10 プロジェクト スケール），每条同样 PPT 引用
  - S29 6 KPI（生産性 工数/品質 指摘件数/品質 不具合密度/納期遵守率/AI 利用率/学習曲線 新人 ramp-up）公式占位 + 実測値 「1ヶ月後更新」注释
- **Acceptance Criteria Addressed**: AC-7, FR-8
- **Test Requirements**:
  - `rule` TR-13.1: Phase1 条数 16 / Phase2 12 / Phase3 8，三个计数精确匹配
  - `rule` TR-13.2: Phase2 12 条与 Phase3 8 条 每条含「PPT 第 Sxx 页」引用
  - `rule` TR-13.3: Phase1 每条 负责人位 + 预计完成日 + 验收公式 三字段齐全

## Task 14: onboarding-checklist.md 新人 2 時間 Walkthrough
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 3, Task 4, Task 5, Task 9, Task 13
- **Description**:
  - `tools/kb-platform/repo/company/patterns/howto/onboarding.md`：10 条 walkthrough 步骤，每条含「作業内容」「実行コマンド」「予定時間（分）」「合格サイン Exit or stdout」
  - 10 条示例：①Git clone + 确认 .claude/ 存在（5 分）②ids.yml 手動 R-102 申请并登记（10 分）③用 req-template.yaml 复制一份 R-102（10 分）④copy F-042→F-043 改 I-ID 引用 3 条（10 分）⑤L-016 一条逻辑 + E-009 一个错误码登记（10 分）⑥TC-009 新用例 用 tc-template 设计（15 分）⑦运行 trace_check --strict 找出 野号并修正（20 分）⑧commit message 符合 05-commit 规则 + git tag baseline/R-102/basic-v0.1（10 分）⑨masking self-test + secrets スキャン（5 分）⑩gen_formal dry-run field_count 确认（5 分）；时间合计约 100 分钟 rubric 4（≤90）或 rubric5（≤60）
  - 末尾加「AI Utilization」记录段与「新人自評価アンケート 5 問」
- **Acceptance Criteria Addressed**: AC-8, NFR-4
- **Test Requirements**:
  - `rubric` TR-14.1: Walkthrough 流畅度；scale 1-5；anchors 1=跳步骤不可跑 3=步骤齐全但每步超过 10 分 4=合计 ≤ 90 分 7/10 通过 5=合计 ≤ 60 分 10/10 通过且 TC-009 自動 trace_check 通；threshold >= 4
  - `rule` TR-14.2: 步骤条数 == 10
  - `rule` TR-14.3: 第 10 条执行命令能跑到 gen_formal dry-run Exit 0

## Task 15: 全 AC 自動検証実行 & レポート生成
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 9, Task 10, Task 11
- **Description**:
  - 顺序执行以下命令，记录退出码并归档输出：
    1. `py -3 -m tools.trace_check --strict --report reports/trace_R101.json` → AC-2 自証（chain_complete=true orphan_ids=[] field_count=56）
    2. `py -3 -m tools.gen_formal.gen_excel --dry-run --module R-101` + gate4 自動比較（通过 trace_check 内部调用字段数）→ AC-3 ①
    3. `grep -rn "受払場所コード" docs/10_requirements docs/20_basic_design docs/30_detail_design | wc -l` → 确认 == 1 → AC-3 ②
    4. `py -3 -m tools.masking.mask_demo --self-test` → AC-4 ①
    5. `py -3 -m tools.trace_check --strict --only-check secrets` → AC-4 ②
    6. `py -3 -m tools.trace_check --strict --gate 6 --report reports/gate6_report.json` → AC-6（gate6_report.json pass=6 fail=0）
  - 生成汇总 `reports/AC-selfcheck.md`：列出 AC-1~AC-8 每条 自検 Result + 指 Evidence 文件路径
- **Acceptance Criteria Addressed**: AC-1~AC-8
- **Test Requirements**:
  - `rule` TR-15.1: reports/trace_R101.json 键 stats.field_count == 56 chain_complete == true
  - `rule` TR-15.2: reports/gate6_report.json gate 汇总 `sum(g.pass for g in gates) == 6`
  - `rule` TR-15.3: reports/AC-selfcheck.md AC-1~AC-8 每条列出 Evidence 且 Result = PASS

## Task 16: 仕上げ 最終ディレクトリ & 生産コード非侵入性確認
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 15
- **Description**:
  - 最終確認：对任务 1 列的 19 个目录 + NFR-5 列出的路径执行「生产代码 0 修改」断言；把 `git status --porcelain --untracked-files=no | grep -E "^( M|MM|A )" src/ api/fastapi_oracle_pjt/app/routers Front-end/src` 输出 == 空；若有非预期改动，全部回滚
  - 把 CLAUDE.md + AGENTS.md + ROADMAP_3PHASE.md + CONTRIBUTING.md + CODEOWNERS + .github/workflows/ai-gate.yml 六个根级新文件列清单到 reports/skeleton-files.txt（作为 AC-1 Evidence）
- **Acceptance Criteria Addressed**: AC-1, NFR-5
- **Test Requirements**:
  - `rule` TR-16.1: 生产代码路径 diff 输出为空
  - `rule` TR-16.2: skeleton-files.txt 列 6 个根文件 全部存在（Test-Path 全部 True）

## Task 17: 独立検査 review.md 作成
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 16
- **Description**:
  - （此任务由 Spec Mode Review 阶段的独立检查员新 fresh context 执行，不在 Plan 阶段写内容，任务占位明确 status=pending 并保留 reviewer fresh context 注释）
  - review.md 结构（按 artifact-templates.md review.md 模板）：至少 6 CP-R rule + 2 CP-U rubric，覆盖所有 8 AC；每条标注 Covers: AC-x + TR 列表；Evidence 初期全部 Pending
- **Acceptance Criteria Addressed**: Review phase CP（所有 AC）
- **Test Requirements**:
  - `rule` TR-17.1: review.md 存在，且列出 CP 数 == **12**（8 rule + 4 rubric。初版 8 = 6 rule + 2 rubric、
    Phase1.5 で CP-R-7 / CP-U-3 / CP-U-4 を追加して 11、2026-10-13 に CP-R-8 を追加して 12。
    **数を増やすときは本行を同じ作業単位で更新する**）
  - `rule` TR-17.2: 每个 CP 含 Covers: 行 指向对应 AC-ID

## Task 18: Phase1 完了 総括 & ユーザ引渡しメモ
- **Status**: `pending`
- **Priority**: low
- **Depends On**: Task 17
- **Description**:
  - 生成 `reports/DELIVERY_MEMO.md`：本次 Phase1 完了 16 条 对应清单 + 未解决 4 Open Questions 现状 + Phase2 启动手順（从 ROADMAP 引用）+ 用户需要 Approve 的 gate 位置说明（spec.md + tasks.md + delivery）
  - 不做进一步修改（Non-Goals 严格遵守），仅归档
- **Acceptance Criteria Addressed**: 全 AC 引渡し証跡
- **Test Requirements**:
  - `rule` TR-18.1: DELIVERY_MEMO.md 列出 Open Questions 4 条 全有记录
  - `rule` TR-18.2: Phase1 16 条清单与 ROADMAP 一致（diff 无差异或仅换行差异）

## Task 19: Phase1.5 取入機制・方法論取入の独立検査項目

- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 17
- **Description**:
  - Phase1.5 で追加した「歴史資産 取入機制」（`tools/ingest/` ＋ `docs/00_registry/ingest-manifest.yml`）と
    「方法論取入」（`.claude/rules/06`・`rules/00 §13`・`rules/03 §7`・`rules/04 §9`・`tools/kb-platform/repo/company/standards/internal/*`）は、
    既存の CP では検査されない。本 Task はその**独立検査項目のみ**を定義する（実装はしない）。
  - 検査は `review.md` の CP-R-7 / CP-U-3 / CP-U-4 が担う。本 Task はその TR の定義を与える。
- **Acceptance Criteria Addressed**: AC-1 / AC-4 / AC-6 / AC-7（間接）
- **Test Requirements**:
  - `rule` TR-19.1: gate6 の走査範囲が**縮小されていない**（`reports/trace_R101.json` の
    `gates[gate6].stats.scanned_files` が前回値以上）。かつ `SECRET_EXEMPT_PATHS` の要素数 == 1。
    かつ `tools/ingest/` に機密パターンの定義が無く、`tools.trace_check.scan_text` を import している
  - `rule` TR-19.2: `py -3 -m tools.ingest --self-test` Exit 0。`reports/ingest/**` の出力に
    **機密の実値が含まれない**（パス・size・sha1 のみ）。`id-apply` が `approved: true` 以外の行を書かない
  - `rule` TR-19.3: `.claude/rules/06-knowledge-flywheel.md`・`tools/kb-platform/repo/company/standards/internal/*.md` の各節の出所が
    `tools/kb-platform/repo/company/standards/ppt-deviation.md` §2（A-14/A-15/A-17/A-18）から辿れる。
    逆に §2 の各行が実在ファイルを指す。**数量の記載は出所 PPT の該当頁で「何を数えた数か」を確認済み**
  - `rule` TR-19.4: `grep -c "^## CP" docs/00_plan/review.md` == 12（TR-17.1 と同一の値であること。
    片方だけ更新すると本骨架が自己矛盾する）

## Task 20: 台帳唯一書込み口・影響面・阻塞機制の独立検査項目

- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 17
- **Description**:
  - 2026-10-13 に追加した 3 ツール（`tools/paths.py` / `tools/registry.py` / `tools/impact.py`）と、
    それに伴う `SKILL.md` §3.1・§4.2・§5・§7・§9 および `references/node-worker-contract.md` §4 の改訂は、
    既存の CP では検査されない。本 Task はその**独立検査項目のみ**を定義する（実装はしない）。
  - 検査は `review.md` の `CP-R-8` が担う。本 Task はその TR の定義を与える。
  - 着眼点は「**規矩はあったが道具が無かった**」の解消である。`ids.yml` を書くコードは 1 行も無く
    （読む側だけが 5 ツールにあった）、阻塞は定義だけで設定する箇所が全文に存在しなかった。
- **Acceptance Criteria Addressed**: AC-1 / AC-6
- **Test Requirements**:
  - `rule` TR-20.1: `py -3 -m tools.registry --self-test` Exit 0、`py -3 -m tools.impact --self-test` Exit 0。
    かつ実在の台帳に対し `py -3 -m tools.registry verify` が Exit 0（errors 0）
  - `rule` TR-20.2: `ids.yml` を書くコードが `tools/registry.py` **のみ**。書込み系副命令は `--apply` なしで
    **1 バイトも書かない**（`next <PREFIX>` 実行後も `ids.yml` の `mtime` が不変）。
    `--apply` 時は一時ファイル → 回読検証 → `docs/00_registry/_backup/` への控え → `os.replace()` の順
  - `rule` TR-20.3: 阻塞が**実際に止める**。祖先を対象とする未回答の Q（`block: true` かつ `answer` 空）が
    あるとき `set-status <ID> --to baselined` が **Exit 1** し、阻塞項を列挙する。
    `py -3 -m tools.registry blockers` が同じ一覧を読み出せる
  - `rule` TR-20.4: `py -3 -m tools.impact R-101` の下流に、`F-042`・`D-043`・`L-014`・`L-015`・
    `I-201`〜`I-256`・`E-001`〜`E-008`・`TC-001`〜`TC-008` が**すべて含まれる**。
    「推奨の作り直し順」の先頭が `R-101` である。かつ `--strict` が Exit 0
    （傳遞で繋がっている参照を「漏記」と誤判定していないこと）。
    実行の前後で `ids.yml` その他を**書いていない**（dependency 無しで空を返す場合も含む）
  - `rule` TR-20.5: **門番は 6 道のまま**。`grep -rn "gate7" tools/` == 0 件。
    `py -3 -m tools.trace_check --strict --report reports/trace_R101.json` Exit 0（`pass 数=6` 不変）。
    かつ `grep -c "^## CP" docs/00_plan/review.md` == 12（TR-17.1 と同一の値であること）
  - `rule` TR-20.6: `alloc` の冪等は**現役の番号に限る**。`deprecate` で `void` にした番号に
    同じ業務鍵で `alloc` し直すと **Exit 1 で拒否**され、その番号は返らず、新番号も振られない
    （`void` エントリの `status` も書き換わらない）。規則 02 §7「作废番号の再利用禁止」の機械化。
    合成ツリー上の自己検査（`registry --self-test` の「alloc: void 済み key の再投入」群）で確認する

## Task 21: 変更・指摘環（旁路環 n09）の手順と追加要素登録

- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 17, Task 20
- **Description**:
  - 2026-10-13 に追加した「变更・指摘環」（`nodes/n09-change.md` ＋ 実行体
    `trans-cosmos-ai-node9-change` ＋ `docs/80_operation/impact-analysis-template.yaml`）は、
    既存の CP では検査されない。本 Task はその**独立検査項目のみ**を定義する（実装はしない）。
  - 検査は `review.md` の `CP-R-8` が担う（**新 CP は起こさない**。CP の本数を変えると
    TR-17.1 / TR-20.5 の `== 12` が同時に落ちる）。本 Task はその TR の定義を与える。
  - 着眼点は「**道具はあったが手順が無かった**」の解消である。A-19 で `registry` / `impact` の
    道具は揃っていたが、QA 指摘を受けた担当者が「では、どこから直すのか」を引く手順が存在しなかった。
- **Acceptance Criteria Addressed**: AC-1 / AC-6
- **Test Requirements**:
  - `rule` TR-21.1: `nodes/n09-change.md` と `.claude/agents/trans-cosmos-ai-node9-change.md` と
    `docs/80_operation/impact-analysis-template.yaml` が実在し、それぞれ front-matter 7 字段
    （`id` / `type` / `req_ids` / `status` / `sensitivity` / `owner` / `version`）または
    agent schema を持つ。`py -3 -m tools.trace_check --strict --gate 3` が Exit 0
  - `rule` TR-21.2: **n09 は工程 9 として直列に置かれていない**。
    `SKILL.md` に §3.0「旁路環 n09」が存在し、§7 鉄則に「直列に繋がない」条がある。
    `SKILL.md` の §3 本表（n01〜n08）には n09 の行が**無く**、n09 行は §3.0 の中にのみある
  - `rule` TR-21.3: **紅線は 7 条のまま**・**門番は 6 道のまま**。
    `head -10 CLAUDE.md | grep -c "7 条红线"` == 1、`grep -rn "gate7" tools/` == 0 件、
    `grep -c "^## CP" docs/00_plan/review.md` == 12（TR-17.1 / TR-20.5 と同一の値）
  - `rule` TR-21.4: `tools/kb-platform/repo/company/standards/ppt-deviation.md` §2 に **A-20** が 1 行あり、
    その行が `n09-change.md` / `trans-cosmos-ai-node9-change` / `impact-analysis-template.yaml`
    の実在パスを指す。かつ **A-16 は依然として空番**である（飛び番の注記が残っていること）
  - `rule` TR-21.5: **鍵名の罠を踏んでいない**。`docs/00_plan/coach/**` と `docs/80_operation/**` に
    `id` / `*_id` / `*_ids` / `ids` を鍵として持つ YAML が無い（環の状態鍵は `case_ref`、
    問いは `q_ref` を用いる）。違反すると gate1 が「ID 宣言」と誤認して野号判定になる
  - `rule` TR-21.6: `py -3 -m tools.impact R-101` が Exit 0 で、その出力に「推奨の作り直し順」が
    含まれる（n09 のステップ 2 が依拠する出力形式が実在すること）。
    かつ `py -3 -m tools.registry verify --strict` が Exit 0（環の追加で台帳を壊していないこと）

## Task 22: 封印・凍結前整合の附属検査と出典等級列の導入

- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 9, Task 17
- **Description**:
  - R60Login 節点1 の事後対比（`reports/drill/R60Login/comparison.md`）が挙げた 3 つの改善提案を、
    規則・ツールへ落とす。**新しい門は増やさない**（`stats.gates_run` は 6 のまま）。
    1. **封印検査 `seal`**：凍結後に下流成果物が実在資産の絶対パス・物理名・実装ファイル名を
       引用していないことを機械検査する（対比時の手作業 grep を置き換える。G2 の再発防止）。
    2. **出典等級（E1〜E4）列**：`02_確認事項一覧.md` の表に列として持たせ、転記で等級が消えるのを防ぐ
       （**節点 2 以降で必須**。節点 1 の承認済み `02` は遡及改訂しない）。
    3. **凍結前整合 `freeze`**：論点の振り分け完了と、R 類件数に対する `revision_history` の
       理由付き項目数を機械照合する。あわせて `virtual-requirement-author` の凍結手順に
       三段整合（表↔注記／自由記述↔必須記述／宙に浮いた参照）を必須化する。
  - 検査は `AUX_CHECKS`（`seal` / `freeze`）として `GATES` の外側に置き、`--strict` の全量実行では
    自動で走らせる。`--only-check seal|freeze` で単独実行できる。
  - 登録は `ppt-deviation-register.md` §2 の **A-26 / A-27**。`review.md` には**触らない**
    （`## CP` を増やさない。CP の本数に依存する機械検査を壊さない）。
- **Acceptance Criteria Addressed**: AC-2 / AC-6
- **Test Requirements**:
  - `rule` TR-22.1: `tools/trace_check/aux_checks.py` が実在し、`seal_check` / `freeze_readiness_check` /
    `discover_freeze_files` / `scan_seal_text` / `parse_disposition_table` を持つ。
    `py -3 -m py_compile tools/trace_check/aux_checks.py tools/trace_check/__init__.py` が Exit 0
  - `rule` TR-22.2: **6 道の門は不変**。`grep -rn "gate7" tools/` が 0 件、
    `py -3 -m tools.trace_check --strict --report reports/trace_aux.json` が Exit 0 で、
    `stats.gates_run == 6` かつ `stats.aux_checks_run == 2`、`set(aux) == {"seal", "freeze"}`、
    `all_pass is True`
  - `rule` TR-22.3: **負向テストと SKIP テスト**。一時 root に
    `reports/drill/T/freeze.yaml`（`frozen_scope: ["D:/__SEAL_TEST__"]`）と
    `tutorial/T/节点1_需求/bad.md`（同パスを含む）を置くと、
    `--strict --only-check seal` が Exit 1 かつ `seal=FAIL`。
    凍結記録の無い root では Exit 0 かつ `seal=SKIP`。**境界一致**：
    `D:/AI_work` は `D:/AI_work_dev` に一致しない
  - `rule` TR-22.4: **R60Login の命中が 0**。`--strict --only-check seal` が
    `seal=PASS seal_hits=0`。かつ `tutorial/R60Login/**`（`_archive*`・`.zh.md` を除く）に
    `R60_[A-Z_]+_TBL|R60Login\.vue|MenuCommon\.vue|AppHeader|D:/AI_work` が 0 件
  - `rule` TR-22.5: **規則と手順に列が入っている**。`.claude/rules/02-requirements.md` §4 に
    「出典等級（E1〜E4）」と「節点 2 以降で必須」の記載があり、§4.1 の回答形態表に
    「出典等級」列がある。`nodes/n02-basic-design.md` の出口条件に `--only-check seal` がある。
    `nodes/n01-requirements.md` に「節点 1 は遡及改訂しない」旨がある
  - `rule` TR-22.6: `tools/kb-platform/repo/company/standards/ppt-deviation.md` §2 に **A-26 / A-27** が各 1 行あり、
    いずれも「**第 7 の門ではない**」と `stats.gates_run` が 6 のままであることに言及している
  - `rule` TR-22.7: **不変量**。`head -10 CLAUDE.md | grep -c "7 条红线"` が 1、
    `grep -c "^## CP" docs/00_plan/review.md` が 12（本 Task は `review.md` を編集しない）
