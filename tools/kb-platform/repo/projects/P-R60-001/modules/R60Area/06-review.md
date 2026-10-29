---
id: KNOW-LEGACY-R60-MODULE-R60AREA-REVIEW-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60area-06-review
scope: project
project_id: P-R60-001
title: R60Area — レビュー指摘と処置
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-29'
generated_by: tools/kb_migrate.py
---

# R60Area — レビュー指摘と処置

> 正本は同ディレクトリの `06-review.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60AREA-REVIEW |
| type | knowledge |
| status | open |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |

## ab_comparison

| 項目 | 値 |
|---|---|
| status | incomplete |
| evidence | search 500 / modify・download SKIP / detail・new 8 列差異 |
| implication | R60Area の実装を正解として学習しない。設計書と単体テスト仕様を正とする。 |

## req_ids

## deviations

| id | title | type | evidence | impact | cause | action | machine_detectable | layer | detection_hint |
|---|---|---|---|---|---|---|---|---|---|
| D-AR-01 | 画面項目数が骨架の I-ID 枠（56）と一致しない | design_vs_skeleton | ["画面項目内容(検索)：項目番号 76 件（r15-r90）", "画面項目内容(マスタ項目)：項目番号 45 件（r16-r60）", "骨架の I-201..I-256 は 56 件"] | I-ID を 1 対 1 で対応付けると、検索 76 件・マスタ 45 件のどちらとも合わない。 | 56 は骨架構築時に置いた仮の枠であり、設計書から導いた数ではない。 | R60Area では I-ID を画面項目数として使わない。I-ID を起こす場合は、検索・マスタを別採番し、設計書の項目番号を source_locator に持つ。 | False | knowledge |  |
| D-AR-02 | R60A0039 / R60A0040（計上事業場 ≠ 事業場の確認）が実装されていない | implementation_gap | ["設計書 10_画面項目間・DB整合チェック r18-r29 に 12 件の確認メッセージがある。", "R60AreaController.py:2453-2489（登録）と 2155-2191（削除）は全てコメントアウトされている。"] | 計上事業場が事業場と異なるデータでも、確認なしで登録・削除される。設計どおりの挙動ではない。 | 実装時に確認ダイアログの往復（エラーコードで返してフロントが再送する方式）が未実装のままコメントアウトされた。 | 実装課題として記録する。設計書を正とするなら、フロントの確認ダイアログとバックエンドの再送パラメータ（confirm_flg 等）を設計へ追加する必要がある。勝手に設計を変えない。 | True | knowledge | 設計書のメッセージ ID と実装の message_id 一覧を突合すると、R60A0039/R60A0040 が実装に現れない。 |
| D-AR-03 | BaseCamelModel の extra が 'ignore'（骨架規則は 'forbid'） | design_vs_skeleton | ["R60AreaController.py:33-39 は extra=\"ignore\"。", "03-design-coding.md §2 は extra='forbid' を固定としている。"] | 定義外の入力が 422 にならず、静かに無視される。項目追加・改定の検知が弱い。 | 既存案件の実装が骨架規則より先に存在し、骨架規則が実装に合わせられていない。 | R60Area の知識カードには実装値を記録する。骨架規則を変えるかは人（ユーザー）の裁定事項であり、本カードでは変更しない。 | True | rules | grep 'extra=' で 'ignore' と 'forbid' の混在を検出できる。 |
| D-AR-04 | イベント番号が 12_イベント一覧 と 14_業務処理説明 で重複・不一致 | design_internal_inconsistency | ["12_イベント一覧：No10=ダウンロード、No16=債務計上事業場ドロップダウン変更、No25=削除、No26=登録。", "14_業務処理説明：r191『イベントNo16：ダウンロードボタンクリック』、r274 以降にも No16 が見える。"] | イベント番号で設計を引くと別の処理に当たる。RAG の検索キーにイベント番号を使うと誤検索する。 | シート間で番号を振り直したが、片方が追随していない。 | RAG の chunk ではイベント番号を主キーにせず、『イベント名称＋処理内容』を主キーにする。 | True | knowledge | 同一文書内で『イベントNo16』が複数の名称に付いている。 |
| D-AR-05 | ダウンロード処理が検索条件を SQL 文字列へ直接連結している | security | ["R60AreaController.py:1666-1682 で cmp_cd / jig_cd を f-string / + で WHERE 句に埋め込む。", "同じファイルの search（1429 以降）は bind パラメータを使っている。"] | 入力値によっては SQL インジェクションが成立し得る。search と download で安全度が異なる。 | 共通 CSV ユーティリティが WHERE 文字列を受け取る設計であり、呼び出し側が値を連結している。 | 実装課題として記録する。download も bind パラメータ化するか、CSV ユーティリティ側でパラメータを受ける形へ変更する。設計（D/L）を変える場合は CR を起票する。 | True | gate | WHERE 句の組み立てで f-string / + を使っている箇所を grep する。 |
| D-AR-06 | ページングと既定ソートが骨架規則の例と異なる | design_vs_skeleton | ["実装は OFFSET {offset} ROWS FETCH FIRST {page_limit} ROWS ONLY。", "既定ソートは DEL_FLG, CMP_CD, TO_NUMBER(R60_Get_Jig_Information_FNC(CMP_CD, JIG_CD, '3')), JIG_CD, ROWID。", "00-project-global.md §5 は ROWID 方式を原則とし、03-design-coding.md §5 の例は JIG_HYJ_SEQ を既定としている。"] | 骨架の例をそのまま当てはめると設計書のソート順（事業場表示順）と食い違う。 | 骨架の例が R60Area 以外の画面を想定した簡略例であり、案件の設計書と一致していない。 | R60Area では設計書のソート順（DEL_FLG → CMP_CD → 事業場表示順 → JIG_CD）を正とする。骨架の例は案件ごとに読み替える。 | False | rules |  |
| D-AR-07 | R60AreaService.ts のヘッダコメントが別画面の名称 | implementation_quality | ["Front-end/src/service/R60AreaService.ts:4 は『製造可能品種マスタサービス R60AreaService』。"] | 検索・保守時に画面の取り違えを招く。機能には影響しない。 | 別サービスのコピー元コメントを残したまま。 | 実装課題として記録する（コメント修正のみ。動作変更なし）。 | True | knowledge | サービス名とコメント内の画面名が一致しない。 |
| D-AR-08 | A/B レポートで search が 500、detail/new に 8 列差異 | implementation_quality | ["doc/03_AI/AB_Reports/reports/R60Area/summary.md", "search / check：500 サーバー崩壊（同一入力で旧 SQL は正常）", "detail / new：8 列差異", "modify / download：SKIP"] | R60Area の新実装は、検索の主要経路が動作しない状態を含む。A/B 比較は完了していない。 | レポートの診断では『データ問題ではなくコード bug』とされている。 | R60Area を『完成した参照実装』として扱わない。学習材料としては設計書を正とし、実装は差分の観測対象とする。 | False | knowledge |  |
| D-AR-09 | REG_STS 判定 16 項目と緊急配信必須 13 項目の混同リスク | design_clarity | ["14_業務処理説明 r488-r505：REG_STS は 16 項目。", "14_業務処理説明 r391-r408：緊急配信必須は 13 項目（キー 3 項目を除く）。", "設計書の項目名に『受払計上場所』『債務計上場所』『債権計上場所』とあるが、実カラムは UKH_KEIJ_BSY_CD / SAIM_KEIJ_BSY_CD / SAIKN_KEIJ_BSY_CD（部署コード）。"] | 項目名だけを読むと存在しないカラムを探す。13 と 16 を取り違えると REG_STS が誤判定される。 | 設計書内で『場所』と『部署』の用語が混在している。 | カラムとの対応は 01-fields.yaml を正とする。REG_STS は 16、R60W0012 は 13 と明記する。 | False | knowledge |  |
| D-AR-10 | 複合キーを 'CMP_CD,JIG_CD' 形式の文字列で受け渡している | implementation_convention | ["request の jig_cd は 'CMP_CD,JIG_CD' 形式で、実装は split(',')[1] を使う。", "部署コードは split(',')[0] を使う箇所がある（R60AreaController.py:2369-2375）。"] | 値の中にカンマが含まれると壊れる。設計書には記述がない暗黙の規約である。 | フロントのドロップダウン値が複合キーを 1 文字列で持つ実装都合。 | API 契約カード（02-api.yaml）に明記する。RAG では『jig_cd は複合キー文字列』として検索できるようにする。 | False | knowledge |  |
| D-AR-11 | 設計書の検索処理説明に『ロケーションマスタを検索する』とある | design_typo | ["14_業務処理説明 r92：『取得した抽出項目と設定した検索条件でロケーションマスタを検索する。』", "同シートの前後はエリアマスタ（R60_AREA_M_TBL）の検索である。"] | 設計書だけを読むと対象テーブルを取り違える。 | 別画面（ロケーション）からの流用。 | R60Area の検索対象は R60_AREA_M_TBL とする。設計書の逐語は source_locator 付きで残す。 | False | knowledge |  |
| D-AR-12 | マスタ項目画面がフロントでは 3 コンポーネントに分かれている | implementation_structure | ["R60AreaCreate.vue（736 行） / R60AreaEdit.vue（1,874 行） / R60AreaCopy.vue（772 行）", "設計書は『マスタ項目画面』を 1 画面として記述する。"] | 設計書の画面単位と実装のファイル単位が一致しない。修正時に 3 箇所を見る必要がある。 | 新規・修正・複製でコンポーネントを分けた実装判断。 | RAG では『マスタ項目画面 = Create/Edit/Copy の 3 コンポーネント』として 1 チャンクにまとめる。 | False | knowledge |  |

## review_questions

| question | status | owner | note |
|---|---|---|---|
| R60A0039/R60A0040 を実装しないことは、顧客の合意済み仕様か。 | open | 人（ユーザー） | 設計書は実装を要求している。合意済みなら設計書側に注記が必要。 |
| download の SQL 連結は許容されているか。 | open | 人（ユーザー） | セキュリティ方針に関わるため、骨架側で勝手に直さない。 |
| extra='ignore' を骨架規則（forbid）へ合わせるのか、規則を実装へ合わせるのか。 | open | 人（ユーザー） | migration 案件固有の実装と greenfield の既定規則が衝突している。 |
