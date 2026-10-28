"""trace_check - trans-cosmos-ai AI 全流程開発 6 重門番（ローカル CI ゲート）

落地篇 PPT S16「工程間の連携メカニズム」＋成果物 6 原則の自動検査実装。
外部 HTTP / DB / モデルに一切依存しない（NFR-6）。依存は標準ライブラリ + pyyaml のみ。

6 ゲート:
  gate1 ID 合法性      - ids.yml 未登録の野号 / void 号の無断使用を検出
  gate2 追跡双方向閉ループ - R→F→I→D→L→E→TC と逆方向が途切れていないか
                           ＋ TC の design_ids が出典（I-ID / E-ID）を漏らしていないか
  gate3 front-matter    - 7 字段 (id/type/req_ids/status/sensitivity/owner/version) 完全性
  gate4 生成物一致      - gen_formal dry-run の列数 == I-ID 数
  gate5 命名分区        - 定義層 snake_case / 接口層 camelCase の混写検出
  gate6 機密ゼロヒット  - 機密の「形」を検出（規則 01 §L3 の 13 項目に対応）。
                          走査対象に docs/00_plan/**・reports/**・archive/**・tutorial/** を含む
                          （除外は .claude/rules/01-security-redlines.md 本体のみ）

使い方:
  python -m tools.trace_check --strict --gate 6
  python tools/trace_check.py --strict --only-check secrets
  python -m tools.trace_check --strict --report reports/trace_R101.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - 環境依存
    yaml = None

from .aux import freeze_readiness_check, seal_check

# --------------------------------------------------------------------------
# 定数
# --------------------------------------------------------------------------

REGISTRY_PREFIXES = ("R", "Q", "F", "I", "D", "L", "E", "TC", "IT", "CR", "BUG")

# 長い接頭辞を先に置く（CR が C に食われないよう）
# IT は 2026-10-27 に追加した。工程⑦の結合・総合テストは TC とは別の成果物単位であり、
# 台帳に載らないまま承認版へ入っていた（ID_RE に無いので gate1 から見えなかった）。
ID_RE = re.compile(r"\b(TC|IT|CR|BUG|R|Q|F|I|D|L|E)-(\d{3,})\b")

FRONT_MATTER_FIELDS = (
    "id",
    "type",
    "req_ids",
    "status",
    "sensitivity",
    "owner",
    "version",
)
ALLOWED_STATUS = {"draft", "open", "baselined", "changed", "done", "void"}

# gate3 対象外（レジストリ本体 / 工程管理計画文書 / Claude Code サブエージェント定義 / 生成物）
#   docs/00_plan  : spec / tasks / review（工程管理の計画文書。成果物ではない）
#   .claude/agents: Claude Code の subagent schema（name/description が必須で 7 字段ではない）
FM_EXEMPT_DIRS = ("docs/00_registry", "docs/00_plan", ".claude/agents")
FM_EXEMPT_FILES = {"CLAUDE.md", "AGENTS.md", "CONTRIBUTING.md", "CODEOWNERS"}

# gate3 の路径パターン免除（tutorial の「成果物でない媒体」）。
#   tutorial を走査根に加えたとき、7 字段を持たない文書が 9 件出た。その中身を見ると
#   **成果物ではないもの**ばかりだった。ここを機械的に免除しないと、逆に
#   「ビューや顧客入力に `id:` を付けさせる」圧力が生まれ、`id: R-201` の誤用
#   （文書が自分を要求そのものだと名乗る）を増やす。免除の理由を 1 行ずつ書く。
FM_EXEMPT_PATTERNS = (
    (r"^tutorial/[^/]+/README\.md$", "印刷用ビュー（手順書であって成果物ではない）"),
    (r"^tutorial/.*/_archive[^/]*/", "アーカイブ（過去版。現行の判定対象ではない）"),
    (r"^tutorial/[^/]+/[^/]+/00_输入_", "顧客入力（我々の成果物ではない）"),
    (r"^tutorial/[^/]+/[^/]+/02_你在这里审查\.md$", "ナビカード（進行役の表示物）"),
    (r"^tutorial/[^/]+/[^/]+/02_审查结果\.md$", "人の審査記録（判断の記録であり成果物ではない）"),
    (r"^tutorial/[^/]+/[^/]+/03_组内审查意见\.md$", "人の審査記録（同上）"),
    (r"^tutorial/[^/]+/[^/]+/03_客户確認依頼書", "対客 PDF 源（内部 ID を載せない文書）"),
    (r"^tutorial/[^/]+/[^/]+/03_技術者検討課題", "社内検討課題 PDF 源（同上）"),
)
FM_EXEMPT_RES = tuple((re.compile(pat), why) for pat, why in FM_EXEMPT_PATTERNS)


def _fm_exempt_reason(rel: str) -> str | None:
    for rx, why in FM_EXEMPT_RES:
        if rx.search(rel):
            return why
    return None

# gate1 対象外（レジストリ本体。ここに野号が居るのは正常）
ID_EXEMPT_DIRS = ("docs/00_registry",)

# gate1 の接頭辞単位の免除。`(パス前方一致, 免除する接頭辞)`。
#   tutorial/ の Q-*: 演習では Q を台帳に出さない（coach SKILL §3.1 の演练例外）。
#     Q は実案件で `tools.registry blockers` が阻塞を解くための道具であり、演習では
#     `nNN.yml` の `open_questions` が同じ役を果たす。台帳に載せると「答える相手の居ない
#     阻塞」が増えるだけで、演習がデッドロックする。
#   ※ 免除は **Q だけ**である。R/F/I/D/L/E/TC/IT は演習でも台帳に載せる（紅线①）。
ID_PREFIX_EXEMPT = (
    ("tutorial/", "Q"),
)

# gate6 対象外:
#   - .claude/rules/01-security-redlines.md : キーワード定義そのもの（L3 一覧を書く場所）
# それ以外（.claude/ 配下・docs/00_plan 配下・tools/ 配下を含む）はすべて走査する。
#
#   ※ 旧版は docs/00_plan/ を「工程管理の計画文書であり成果物ではない」として除外していたが、
#     その除外区画こそが本番 Oracle 接続情報（ユーザ・パスワード・内部 IP）の漏洩箇所であった。
#     2026-10 に除外を撤廃。計画文書にも機密紅線（規則 01）が等しく適用される。
SECRET_EXEMPT_PATHS = (
    ".claude/rules/01-security-redlines.md",
)

# gate6 汎用ルール（コミット対象）。機密「値そのもの」ではなく「機密の形」を検出する。
#
# 「緊急配信」の L3 指定について:
#   L3 の実体は「どの業務 ID・ステータス遷移が緊急配信を発火させるか」という
#   条件式のほうであり、ステータス定数そのものは業務値にすぎない。
#   運用 Runbook が切り戻し手順でその定数に触れるのは正当なため、
#   本チェッカーは「条件式として書かれた形」だけを検出対象にする（下の 2 パターン）。
GENERIC_SECRET_PATTERNS = [
    ("環境変数パスワード", re.compile(r"(?:DB_PASSWORD|API_SECRET|TOKEN_SALT)\s*=\s*['\"]?[^\s'\"]{3,}")),
    (
        "緊急配信トリガ条件",
        re.compile(r"(?:IF|WHEN|条件|トリガ|契機)[^\n]{0,60}SEND_STS\s*=\s*['\"]9['\"]", re.IGNORECASE),
    ),
    (
        "緊急配信トリガ条件(逆順)",
        re.compile(r"SEND_STS\s*=\s*['\"]9['\"][^\n]{0,60}(?:IF|WHEN|条件|トリガ|契機)", re.IGNORECASE),
    ),
    ("AES 当日キー実値", re.compile(r"AES[-_ ]?256[-_ ]?ECB[^\n]{0,40}\b\d{8}\b")),
    ("復号ファンクション実引数", re.compile(r"R60_DECRYPTION_FNC\s*\([^)]*['\"][^'\"]+['\"]")),
    ("内部 IP (RFC1918)", re.compile(r"\b(?:10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b")),
    ("社内メール", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.co\.jp")),
    ("実在社員コード", re.compile(r"社員コード\s*[=:]\s*\d{4,}")),
    ("本番業務データ実値", re.compile(r"(?:受注番号|品番)\s*[=:]\s*[A-Za-z0-9-]{4,}")),
    ("資格情報付き接続 URL", re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*://[^\s/:@]+:[^\s/:@]+@")),
]

# 「占位」判定（連接 URL の資格情報部分にだけ適用）。
# 占位であれば検出しない。判定は 3 通り:
#   1. 角度括弧で囲まれた説明文   … <接続ユーザ>
#   2. 全大文字＋数字＋アンダースコアのみ … TBL_1 / PWD_1 / PORT_1 / DEMODB1
#   3. demo/sample/test/example 等のダミー語を含む … demo_user / sample_password_0000
# 実値はほぼ確実に小文字を含むため、2 が case-sensitive であることが判定の要。
_PLACEHOLDER_TOKEN_RES = (
    ("full", re.compile(r"^<[^>]*>$")),      # <接続ユーザ>
    ("full", re.compile(r"^[A-Z0-9_]+$")),   # TBL_1（大文字のみ。小文字を含めば実値扱い）
    (
        "part",
        re.compile(r"demo|sample|test|example|dummy|fake|placeholder|changeme|xxxx|\*{2,}", re.IGNORECASE),
    ),
)

_CREDENTIAL_URL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://([^/@:]+):([^/@]*)@")


def _is_placeholder_token(token: str) -> bool:
    """1 個のトークンが「占位」かどうか（full=全体一致 / part=部分一致）。"""
    if not token:
        return False
    for mode, pattern in _PLACEHOLDER_TOKEN_RES:
        hit = pattern.match(token) if mode == "full" else pattern.search(token)
        if hit:
            return True
    return False


def _is_placeholder_credential(matched: str) -> bool:
    """連接 URL の user:pass 部分が占位かどうか。占位なら検出対象から外す。

    両方とも占位のときだけ True。片方でも実値らしければ検出する。
    """
    m = _CREDENTIAL_URL_RE.match(matched)
    if not m:
        return False
    return _is_placeholder_token(m.group(1)) and _is_placeholder_token(m.group(2))

# プロジェクト固有の識別子（接続ユーザ / バケット名 / AWS プロファイル / テナントドメイン等）は
# 値そのものを Git に置かない。実値は .gitignore 済みの local ファイルのみに置く。
LOCAL_PATTERNS_FILE = "tools/trace_check/secret_patterns.local.json"
LOCAL_PATTERNS_EXAMPLE = "tools/trace_check/secret_patterns.example.json"


def load_secret_patterns(root: Path) -> list[tuple[str, re.Pattern]]:
    """汎用ルール + ローカル固有ルール（任意）を返す。

    local ファイルが無い場合でも汎用ルールだけで動作する（テスト可能・可搬）。
    """
    patterns = list(GENERIC_SECRET_PATTERNS)
    local = root / LOCAL_PATTERNS_FILE
    if not local.is_file():
        return patterns
    try:
        data = json.loads(local.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return patterns
    for entry in data.get("patterns", []):
        label = str(entry.get("label", "ローカル固有機密"))
        expr = str(entry.get("regex", ""))
        if not expr or expr.startswith("__"):
            continue  # example のプレースホルダ行はスキップ
        try:
            patterns.append((label, re.compile(expr)))
        except re.error:
            continue
    return patterns


def scan_text(
    text: str,
    patterns: list[tuple[str, re.Pattern]] | None = None,
    rel: str = "",
    root: Path | None = None,
) -> list[dict]:
    """テキスト 1 件を機密パターンで走査し、ヒットのリストを返す**公開ヘルパー**。

    gate6 の本体ロジックであり、`tools/ingest` もこれを import して使う。
    規則を二重実装すると、片方だけ更新されて走査漏れが生じる
    （`docs/00_plan/**` の除外がまさにその形で本番接続情報の漏洩を招いた）。

    Args:
        text:     走査対象のテキスト。
        patterns: 省略時は `root` から `load_secret_patterns()` で解決する。
                  `root` も省略した場合は汎用ルールのみ（ローカル固有ルールは読まない）。
        rel:      ヒットに付けるファイル相対パス（表示用。空でもよい）。
        root:     ローカル固有パターン（`secret_patterns.local.json`）の解決ルート。

    Returns:
        `{"file": rel, "line": 行番号, "kind": ルール名, "match": 先頭 40 文字}`
        のリスト。占位のみの資格情報は除外済み。
    """
    if patterns is None:
        patterns = load_secret_patterns(root) if root is not None else list(GENERIC_SECRET_PATTERNS)
    hits: list[dict] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for label, pat in patterns:
            m = pat.search(line)
            if not m:
                continue
            matched = m.group(0)
            # 占位だけの接続 URL（TBL_1:PWD_1@…）は機密ではないので通す
            if _is_placeholder_credential(matched):
                continue
            hits.append({"file": rel, "line": lineno, "kind": label, "match": matched[:40]})
    return hits


# リポジトリルートの上方探索は tools/paths.py が唯一の実装である
# （かつて trace_check / gen_formal / ingest が同じ関数を 3 つ持っていた）。
from ..paths import find_root  # noqa: E402  （公開名としての再輸出も兼ねる）


# --------------------------------------------------------------------------
# ローダ
# --------------------------------------------------------------------------

class Repo:
    def __init__(self, root: Path):
        self.root = root
        self.ids_path = root / "docs" / "00_registry" / "ids.yml"
        self.trace_path = root / "docs" / "00_registry" / "traceability.yml"
        self.registry = self._load(self.ids_path) or {}
        self.trace = self._load(self.trace_path) or {}
        self.ids = self.registry.get("ids") or {}
        self.forward = self.trace.get("forward_links") or {}
        self.back = self.trace.get("back_links") or {}

    @staticmethod
    def _load(path: Path):
        if yaml is None:
            raise RuntimeError("pyyaml が必要です: pip install pyyaml")
        if not path.is_file():
            return None
        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh)

    # ---- 収集ヘルパ -------------------------------------------------------

    # 走査根。`tutorial` は 2026-10-27 に追加した。
    #   旧版は docs/ と .claude/ だけを見ており、**演習（tutorial/R60Login）の 8 工程産出は
    #   gate6（機密）以外の 5 門から丸ごと外れていた**。その結果、台帳に無い ID・
    #   他人の ID を名乗る文書・7 字段を欠く承認版が「6 門全 PASS」で通っていた。
    #   検査範囲を広げる変更は許可されている（規則 06 §3 は「狭める変更」のみ禁止）。
    SCAN_BASES = ("docs", ".claude", "tutorial")

    def iter_docs(self, *, suffixes=(".yaml", ".yml", ".md")) -> list[Path]:
        out = []
        for base in self.SCAN_BASES:
            d = self.root / base
            if not d.is_dir():
                continue
            for p in sorted(d.rglob("*")):
                if p.is_file() and p.suffix in suffixes:
                    out.append(p)
        return out

    def rel(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    def parse_front_matter(self, path: Path):
        """Markdown/YAML 先頭のフロントマターを dict で返す。無ければ None。"""
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None, ""
        if not text.startswith("---"):
            return None, text
        end = text.find("\n---", 3)
        if end == -1:
            return None, text
        block = text[3:end]
        try:
            return (yaml.safe_load(block) or {}), text[end + 4:]
        except yaml.YAMLError:
            return None, text


# --------------------------------------------------------------------------
# gate1: ID 合法性
# --------------------------------------------------------------------------

def _collect_declared_ids(node, acc: set[str]):
    """front-matter / YAML の中で「ID を宣言しているキー」の値だけを拾う。

    prose（本文）は走査しないので、手順書中の例示 ID（R-102 等）は誤検知しない。
    """
    if isinstance(node, dict):
        for key, value in node.items():
            k = str(key)
            if k == "id" or k.endswith("_id") or k.endswith("_ids") or k == "ids":
                for hit in _extract_ids(value):
                    acc.add(hit)
            else:
                _collect_declared_ids(value, acc)
    elif isinstance(node, list):
        for item in node:
            _collect_declared_ids(item, acc)


def _prefix_exempt(rel: str, one_id: str) -> bool:
    """`ID_PREFIX_EXEMPT`（パス × 接頭辞）に該当するか。"""
    prefix = one_id.split("-")[0]
    return any(rel.startswith(d) and prefix == p for d, p in ID_PREFIX_EXEMPT)


def _extract_ids(value) -> list[str]:
    out: list[str] = []
    if isinstance(value, str):
        out.extend(m.group(0) for m in ID_RE.finditer(value))
    elif isinstance(value, (list, tuple)):
        for v in value:
            out.extend(_extract_ids(v))
    return out


def gate1_id_validity(repo: Repo) -> dict:
    declared: dict[str, list[str]] = {}
    for path in repo.iter_docs():
        rel = repo.rel(path)
        if any(rel.startswith(d) for d in ID_EXEMPT_DIRS):
            continue
        declared_ids: set[str] = set()
        if path.suffix in (".yaml", ".yml"):
            doc = repo._load(path)
            if doc:
                _collect_declared_ids(doc, declared_ids)
        else:
            fm, _ = repo.parse_front_matter(path)
            if fm:
                _collect_declared_ids(fm, declared_ids)
        for one in declared_ids:
            if _prefix_exempt(rel, one):
                continue
            declared.setdefault(one, []).append(rel)

    wild, void_used = [], []
    for one, where in sorted(declared.items()):
        entry = repo.ids.get(one)
        if entry is None:
            wild.append({"id": one, "used_in": where})
        elif str(entry.get("status", "")) == "void":
            void_used.append({"id": one, "used_in": where})

    ok = not wild and not void_used
    return {
        "pass": ok,
        "stats": {
            "declared_ids": len(declared),
            "registered_ids": len(repo.ids),
            "wild_ids": len(wild),
            "void_used": len(void_used),
        },
        "wild_ids": wild,
        "void_used": void_used,
    }


# --------------------------------------------------------------------------
# gate2: 追跡双方向閉ループ
# --------------------------------------------------------------------------

def _reach(graph: dict, start: str, seen=None) -> set[str]:
    seen = seen if seen is not None else set()
    if start in seen:
        return seen
    seen.add(start)
    for nxt in graph.get(start, []) or []:
        _reach(graph, nxt, seen)
    return seen


def _tc_design_id_gaps(repo: Repo) -> list[str]:
    """TC の `design_ids` が、ケース内部で参照した I-/E- ID を漏らしていないか。

    規則 04 §4「入出力項目に対応する I-ID は必ず TC の design_ids に列挙する」と
    紅线⑤「全 TC は design_ids（D/L と E）と req_ids を必ず持つ」の機械化。

    判定は 2 つ:
      (1) `design_ids` に `I-*` が 1 つ以上あること
      (2) `input_spec` / `expected_output` の `item` に現れる I-/E- ID が、
          すべて `design_ids` に宣言されていること（= 出典なきテストケースの禁止）

    対象は front-matter の `id` が `TC-` の**実成果物のみ**。
    `TPL-` テンプレート（プレースホルダ `<I-xxx>`）と IT-* は対象外である。
    """
    gaps: list[str] = []
    for path in repo.iter_docs():
        if path.suffix not in (".yaml", ".yml"):
            continue
        doc = repo._load(path)
        if not isinstance(doc, dict):
            continue
        if not re.fullmatch(r"TC-\d{3,}", str(doc.get("id", ""))):
            continue
        rel = repo.rel(path)
        cases = doc.get("test_cases")
        cases = cases if isinstance(cases, list) else [doc]
        for case in cases:
            if not isinstance(case, dict):
                continue
            case_id = str(case.get("test_id") or doc.get("id"))
            declared = {one for one in (case.get("design_ids") or []) if isinstance(one, str)}
            referenced: set[str] = set()
            for key in ("input_spec", "expected_output"):
                for entry in case.get(key) or []:
                    if isinstance(entry, dict):
                        referenced |= set(_extract_ids(entry.get("item")))
            missing = sorted(one for one in referenced if one not in declared)
            if not any(one.startswith("I-") for one in declared):
                missing.append("I-ID が 1 つも無い")
            if missing:
                gaps.append(f"{case_id} ({rel}): design_ids に {', '.join(missing)}")
    return gaps


def _trace_roots(meta: dict) -> list[str]:
    """追跡鎖の起点。`meta.roots`（複数）を優先し、無ければ `meta.root`（単一）。

    複数起点は 2026-10-26 に追加した。骨組みは長らく `root: R-101` の 1 本しか
    持っておらず、**別モジュールの鎖（R60Login の R-201）を登録すると全件が孤児**に
    なっていた。起点を増やすのは検査範囲を狭める変更ではなく**追加**である
    （`.claude/rules/06-knowledge-flywheel.md` §3）。単一起点の設定は従来どおり動く。
    """
    roots = meta.get("roots")
    if isinstance(roots, str):
        roots = [roots]
    if not roots:
        roots = [meta.get("root", "R-101")]
    return [str(one) for one in roots]


def gate2_traceability(repo: Repo) -> dict:
    fwd, back = repo.forward, repo.back
    meta = repo.trace.get("meta") or {}
    roots = _trace_roots(meta)

    # (a) forward / back の対称性
    asym = []
    for src, targets in fwd.items():
        for tgt in targets or []:
            if src not in (back.get(tgt) or []):
                asym.append(f"{src}->{tgt} (back 欠落)")
    for src, sources in back.items():
        for tgt in sources or []:
            if src not in (fwd.get(tgt) or []):
                asym.append(f"{tgt}->{src} (forward 欠落)")

    # (b) 前方向全域到達（いずれかの起点から辿れるか）
    reached_fwd: set[str] = set()
    for start in roots:
        reached_fwd |= _reach(fwd, start)
    # (c) 逆方向（末端 TC から起点に戻れるか）
    leaves = [k for k in fwd if not fwd.get(k)]
    back_reached = set()
    for leaf in leaves:
        back_reached |= _reach(back, leaf)

    registered = set(repo.ids.keys())
    chain_ids = set(fwd) | {t for ts in fwd.values() for t in (ts or [])}

    # 工程管理系（Q/CR/BUG）は要求→テストの鎖に属さないため孤児判定から除外
    exempt = set(meta.get("chain_exempt_prefixes") or [])
    in_scope = lambda one: one.split("-")[0] not in exempt  # noqa: E731

    unreachable = sorted(one for one in chain_ids - reached_fwd if in_scope(one))
    orphans = sorted(one for one in registered - chain_ids if in_scope(one))
    # 末端（forward を持たないノード）すべてが **いずれかの** 起点まで逆辿りできること
    root_set = set(roots)
    leaves_not_returning = sorted(
        leaf for leaf in leaves if not (_reach(back, leaf) & root_set)
    )
    back_missing = sorted(leaf for leaf in leaves_not_returning if in_scope(leaf))

    ok = not asym and not unreachable and not orphans and not back_missing
    # 追跡閉ループに加え、TC の design_ids 出典（規則 04 §4 / 紅线⑤）も本門で見る。
    #   chain_complete は「鎖そのもの」の結果を保つ（AC-2 の証跡の意味を変えないため）。
    design_gaps = _tc_design_id_gaps(repo)
    return {
        "pass": ok and not design_gaps,
        "stats": {
            "nodes": len(chain_ids),
            "edges": sum(len(v or []) for v in fwd.values()),
            "unreachable": len(unreachable),
            "asymmetric": len(asym),
            "orphans": len(orphans),
            "leaves": len(leaves),
            "leaves_not_returning": len(leaves_not_returning),
            "tc_design_id_gaps": len(design_gaps),
        },
        "unreachable_ids": unreachable,
        "asymmetric": asym,
        "orphan_ids": orphans,
        "back_unreachable": back_missing,
        "design_id_gaps": design_gaps,
        "chain_complete": ok,
    }


# --------------------------------------------------------------------------
# gate3: front-matter 7 字段
# --------------------------------------------------------------------------

def gate3_front_matter(repo: Repo) -> dict:
    problems, checked = [], 0
    for path in repo.iter_docs():
        rel = repo.rel(path)
        if any(rel.startswith(d) for d in FM_EXEMPT_DIRS) or rel in FM_EXEMPT_FILES:
            continue
        if _fm_exempt_reason(rel):
            continue

        if path.suffix in (".yaml", ".yml"):
            if not rel.startswith("docs/"):
                continue
            # YAML は文書先頭の 7 フィールドがそのままトップレベルキーになる
            doc = repo._load(path)
            fm = doc if isinstance(doc, dict) else None
        elif path.suffix == ".md":
            fm, _ = repo.parse_front_matter(path)
        else:
            continue

        checked += 1
        if fm is None:
            problems.append({"file": rel, "issue": "front-matter 未検出", "missing": list(FRONT_MATTER_FIELDS)})
            continue
        missing = [f for f in FRONT_MATTER_FIELDS if f not in fm]
        if missing:
            problems.append({"file": rel, "issue": "7 字段欠落", "missing": missing})
            continue
        status = str(fm.get("status", ""))
        if status not in ALLOWED_STATUS:
            problems.append({"file": rel, "issue": f"status 値不正: {status}", "missing": []})

    return {
        "pass": not problems,
        "stats": {"checked": checked, "problems": len(problems)},
        "problems": problems,
    }


# --------------------------------------------------------------------------
# gate4: 生成物一致（gen_formal dry-run 列数 == I-ID 数）
# --------------------------------------------------------------------------

def _count_ids_by_prefix(repo: Repo, prefix: str) -> int:
    pat = re.compile(rf"^{re.escape(prefix)}-\d+$")
    return sum(1 for k in repo.ids if pat.match(k))


def gate4_generation_consistency(repo: Repo) -> dict:
    expected = _count_ids_by_prefix(repo, "I")
    generated = None
    detail = "gen_formal 未実行"
    try:
        sys.path.insert(0, str(repo.root))
        from tools.gen_formal.gen_excel import field_columns  # type: ignore

        columns = field_columns("R-101")
        generated = len(columns)
        detail = f"gen_formal.columns={generated}"
    except Exception as exc:  # pragma: no cover - 実装差分吸収
        gen_json = repo.root / "reports" / "gen_formal_columns_R101.json"
        if gen_json.is_file():
            try:
                data = json.loads(gen_json.read_text(encoding="utf-8"))
                columns = data.get("columns") or data.get("output_columns") or []
                generated = len(columns)
                detail = f"reports/gen_formal_columns_R101.json={generated}"
            except (OSError, json.JSONDecodeError) as sub:
                detail = f"gen_formal 読込失敗: {sub} / {exc}"
        else:
            detail = f"gen_formal 読込失敗: {exc}"

    ok = generated is not None and generated == expected
    return {
        "pass": ok,
        "stats": {
            "expected_field_count": expected,
            "generated_field_count": generated if generated is not None else -1,
        },
        "detail": detail,
    }


# --------------------------------------------------------------------------
# gate5: 命名分区（定義層 snake_case / 接口層 camelCase）
# --------------------------------------------------------------------------

CAMEL_KEY_RE = re.compile(r"^[a-z][A-Za-z0-9]*[A-Z]")  # 小文字始まりで大文字を含むキー


def gate5_naming_partition(repo: Repo) -> dict:
    violations = []
    for path in repo.iter_docs(suffixes=(".yaml", ".yml", ".md")):
        rel = repo.rel(path)
        if rel.startswith("docs/00_registry/ids.yml"):
            # レジストリは name: cmpCd のように「値」として camel 名を持つ。キーではない。
            continue
        if path.suffix in (".yaml", ".yml"):
            doc = repo._load(path)
            if doc is None:
                continue
            for key in _iter_keys(doc):
                if key in FRONT_MATTER_FIELDS:
                    continue
                if CAMEL_KEY_RE.match(key):
                    violations.append({"file": rel, "key": key})
    return {
        "pass": not violations,
        "stats": {"violations": len(violations)},
        "violations": violations[:50],
    }


def _iter_keys(node):
    if isinstance(node, dict):
        for key, value in node.items():
            yield str(key)
            yield from _iter_keys(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_keys(item)


# --------------------------------------------------------------------------
# gate6: 機密ゼロヒット
# --------------------------------------------------------------------------

def _is_secret_exempt(rel: str) -> bool:
    return any(rel.startswith(p) or rel == p for p in SECRET_EXEMPT_PATHS)


def gate6_secret_scan(repo: Repo) -> dict:
    hits = []
    scanned = 0
    patterns = load_secret_patterns(repo.root)
    # .jsonl は RAG の chunk 正本（docs/90_knowledge/**/chunks/*.jsonl）。
    # 走査範囲を狭める変更は行わない（追加のみ）ため、ここで追加する。
    targets = list(repo.iter_docs(suffixes=(".yaml", ".yml", ".md", ".jsonl")))
    for extra in ("CLAUDE.md", "AGENTS.md", "CONTRIBUTING.md", "CODEOWNERS", "ROADMAP_3PHASE.md"):
        p = repo.root / extra
        if p.is_file():
            targets.append(p)
    tools_dir = repo.root / "tools"
    if tools_dir.is_dir():
        targets += [p for p in sorted(tools_dir.rglob("*.py")) if p.is_file()]
    # reports/ は納品証跡（DELIVERY_MEMO / AC-selfcheck 等）を含むため走査対象に加える。
    # 取入機構（tools/ingest）は reports/ingest/** に YAML/JSON を書き出すため、
    # archive/ ・ tutorial/ と同じく .yaml/.yml まで含める。
    # かつて「成果物でない区画は除外してよい」という判断が本番接続情報の漏洩を招いた。
    # 走査範囲を狭める変更は行わない（追加のみ）。
    reports_dir = repo.root / "reports"
    if reports_dir.is_dir():
        targets += [p for p in sorted(reports_dir.rglob("*")) if p.is_file() and p.suffix in (".md", ".txt", ".json", ".yaml", ".yml")]
    # archive/ は旧版スナップショット（Trae 期の rules/SKILL 等）を凍結保管する区画。
    # 「過去の写し」であることは機密紅線の適用除外を意味しないため走査対象に含める。
    archive_dir = repo.root / "archive"
    if archive_dir.is_dir():
        targets += [p for p in sorted(archive_dir.rglob("*")) if p.is_file() and p.suffix in (".md", ".txt", ".json", ".yaml", ".yml")]
    # tutorial/ は 8 節点の実例教材。顧客向けサンプルを含むため走査対象に加える。
    tutorial_dir = repo.root / "tutorial"
    if tutorial_dir.is_dir():
        targets += [p for p in sorted(tutorial_dir.rglob("*")) if p.is_file() and p.suffix in (".md", ".txt", ".json", ".yaml", ".yml")]

    for path in targets:
        rel = repo.rel(path)
        if _is_secret_exempt(rel):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        scanned += 1
        hits.extend(scan_text(text, patterns=patterns, rel=rel))
    return {
        "pass": not hits,
        "stats": {"scanned_files": scanned, "patterns": len(patterns), "hits": len(hits)},
        "hits": hits[:50],
    }


# --------------------------------------------------------------------------
# ランナー
# --------------------------------------------------------------------------

GATES = {
    1: ("gate1_id_validity", "ID 合法性（野号検出）"),
    2: ("gate2_traceability", "追跡双方向閉ループ"),
    3: ("gate3_front_matter", "front-matter 7 字段"),
    4: ("gate4_generation_consistency", "生成物一致"),
    5: ("gate5_naming_partition", "命名分区"),
    6: ("gate6_secret_scan", "機密ゼロヒット"),
}

ONLY_CHECK_MAP = {
    "id-chain": (1, 2),
    "front-matter": (3,),
    "secrets": (6,),
    "naming": (5,),
    "generation": (4,),
}

# 補助検査。門番ではないため GATES / stats.gates_run には数えない。
AUX_CHECKS = {
    "seal": ("seal_check", "封印検査（補助）"),
    "freeze": ("freeze_readiness_check", "凍結前整合（補助）"),
}


def run(root: Path, *, max_gate: int = 6, only: str | None = None) -> dict:
    repo = Repo(root)
    enabled = set(range(1, max_gate + 1))
    aux_enabled: list[str] = []
    if only:
        if only in ONLY_CHECK_MAP:
            enabled = set(ONLY_CHECK_MAP[only])
        elif only in AUX_CHECKS:
            enabled = set()
            aux_enabled = [only]
        else:
            names = sorted(list(ONLY_CHECK_MAP) + list(AUX_CHECKS))
            raise SystemExit(f"[trace_check] --only-check の値が不正です: {only}（{', '.join(names)}）")
    elif max_gate >= 6:
        # 全量（6 門）运行时だけ補助検査を自動実行する。--gate 1..5 は従来どおり。
        aux_enabled = list(AUX_CHECKS)

    results = {}
    for num in sorted(enabled):
        func_name, label = GATES[num]
        func = globals()[func_name]
        try:
            res = func(repo)
        except Exception as exc:  # pragma: no cover
            res = {"pass": False, "stats": {"error": str(exc)}, "error": repr(exc)}
        res["id"] = f"gate{num}"
        res["label"] = label
        results[f"gate{num}"] = res

    aux_results = {}
    for name in aux_enabled:
        func_name, label = AUX_CHECKS[name]
        func = globals()[func_name]
        try:
            res = func(repo)
        except Exception as exc:  # pragma: no cover
            res = {
                "pass": False,
                "status": "FAIL",
                "stats": {"error": str(exc)},
                "error": repr(exc),
                "problems": [str(exc)],
            }
        res.setdefault("status", "PASS" if res.get("pass") else "FAIL")
        res["id"] = f"aux:{name}"
        res["label"] = label
        aux_results[name] = res

    gate2 = results.get("gate2", {})
    gate4 = results.get("gate4", {})
    aux_ok = all(r["pass"] for r in aux_results.values() if r.get("status") != "SKIP")
    all_pass = all(r["pass"] for r in results.values()) and aux_ok
    return {
        "root": str(root),
        "gates": [results[k] for k in sorted(results)],
        "results": results,
        "aux": aux_results,
        "aux_checks": list(aux_results.values()),
        "all_pass": all_pass,
        "chain_complete": bool(gate2.get("chain_complete", False)),
        "orphan_ids": gate2.get("orphan_ids", []),
        "stats": {
            "field_count": gate4.get("stats", {}).get("expected_field_count", 0),
            "gates_run": len(results),
            "gates_pass": sum(1 for r in results.values() if r["pass"]),
            "aux_checks_run": len(aux_results),
            "aux_checks_pass": sum(1 for r in aux_results.values() if r["pass"]),
            "aux_checks_skipped": sum(1 for r in aux_results.values() if r.get("status") == "SKIP"),
        },
    }


def _reconfigure_stdout() -> None:
    """Windows 既定 cp932 コンソールでも日本語診断を正しく出力する。"""
    for stream in (getattr(sys, "stdout", None), getattr(sys, "stderr", None)):
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):  # pragma: no cover
                pass


def main(argv: list[str] | None = None) -> int:
    _reconfigure_stdout()
    ap = argparse.ArgumentParser(prog="trace_check", description="trans-cosmos-ai AI 全流程 6 重門番")
    ap.add_argument("--strict", action="store_true", help="不合格時に非ゼロ終了")
    ap.add_argument("--gate", type=int, default=6, choices=range(1, 7), help="第 N 門まで実行")
    ap.add_argument(
        "--only-check",
        choices=sorted(list(ONLY_CHECK_MAP) + list(AUX_CHECKS)),
        help="特定検査のみ（seal / freeze は補助検査）",
    )
    ap.add_argument("--report", help="JSON レポート出力先")
    ap.add_argument("--root", help="リポジトリルート（既定: 自動探索）")
    ap.add_argument("--id-chain", nargs="?", const="R-101", help="閉ループ起点 ID（既定 R-101）")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve() if args.root else find_root()
    report = run(root, max_gate=args.gate, only=args.only_check)

    # サマリ行（6 門 + 補助検査。補助は SKIP も表示する）
    parts = []
    for g in report["gates"]:
        parts.append(f"{g['id']}={'PASS' if g['pass'] else 'FAIL'}")
    for name, res in report.get("aux", {}).items():
        parts.append(f"{name}={res.get('status', 'PASS' if res['pass'] else 'FAIL')}")
    seal_hits = report.get("aux", {}).get("seal", {}).get("stats", {}).get("hit_lines", 0)
    summary = (
        f"[trace_check] {' '.join(parts)} | "
        f"total_ids={len(Repo(root).ids)} orphans={len(report['orphan_ids'])} "
        f"field_count={report['stats']['field_count']} seal_hits={seal_hits}"
    )
    print(summary)

    for g in report["gates"]:
        if g["pass"]:
            continue
        print(f"  !! {g['id']} {g['label']} 不合格", file=sys.stderr)
        for key in ("problems", "hits", "wild_ids", "asymmetric", "violations", "design_id_gaps"):
            for item in (g.get(key) or [])[:10]:
                if key == "wild_ids":
                    print(f"     - 野号: {item.get('id')} (used in {', '.join(item.get('used_in', []))})", file=sys.stderr)
                else:
                    print(f"     - {item}", file=sys.stderr)

    for res in report.get("aux_checks", []):
        if res["pass"]:
            continue
        print(f"  !! {res.get('id')} {res.get('label')} 不合格", file=sys.stderr)
        for item in (res.get("hits") or [])[:10]:
            # 実在識別子の値は出さない。場所と種別だけを示す。
            print(
                f"     - {item.get('file')}:{item.get('line')} "
                f"[{item.get('module')}/{item.get('kind')}] {item.get('label')}",
                file=sys.stderr,
            )
        for item in (res.get("problems") or [])[:10]:
            print(f"     - {item}", file=sys.stderr)

    if args.report:
        out = (root / args.report) if not Path(args.report).is_absolute() else Path(args.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[trace_check] report -> {repo_rel(root, out)}")

    if report["all_pass"]:
        return 0
    return 1 if args.strict else 0


def repo_rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
