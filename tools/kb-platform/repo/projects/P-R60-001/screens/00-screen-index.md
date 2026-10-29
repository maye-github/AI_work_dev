---
id: KNOW-LEGACY-R60-SCREENINDEX
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-screens-00-screen-index
scope: project
project_id: P-R60-001
title: 画面索引 — 56 画面の地図
doc_type: design-basic
conf_level: 30
updated_at: '2026-10-28'
---

# 画面索引 — 56 画面の地図

> **出所**：`doc/02_INPUT/80.機能一覧/…プログラム一覧（画面）_v1.0.xlsx` の `画面一覧` シート
> ＋ **実物との突き合わせ**（[07](07-traceability.md)）。
> **★台帳は実装から乖離している。** **本書は「台帳の一覧」と「実測の補正」を並べて示す。**

---

## 1. まず「1 画面」の数え方（【実測】）

| 数え方 | 値 | 出所 |
|---|---|---|
| **view ファイル** | **49** | `ls Front-end/src/views/*.vue \| wc -l` |
| component ファイル | 113 | `ls Front-end/src/components/*.vue \| wc -l` |
| service ファイル | 56 | `ls Front-end/src/service/*.ts \| wc -l` |
| router ファイル（＝controller） | 57（55 ＋ `default` ＋ `__init__`） | `ls app/routers/*.py \| wc -l` |
| `画面一覧` の行数（**No. 1〜129**） | 129 ＋ 章見出し 9 ＋ 集計 1 | 台帳 |

> ✗ **「56 画面」という数え方は、どこにも正確には存在しない。**
> `CLAUDE.md` 周辺で言う「56 画面」は **service ファイル数（56）** と一致する。
> **われわれは「1 画面 = 1 画面 ID = view ＋ component ＋ service」と定義**して扱う（[02](02-architecture.md) §5.1）。
> **⚠ 数え方を宣言せずに「56 画面」と言うと、台帳（129）・view（49）・service（56）のどれか分からなくなる。**

---

## 2. 業務領域は 9 つ（【実測】`画面一覧` の章見出し）

| # | 領域（逐語） | 台帳の行範囲 | No. |
|---|---|---|---|
| 1 | **会社・事業場・製造列等関連** | `r4`–`r27` | 1–23 |
| 2 | **アイテム関連** | `r28`–`r43` | 24–38 |
| 3 | **購入品目関連・半製品関連** | `r44`–`r60` | 39–54 |
| 4 | **購入品目－仕入先関連** | `r61`–`r72` | 55–65 |
| 5 | **生産モデル関連** | `r73`–`r100` | 66–92 |
| 6 | **資材切り替え** | `r101`–`r102` | 93 |
| 7 | **その他** | `r103`–`r123` | 94–113 |
| 8 | **入力支援系** | `r124`–`r139` | 114–126 |
| 9 | **共通系** | `r140`–`r143` | 127–129 |

> **★領域名は `画面一覧` の逐語である。** **DR 図（論理）の 8 分類シートとも概ね対応**する
> （[05](05-database.md) §1：会社・事業場・受払場所等関連／アイテム関連／購入品目関連・半製品関連／
> 生産モデル関連／購入品目－仕入先関連／受払区分関連／資材切替イベントマスタ関連／その他）。

---

## 3. ★シミュレーション派生（`(sim1)`〜`(sim6)`）— 数え方の最大の落とし穴

**【実測】** 台帳の No. 129 件のうち、**多数が同じ 画面 ID の `(simN)` 違い**である。

```
[1]  R60Ssk          部署マスタメンテナンス              R60Ssk.vue / R60SskEdit.vue / R60SskService.ts
[2]  R60User         ユーザマスタメンテナンス            …
[5]  R60SezRet       製造列マスタメンテナンス(sim4)       ← ★view/component/service の記載なし
[6]  R60SezRet       製造列マスタメンテナンス(sim5)
[7]  R60SezRet       製造列マスタメンテナンス(sim6)
```

- **`(simN)` の行は、view/component/service の列が空**である（【実測】）。
  → **ファイルを増やすのではなく、同じ画面を「別モード」で動かす**ものだと読める。
- **根拠となる実装（【実測】）**：`app/utils/r60sim_util.py`（設計書 318 行＝最重量の util）／
  `app/models/r60_sim_info_model.py`／`r60util.chk_sim_request`／**API の共通パラメータ `sim_kbn` / `sim_tbl_id`**
  （[09](09-ai-workflow.md) §3 のテンプレート注記に逐語で出てくる）。
- **さらに**：`20.DB定義書/テーブル一覧` に **`Sim` 列**がある（【差異】[D-17](08-deviations.md)）。

> ★★ **シミュレーションは本システムの第一級の機能である。** **`(simN)` を「別画面」と数えると
> 画面数が水増しされ、`sim` を無視すると API の共通パラメータを取り落とす。**

---

## 4. 画面 ID の全一覧（領域別・台帳の逐語から）

**凡例**：`ID ／ 画面名 ／ view ／ 補足`。**★印は実測で名前がずれたもの**。

### 4.1 会社・事業場・製造列等関連

| No. | 画面 ID | 画面名（逐語） | view |
|---|---|---|---|
| 1 | `R60Ssk` | 部署マスタメンテナンス | `R60Ssk.vue` |
| 2 | `R60User` | ユーザマスタメンテナンス | `R60User.vue` |
| 3 | `R60Jig` | 事業場マスタメンテナンス | `R60Jig.vue` |
| 4 | `R60SezRet` | 製造列マスタメンテナンス（**sim4/5/6 あり**） | `R60SezRet.vue` |
| 8 | `R60Plc` | ロケーションマスタメンテナンス | `R60Plc.vue` |
| 9 | `R60PlcUkiKnr` | ロケーション受入管理マスタメンテナンス | `R60PlcUkiKnr.vue` |
| 10 | `R60YokMes` | 容器明細マスタメンテナンス | `R60YokMes.vue` |
| **11** | **`R60Area`** | **エリアマスタメンテナンス** | `R60Area.vue` ← **★骨架の R-101/F-042 の貫通例** |
| 12 | `R60SikKgo` | 仕込記号マスタメンテナンス | `R60SikKgo.vue` |
| 13 | `R60SikKgo` | 仕込配合マスタメンテナンス | **component のみ**（`R60SikHaigEdit.vue`） |
| 14 | `R60SikKgoHan` | 仕込記号半製品マスタメンテナンス | `R60SikKgoHan.vue` |
| 15 | `R60SikKgoPro` | 仕込記号工程関連マスタメンテナンス | `R60SikKgoPro.vue` |
| 16 | `R60DC` | 出荷場所マスタメンテナンス（**sim4/5/6**） | `R60DC.vue` |
| 20 | `R60SntSsi` | その他装製マスタメンテナンス（**sim4/5/6**） | `R60SntSsi.vue` |

### 4.2 アイテム関連

| No. | 画面 ID | 画面名 | view | 補足 |
|---|---|---|---|---|
| 24 | `R60Item` | アイテムマスタメンテナンス | `R60Item.vue` | **sim1〜sim6（最多）** |
| 31 | `R60ItemMulti` | アイテムマスタメンテナンス（複数行、アップロード） | `R60ItemMulti.vue` | sim4/5/6 |
| 35 | `R60PackGift` | パック・ギフト品単品紐付けマスタメンテ | `R60PackGift.vue` | sim4/5/6 |

### 4.3 購入品目関連・半製品関連

| No. | 画面 ID | 画面名 | view |
|---|---|---|---|
| 39 | `R60KonHmk` | 購入品目マスタメンテナンス（sim4/5/6） | `R60KonHmk.vue` |
| 43 | `R60KonHmkMulti` | 購入品目マスタメンテナンス（複数行・アップロード） | `R60KonHmkMulti.vue` |
| 44 | `R60Ikt` | 一括マスタメンテナンス（全て（製品を除く）） | `R60Ikt.vue` |
| 48 | `R60KonHmkCopy` | 購入品目関連マスタ一括コピー | `R60KonHmkCopy.vue` ← **AI 手順書の例示の題材**（[09](09-ai-workflow.md) §5） |
| 49 | `R60SirSziCha` | サプライヤ資材変換マスタメンテナンス | `R60SirSziCha.vue` |
| 50 | `R60Hsh` | 半製品マスタメンテナンス（sim4/5/6） | `R60Hsh.vue` |
| 54 | `R60HshChaChk2` | 半製品変換チェック２マスタメンテナンス | `R60HshChaChk2.vue` |

### 4.4 購入品目－仕入先関連

| No. | 画面 ID | 画面名 | view |
|---|---|---|---|
| 55 | `R60Sir` | 仕入先マスタメンテナンス | `R60Sir.vue` |
| 56 | `R60Maker` | メーカーマスタメンテ | `R60Maker.vue` |
| 57 | `R60SirKytn` | 仕入先拠点マスタメンテナンス | `R60SirKytn.vue` |
| 58 | `R60KonHmkSir` | 購入品目別仕入先マスタメンテナンス | `R60KonHmkSir.vue` |
| 59 | `R60KonHmkSirMes` | 購入品目別仕入先マスタメンテナンス（明細） | **component のみ** |
| 60 | `R60GzrSirTk` | 原材料仕入単価マスタメンテナンス（sim4/5/6） | `R60GzrSirTk.vue` |
| 64 | `R61GzrSirTk` | 原材料支給単価マスタメンテナンス | **★台帳に行はあるが view/component/service の記載が全く無い** |
| 65 | `R60GzrSkyTkSelf` | 原材料支給単価マスタメンテナンス（支給先ごと） | `R60GzrSkyTkSelf.vue` |

### 4.5 生産モデル関連

| No. | 画面 ID | 画面名 | view |
|---|---|---|---|
| 66 | `R60SezKnoItem` | 製造可能品種マスタメンテナンス（**sim1〜6**） | `R60SezKnoItem.vue` ← **AI 手順書の例示コード**（[09](09-ai-workflow.md) §2 Step7） |
| 73 | `R60SezKnoItemMulti` | 製造可能品種マスタメンテナンス（複数行・アップロード） | `R60SezKnoItemMulti.vue` |
| 77 | `R60KojoSesModel` | 工場生産モデルマスタメンテナンス（sim4/5/6） | `R60KojoSesModel.vue` |
| 81 | `R60SesModel` | **アイテム／半製品／原材料**生産モデルマスタメンテナンス | `R60SesModel.vue` |

> **★No.81〜92 は同じ `R60SesModel` で「アイテム／半製品／原材料」の 3 種を兼ねる。**
> **1 画面 ID が複数の業務対象を持つ**例（`画面構成部` で分岐する。【未確認】実装の分岐方法）。

### 4.6 資材切り替え／その他

| No. | 画面 ID | 画面名 | view |
|---|---|---|---|
| 93 | `R60SziKirEvtReg` | 資材切替 | `R60SziKirEvtReg.vue` |
| 94 | `R60CSVDownload` | 全件ダウンロード | `R60CSVDownload.vue` |
| 95 | `R60Code` | コード値マスタメンテナンス（sim4/5/6） | `R60Code.vue` |
| 99 | `R60CodeMes` | コード値明細マスタメンテナンス（sim4/5/6） | `R60CodeMes.vue` |
| 103 | `R60Hany` | 汎用マスタメンテナンス | `R60Hany.vue` |
| 104 | `R60HanyMes` | 汎用明細マスタメンテナンス | `R60HanyMes.vue` |
| 105 | `R60KkuChi` | 規格値マスタメンテナンス | `R60KkuChi.vue`（＋`*001/002/003`） |
| 106 | `R60KkuChiCopy` | 規格値マスタ一括コピー | `R60KkuChiCopy.vue` |
| 107 | `R60Calender` | カレンダーマスタメンテナンス（**sim1〜6**） | `R60Calender.vue` |

### 4.7 入力支援系（**大半は `components/` 側**）

| No. | 画面 ID | 画面名 | 実物 |
|---|---|---|---|
| 114 | `R60ItemSup` | アイテム入力支援 | `components/R60ItemSup.vue` |
| 115 | `R60KonHmkSup` | 購入品目入力支援 | `components/` |
| 116 | `R60HshSup` | 半製品入力支援 | `components/` |
| 117 | `R60SirSup` | 仕入先入力支援 | `components/` |
| 118 | `R60PlcSup` | ロケーション入力支援 | `components/` |
| 119 | `R60SikKgoSup` | 仕込記号入力支援 | `components/` |
| 120 | `SubDeploy` | 容器明細入力支援 | **★実物は `components/R60SubDeploy.vue`**（名前が違う） |
| 121 | `R60ChotSkSup` | 調達先入力支援画面 | `components/R60ChotSkSup.vue` |
| 122 | `R60KjoSesModelSup` | 事業場／製造列複数選択 | **★台帳に「使用している画面なし」と明記** |
| 123 | `R60ListTypeSup` | 一覧型入力支援（原価数単コード／仕入先拠点コード／組織ユニット） | `components/R60ListTypeSup.vue` |
| 126 | `R60ListTypeSupItem` | 一覧系入力支援画面（アイテム）複数選択可 | `components/R60ListTypeSupItem.vue` |
| — | `R60SesModelItemSup` | 生産モデルアイテム支援 | **★`設計書なし、参照なし`**（逐語） |
| — | `R60SesModelKonHmkSup` | 生産モデル購入品目支援 | **★`設計書なし、参照なし`**（逐語） |

> **★支援画面は「画面」ではなく「部品」である**（[02](02-architecture.md) §5.1）。
> **重做の候補から外すのが安全**（他画面から呼ばれるため、単独で作り直せない）。

### 4.8 共通系

| No. | 画面 ID | 画面名 | view | 補足 |
|---|---|---|---|---|
| **127** | **`R60Login`** | **共通マスタログイン** | `R60Login.vue` | **★われわれの対象**（[R60Login.md](R60Login.md)） |
| 128 | `R60Menu` | 共通マスタメンテナンスメニュー | **★実物は `views/MenuCommon.vue`** | **台帳のファイル名が違う** |
| 129 | `r60ServerJobRef` | サーバ処理照会 | **★実物は `views/R60ServerJobRef.vue`** | **台帳が小文字始まり** |

---

## 5. ★台帳に無い画面（【実測】− 重要な補正）

**台帳の 画面 ID 集合（71）と実物の view 集合（49）を突き合わせると、6 件の view が台帳に無い**：

| view | 内容 |
|---|---|
| `MenuCommon.vue` | **共通系メニュー**（台帳は `R60Menu.vue` と書く。**名前が違う**） |
| `R60ServerJobRef.vue` | サーバ処理照会（台帳は小文字始まり `r60ServerJobRef`） |
| **`R60OnlineError.vue`** | **オンラインエラー画面**（route `/OnlineError`） |
| **`R60SessionError.vue`** | **セッションエラー画面**（route `/SessionError`） |
| **`R60SystemError.vue`** | **システムエラー画面**（route `/SystemError`） |
| **`R60Sup.vue`** | 支援画面の共通枠（route `/R60Sup`） |

> ★★ **3 つのエラー画面は台帳に載っていない。**
> **これらは `app/common/` の例外 3 系統（`R60OnlineError` / `R60SessionError` / `R60SystemError`）と
> 1 対 1 で対応する**（[06](06-api.md) §2.5・[04](04-common-parts.md) §3）。
> **＝ 台帳は「業務画面」だけを数え、共通のエラー表示を落としている。**
> **われわれの I-ID / 画面設計には、これらをどこで扱うかを決めておく必要がある。**

---

## 6. 重做候補の選び方（【実測】から導く）

| 判定 | 条件 | 例 |
|---|---|---|
| ✅ **最良** | **設計書 8 シート ＋ view/service/controller ＋ 単体テスト仕様 ＋ A/B レポートが揃う** | **`R60Login`**、`R60Area`、`R60Ssk`、`R60User` |
| ✅ 可 | 設計書 ＋ view/service/controller がある | 上記 4.1〜4.6 の大半 |
| ⚠ 難 | **`(simN)` 派生しか台帳に無い** | 単独では仕様が立たない |
| ❌ 不可 | **`設計書なし、参照なし`** | `R60SesModelItemSup` / `R60SesModelKonHmkSup` |
| ❌ 不可 | **台帳にファイル記載が無い** | `R61GzrSirTk`（No.64） |
| ❌ 不適 | **支援画面（他画面から呼ばれる部品）** | `*Sup` 系 13 件 |

> **★R60Login が最良なのは偶然ではない**：**設計書（8 シート）・実装（view/service/controller）・
> 単体テスト仕様（9 シート）・A/B レポート（`03_AI/AB_Reports/reports/R60Login/`）の 4 点が揃う**
> （[07](07-traceability.md) §5）。**他の画面と比べても最も資料が厚い。**

---

## 7. 画面カードの書式（1 枚 1 ファイル）

`screens/<画面ID>.md` を作るときの固定構成（書式の実物は [R60Login.md](R60Login.md)）：

```
1. 識別情報      画面ID / 画面名 / ルート / view / component / service / controller / 設計書 / 単測仕様 / A/B
2. 仕様要点      画面概要 / 前提条件 / 排他条件 / 利用対象者 / 関連画面
3. 画面項目内容  項目名 / 物理名 / 種別 / 型・桁 / 必須 / 編集仕様        ← 設計書 `画面項目内容` シート
4. イベント一覧  ボタン / イベント名 / 呼ぶ API / 備考                  ← 設計書 `イベント一覧` シート ＋ [06](06-api.md) §2.3 の語彙
5. 業務処理説明  手順                                                   ← 設計書 `業務処理説明` シート（★現行 Java 仕様。D-19）
6. API 契約      端点 / Request / Response                              ← 実物の controller を読む（★台帳を信じない。D-14）
7. DB            表 / 列 / 操作                                        ← [05](05-database.md)
8. 共通部品      呼ぶ R60Common.ts / r60util の関数                      ← [04](04-common-parts.md)
9. 人間実装対応  主要ファイルの file:line
10. テスト       単体テスト仕様の要点
11. 出典         各事実の出所
12. 未確定・差異  【未確認】と【差異】D-xx
```

> **★12 番を空にしない。** **「分からないこと」を書かないカードは、後で嘘になる**（規則 06 §4）。

---

## 8. 出典

- 【実測】`py -3 -m tools.legacy "doc/02_INPUT/80.機能一覧/…プログラム一覧（画面）_v1.0.xlsx" --sheet 画面一覧`
- 【実測】`ls Front-end/src/{views,components,service}` ／ `ls api/fastapi_oracle_pjt/app/routers`
- 【実測】`grep -nE 'Menu|R60Sup|Error' Front-end/src/router/index.ts`（route 定義）
- 【実測】台帳の画面 ID 集合と view 集合の `comm` 突き合わせ（2026-10-14 実行）
- 骨架側：`.claude/rules/02-requirements.md` §2、`CLAUDE.md` §4
