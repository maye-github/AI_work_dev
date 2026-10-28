"""trans-cosmos-ai AI 全流程骨架 - ID 台帳（ids.yml）唯一の書込み口。

なぜ必要か
----------
`docs/00_registry/ids.yml` は NFR-1 の単一ソースでありながら、これまで
**書き込むコードが 1 行も存在しなかった**（読む側だけが 5 ツールにあった）。
79 件の ID はすべて手書きで、書き間違えれば野号、重複させれば誰も気づかない。

本ツールはその唯一の書き込み口である。**人間が叩く CLI であり、エージェントの能力ではない。**
`node-worker-contract.md` §5 禁① と coach スキル §0 の「エージェントは ids.yml を書かない」は
**1 文字も変えていない**。

安全設計（本リポジトリは git 管理下になく、書き壊しは不可逆）
------------------------------------------------------------
- 書き込みを伴う副命令は **既定でドライラン**（差分を出すだけ）。実際に書くには `--apply` が要る。
- `--apply` 時は「一時ファイル → 回読検証 → バックアップ → `os.replace()`」の順。
  途中で失敗すれば 1 バイトも書かずに中止する。
- 書き込む先は `docs/00_registry/ids.yml` **ただ 1 つ**。
  git の無い環境では、書き込むファイルが増えるほど故障点が増えるためである。
- 差分は**該当箇所だけ**を書き換える（ファイル全体を再ダンプしない）。
  再ダンプはコメントを全部消し、以後どのコマンドでも全体差分が出る（規則 03 §7.1 の冪等性違反）。

副命令
------
    alloc / next / set-status / deprecate / mark-stale / clear-stale / answer
    verify / blockers / --self-test
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

from .paths import find_root, reconfigure_stdout, registry_path, rel, traceability_path
from .trace_check import REGISTRY_PREFIXES

STATUS_DOMAIN = ("draft", "open", "baselined", "changed", "done", "void")

# 状態機（規則 02 §6）。逆行は禁止で、修正は changed を経由する。
TRANSITIONS = {
    "draft": {"open", "void"},
    "open": {"baselined", "void"},
    "baselined": {"changed", "done", "void"},
    "changed": {"baselined", "void"},
    "done": {"void"},
    "void": set(),
}

# 親リンク（子 → 親）。error_id は「エラー番号の値」であって親リンクではないので含めない。
PARENT_KEYS = ("r_id", "f_id", "d_id", "l_id", "e_id")

ENTRY_KEY_RE = re.compile(r"^(TC|IT|CR|BUG|R|Q|F|I|D|L|E)-\d{3,}$")

# 親リンクの鍵（子の接頭辞 → 親を格納する鍵名）。
#   adopt で `--parent` を受けたとき、どちらの鍵に入れるかをこれで決める。
PARENT_KEY_BY_PREFIX = {"R": "r_id", "F": "f_id", "D": "d_id", "L": "l_id", "E": "e_id"}
TOP_KEY_RE = re.compile(r"^  ([A-Za-z]+-\d{3,}):\s*$")
FIELD_RE_TMPL = r"^    {name}:"
BACKUP_DIRNAME = "_backup"

# エントリを描画する際のキー順（既存エントリの並びに合わせる）
FIELD_ORDER = (
    "status", "name", "jp", "description", "kind", "text", "block",
    "answer", "answer_by", "answered_at", "origin_key", "related_ids",
    "stale", "void_reason", "category", "error_id", "flg", "file", "lines",
    "r_id", "f_id", "d_id", "l_id", "e_id", "used_by",
)


# --------------------------------------------------------------------------
# 基本ユーティリティ
# --------------------------------------------------------------------------

def _need_yaml() -> None:
    if yaml is None:  # pragma: no cover
        raise SystemExit("[registry] pyyaml が必要です: pip install pyyaml")


def _read_text(path: Path) -> str:
    """改行コードを変換せずに読む（書戻しでファイル全体の差分を出さないため）。"""
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _eol(line: str) -> str:
    """行の改行コードを保つ（`splitlines(keepends=True)` の行を組み直すため）。"""
    if line.endswith("\r\n"):
        return "\r\n"
    return "\n"


def _scalar(value) -> str:
    """YAML スカラー（list/bool/None 含む）を 1 行のテキストへ描画する。"""
    text = yaml.safe_dump(
        value, allow_unicode=True, default_flow_style=True, width=10 ** 6
    ).strip()
    if text.endswith("\n..."):
        text = text[:-4].rstrip()
    return text


def load_registry(root: Path) -> dict:
    """ids.yml を読み込む（トップレベル map）。"""
    _need_yaml()
    path = registry_path(root)
    if not path.is_file():
        raise SystemExit(f"[registry] ids.yml が見つかりません: {path}")
    with open(path, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    if not isinstance(doc, dict):
        raise SystemExit("[registry] ids.yml のトップレベルが map ではありません")
    if not isinstance(doc.get("ids"), dict):
        raise SystemExit("[registry] ids.yml に `ids:` map がありません")
    return doc


def duplicate_top_keys(text: str) -> list[str]:
    """生テキストから ID キーの重複を検出する。

    `yaml.safe_load` は重複キーを**黙って上書き**するため、パース後には検出できない。
    ここだけは生テキストを見る必要がある。
    """
    seen: dict[str, int] = {}
    dups: list[str] = []
    for line in text.splitlines():
        m = TOP_KEY_RE.match(line)
        if not m:
            continue
        key = m.group(1)
        seen[key] = seen.get(key, 0) + 1
        if seen[key] == 2:
            dups.append(key)
    return sorted(set(dups))


def count_by_prefix(ids: dict) -> dict[str, int]:
    out: dict[str, int] = {}
    for key in ids:
        m = ENTRY_KEY_RE.match(str(key))
        if m:
            out[m.group(1)] = out.get(m.group(1), 0) + 1
    return out


def next_number(ids: dict, prefix: str) -> int:
    """当該接頭辞で**これまでに使われた最大番号 + 1**。void も数える（番号再利用禁止）。"""
    pat = re.compile(rf"^{re.escape(prefix)}-(\d+)$")
    top = 0
    for key in ids:
        m = pat.match(str(key))
        if m:
            top = max(top, int(m.group(1)))
    return top + 1


def format_id(prefix: str, number: int) -> str:
    return f"{prefix}-{number:03d}"


def find_by_origin(ids: dict, origin_key: str) -> str | None:
    for key, entry in ids.items():
        if isinstance(entry, dict) and str(entry.get("origin_key") or "") == origin_key:
            return str(key)
    return None


def unresolved_blockers(doc: dict) -> list[dict]:
    """未解除の阻塞項（`block: true` かつ `answer` が空）を列挙する。"""
    out: list[dict] = []
    for key, entry in (doc.get("ids") or {}).items():
        if not isinstance(entry, dict):
            continue
        if entry.get("block") is True and not entry.get("answer"):
            out.append({
                "id": str(key),
                "kind": str(entry.get("kind") or "question"),
                "text": str(entry.get("text") or entry.get("name") or ""),
                "relates_to": [str(v) for v in (entry.get("related_ids") or [])],
            })
    return out


def parent_map(doc: dict, trace: dict) -> dict[str, set[str]]:
    """子 → 親 の集合（ids.yml の親リンク ＋ traceability の back_links）。"""
    parents: dict[str, set[str]] = {}
    for key, entry in (doc.get("ids") or {}).items():
        if not isinstance(entry, dict):
            continue
        here = {str(entry[k]) for k in PARENT_KEYS if entry.get(k)}
        if here:
            parents.setdefault(str(key), set()).update(here)
    for key, vals in (trace.get("back_links") or {}).items():
        parents.setdefault(str(key), set()).update(str(v) for v in (vals or []))
    return parents


def ancestors_of(target: str, parents: dict[str, set[str]]) -> set[str]:
    """target の祖先（target 自身は含めない）。"""
    seen: set[str] = set()
    stack = list(parents.get(target, ()))
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        stack.extend(parents.get(cur, ()))
    seen.discard(target)
    return seen


def blockers_for(doc: dict, trace: dict, target: str) -> list[dict]:
    """target を阻塞している未解除項。祖先まで遡って判定する（伝遞閉包）。"""
    parents = parent_map(doc, trace)
    scope = ancestors_of(target, parents) | {target}
    return [b for b in unresolved_blockers(doc) if set(b["relates_to"]) & scope]


# --------------------------------------------------------------------------
# 生テキスト編集（コメントと既存の並びを壊さない）
# --------------------------------------------------------------------------

def _find_entry_span(lines: list[str], key: str) -> tuple[int, int] | None:
    """`  KEY:` の行 index と、その項目の最終行の次 index（排他）を返す。"""
    start = None
    for i, line in enumerate(lines):
        if TOP_KEY_RE.match(line) and line.strip() == f"{key}:":
            start = i
            break
    if start is None:
        return None
    j = start + 1
    while j < len(lines) and (lines[j].strip() == "" or _indent_of(lines[j]) >= 4):
        j += 1
    end = j
    while end - 1 > start and lines[end - 1].strip() == "":
        end -= 1
    return start, end


def _render_entry(key: str, entry: dict) -> list[str]:
    """1 エントリを ids.yml の書式で描画する。"""
    known = [k for k in FIELD_ORDER if k in entry]
    known += [k for k in entry if k not in FIELD_ORDER]
    out = [f"  {key}:"]
    for name in known:
        value = entry[name]
        if isinstance(value, dict):
            out.append(f"    {name}:")
            for sub, sub_value in value.items():
                out.append(f"      {sub}: {_scalar(sub_value)}")
        else:
            out.append(f"    {name}: {_scalar(value)}")
    return out


def _insert_entry(lines: list[str], key: str, entry_lines: list[str]) -> list[str]:
    """同接頭辞の最後のエントリ直後へ差し込む。当該接頭辞が未登場なら新節として足す。"""
    eol = _eol(lines[0]) if lines else "\n"
    entry_lines = [ln if ln.endswith("\n") else ln + eol for ln in entry_lines]
    prefix = key.split("-")[0]
    anchor_key = None
    for line in lines:
        m = TOP_KEY_RE.match(line)
        if m and m.group(1).split("-")[0] == prefix:
            anchor_key = m.group(1)
    if anchor_key:
        span = _find_entry_span(lines, anchor_key)
        if span:
            lines[span[1]:span[1]] = entry_lines
            return lines
    for i, line in enumerate(lines):
        if line.startswith("prefix_count_summary:"):
            at = i
            while at > 0 and lines[at - 1].strip() == "":
                at -= 1
            lines[at:at] = [eol, f"  # ---------- {prefix}: 追加 ----------{eol}"] + entry_lines
            return lines
    lines.extend([eol] + entry_lines)
    return lines


def _set_field(lines: list[str], key: str, name: str, value) -> list[str]:
    """エントリ内のフィールドを置換／追加する。"""
    span = _find_entry_span(lines, key)
    if span is None:
        raise KeyError(key)
    start, end = span
    eol = _eol(lines[start])
    pat = re.compile(rf"^    {re.escape(name)}:")
    for i in range(start + 1, end):
        if pat.match(lines[i]):
            if isinstance(value, dict):
                block = [f"    {name}:{eol}"]
                block += [f"      {s}: {_scalar(v)}{eol}" for s, v in value.items()]
                lines[i:i + 1] = block
            else:
                lines[i] = f"    {name}: {_scalar(value)}{eol}"
            return lines
    at = end
    for i in range(start + 1, end):
        if re.match(r"^    status:", lines[i]):
            at = i + 1
            break
    if isinstance(value, dict):
        block = [f"    {name}:{eol}"]
        block += [f"      {s}: {_scalar(v)}{eol}" for s, v in value.items()]
        lines[at:at] = block
    else:
        lines.insert(at, f"    {name}: {_scalar(value)}{eol}")
    return lines


def _remove_field(lines: list[str], key: str, name: str) -> list[str]:
    """エントリ内のフィールド（ネストを含む）を削除する。無ければ何もしない。"""
    span = _find_entry_span(lines, key)
    if span is None:
        return lines
    start, end = span
    pat = re.compile(rf"^    {re.escape(name)}:")
    for i in range(start + 1, end):
        if pat.match(lines[i]):
            j = i + 1
            while j < len(lines) and lines[j].strip() != "" and _indent_of(lines[j]) >= 6:
                j += 1
            del lines[i:j]
            return lines
    return lines


def _sync_counts(lines: list[str], ids: dict) -> list[str]:
    counts = count_by_prefix(ids)
    start = None
    for i, line in enumerate(lines):
        if line.startswith("prefix_count_summary:"):
            start = i
            break
    eol = _eol(lines[0]) if lines else "\n"
    if start is None:
        lines.extend([eol, f"prefix_count_summary:{eol}"])
        lines.extend(f"  {p}: {counts.get(p, 0)}{eol}" for p in REGISTRY_PREFIXES)
        return lines
    i = start + 1
    seen = set()
    while i < len(lines) and (lines[i].strip() == "" or _indent_of(lines[i]) >= 2):
        if lines[i].strip():
            name = lines[i].strip().split(":")[0]
            seen.add(name)
            lines[i] = f"  {name}: {counts.get(name, 0)}{eol}"
        i += 1
    # 接頭辞を新設したとき（例: 2026-10-27 の IT）、既存の行を書き換えるだけでは
    # 当該接頭辞の行が増えず、verify が「prefix_count_summary.IT = None だが実際は 12」
    # で落ちる。**足りない接頭辞の行を補う**（REGISTRY_PREFIXES の順に挿入する）。
    missing = [p for p in REGISTRY_PREFIXES if p not in seen]
    if missing:
        anchor = i
        # 既存行の並び（REGISTRY_PREFIXES 順）を壊さないよう、直前の接頭辞の次に入れる
        ordered = [p for p in REGISTRY_PREFIXES if p in seen or p in missing]
        insert_at = anchor
        for p in missing:
            pos = ordered.index(p)
            if pos > 0:
                prev = ordered[pos - 1]
                for j in range(start + 1, anchor):
                    if lines[j].strip().startswith(f"{prev}:"):
                        insert_at = j + 1
                        break
            lines.insert(insert_at, f"  {p}: {counts.get(p, 0)}{eol}")
            seen.add(p)
            anchor += 1
            insert_at += 1
    return lines


# --------------------------------------------------------------------------
# 差分・バックアップ・原子的書込み
# --------------------------------------------------------------------------

def _backup(root: Path) -> Path:
    src = registry_path(root)
    out_dir = src.parent / BACKUP_DIRNAME
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dst = out_dir / f"ids.yml.{stamp}.bak"
    dst.write_bytes(src.read_bytes())
    return dst


def _write_atomic(root: Path, text: str) -> None:
    target = registry_path(root)
    fd, tmp_name = tempfile.mkstemp(prefix="ids.yml.tmp-", suffix=".part", dir=str(target.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, target)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def _commit(root: Path, before: str, after: str, *, apply: bool, label: str, expect=None) -> int:
    """差分を出し、`--apply` なら原子的に書き込む。"""
    if before == after:
        print(f"[registry] {label}: 変更なし（既にその状態です）")
        return 0

    diff = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile="docs/00_registry/ids.yml (現状)",
        tofile="docs/00_registry/ids.yml (変更後)",
        n=3,
    )
    text = "".join(diff)
    print(text, end="" if text.endswith("\n") else "\n")

    parsed = yaml.safe_load(after)
    if not isinstance(parsed, dict) or not isinstance(parsed.get("ids"), dict):
        print("[registry] 回読検証に失敗（YAML map として解析できません）。書込みを中止しました。",
              file=sys.stderr)
        return 1
    if expect is not None:
        reason = expect(parsed)
        if reason:
            print(f"[registry] 回読検証に失敗（{reason}）。書込みを中止しました。", file=sys.stderr)
            return 1

    if not apply:
        print(f"[registry] {label}: ドライラン（書き込んでいません）。"
              f"反映するには同じコマンドに --apply を付けてください。")
        return 0

    backup = _backup(root)
    _write_atomic(root, after)
    print(f"[registry] {label}: 書込みました。バックアップ: {rel(root, backup)}")
    return 0


def _edit(root: Path, mutate, *, apply: bool, label: str, expect=None) -> int:
    """生テキストを読み、mutate(lines, doc) で書き換え、_commit へ渡す。"""
    path = registry_path(root)
    before = _read_text(path)
    doc = load_registry(root)
    lines = before.splitlines(keepends=True)
    mutate(lines, doc)
    after = "".join(lines)
    return _commit(root, before, after, apply=apply, label=label, expect=expect)


# --------------------------------------------------------------------------
# 副命令
# --------------------------------------------------------------------------

def cmd_alloc(root: Path, args) -> int:
    prefix = args.prefix.upper()
    if prefix not in REGISTRY_PREFIXES:
        print(f"[registry] 未知の接頭辞: {args.prefix}（許容: {', '.join(REGISTRY_PREFIXES)}）",
              file=sys.stderr)
        return 2

    doc = load_registry(root)
    ids = doc.get("ids") or {}

    existing = find_by_origin(ids, args.key)
    if existing is not None:
        entry = ids.get(existing) or {}
        # void 済みの番号は「既に割当て済み」ではない。返すと作废番号を現役として使わせることになる
        # （規則 02 §7 の番号再利用禁止に反する）。自動で別番号を振ることもできない
        # （同一 origin_key のエントリが 2 つになり verify の一意性検査が落ちる）ため、人に返す。
        if str(entry.get("status") or "") == "void":
            print(
                f"[registry] origin_key='{args.key}' は {existing} に割当て済みですが、"
                f"その番号は void（作废）です。作废番号は再利用できません（規則 02 §7）。\n"
                f"          業務鍵を変えて新規発号するか、人が {existing} を復活させるかを"
                f"判断してください（本ツールは決めません）。",
                file=sys.stderr,
            )
            return 1
        conflicts = []
        if args.name and str(entry.get("name") or "") != args.name:
            conflicts.append("name")
        if args.relates_to and [str(v) for v in (entry.get("related_ids") or [])] != list(args.relates_to):
            conflicts.append("related_ids")
        if conflicts:
            print(f"[registry] origin_key='{args.key}' は既に {existing} に割当て済みですが、"
                  f"{', '.join(conflicts)} が異なります。"
                  f"（同じ業務鍵に別の意味を与えないこと。手で確認してください）", file=sys.stderr)
            return 1
        print(f"[registry] {existing}  <-- origin_key='{args.key}' は既にこの番号に割当て済み"
              f"（冪等・変更なし）")
        return 0

    new_id = format_id(prefix, next_number(ids, prefix))
    entry: dict = {"status": "open"}
    if args.name:
        entry["name"] = args.name
    if args.note:
        entry["description"] = args.note
    if args.kind:
        entry["kind"] = args.kind
    if args.block:
        entry["block"] = True
        entry["answer"] = None
        entry["answer_by"] = None
        entry["answered_at"] = None
    entry["origin_key"] = args.key
    if args.relates_to:
        entry["related_ids"] = list(args.relates_to)
    if args.used_by:
        entry["used_by"] = args.used_by

    def mutate(lines: list[str], _doc: dict) -> None:
        _insert_entry(lines, new_id, _render_entry(new_id, entry))
        new_ids = dict(ids)
        new_ids[new_id] = entry
        _sync_counts(lines, new_ids)

    def expect(parsed: dict):
        if new_id not in (parsed.get("ids") or {}):
            return f"{new_id} が書き込まれていない"
        return None

    print(f"[registry] 発号: {new_id}  (origin_key='{args.key}')")
    return _edit(root, mutate, apply=args.apply, label=f"alloc {new_id}", expect=expect)


def cmd_adopt(root: Path, args) -> int:
    """**既に成果物の中で使われている番号**を台帳へ追認登録する（新規発号ではない）。

    なぜ alloc では足りないか:
      `alloc` は必ず `next_number`（最大番号 + 1）を振る。ところが演習 R60Login の
      TC-201..TC-220 と IT-201..IT-211 は**既に承認版の中で使われており**、節点7・8 から
      何十回も参照されている。alloc で振り直すと TC-009.. になり、参照が総崩れになる。
      番号は AI が考えたものではなく**成果物に既に存在する**ので、台帳がそれを
      **追認**するのが正しい（紅线①の実質は「台帳が唯一の真源」であって「必ず連番」ではない）。
    安全側の設計:
      - 既に別の origin_key で登録済みの番号は**奪わない**（Exit 1）。
      - 同じ origin_key が別の番号に付いていれば**増やさない**（Exit 1）。
      - 冪等（同じ引数で二度流しても書き込みは 1 回）。
    """
    one = str(args.id).upper()
    if not ENTRY_KEY_RE.match(one):
        print(f"[registry] 追認できない形の ID です: {args.id}", file=sys.stderr)
        return 2
    prefix = one.split("-")[0]
    if prefix not in REGISTRY_PREFIXES:
        print(f"[registry] 未知の接頭辞: {prefix}（許容: {', '.join(REGISTRY_PREFIXES)}）",
              file=sys.stderr)
        return 2

    doc = load_registry(root)
    ids = doc.get("ids") or {}

    if one in ids:
        entry = ids.get(one) or {}
        same = str(entry.get("origin_key") or "") == str(args.key)
        if same:
            print(f"[registry] {one}  <-- origin_key='{args.key}' は既に追認済み（冪等・変更なし）")
            return 0
        print(
            f"[registry] {one} は既に別の業務鍵 "
            f"(origin_key='{entry.get('origin_key')}') で登録済みです。\n"
            f"          番号は奪えません（規則 02 §7 の番号再利用禁止）。人が確認してください。",
            file=sys.stderr,
        )
        return 1

    owner = find_by_origin(ids, str(args.key))
    if owner is not None:
        print(f"[registry] origin_key='{args.key}' は既に {owner} に付いています。"
              f"同じ業務鍵を 2 つの番号に付けません（verify の一意性検査が落ちます）。",
              file=sys.stderr)
        return 1

    entry: dict = {"status": "open"}
    if args.name:
        entry["name"] = args.name
    if args.note:
        entry["description"] = args.note
    entry["origin_key"] = str(args.key)
    if args.parent:
        parent = str(args.parent).upper()
        pkey = PARENT_KEY_BY_PREFIX.get(parent.split("-")[0])
        if pkey is None or parent not in ids:
            print(f"[registry] 親にできない ID です: {args.parent}"
                  f"（台帳に存在する R/F/D/L/E を指定してください）", file=sys.stderr)
            return 2
        entry[pkey] = parent
    if args.used_by:
        entry["used_by"] = args.used_by

    def mutate(lines: list[str], _doc: dict) -> None:
        _insert_entry(lines, one, _render_entry(one, entry))
        new_ids = dict(ids)
        new_ids[one] = entry
        _sync_counts(lines, new_ids)

    def expect(parsed: dict):
        if one not in (parsed.get("ids") or {}):
            return f"{one} が書き込まれていない"
        return None

    print(f"[registry] 追認登録: {one}  (origin_key='{args.key}')")
    return _edit(root, mutate, apply=args.apply, label=f"adopt {one}", expect=expect)


def cmd_next(root: Path, args) -> int:
    prefix = args.prefix.upper()
    if prefix not in REGISTRY_PREFIXES:
        print(f"[registry] 未知の接頭辞: {args.prefix}（許容: {', '.join(REGISTRY_PREFIXES)}）",
              file=sys.stderr)
        return 2
    ids = load_registry(root).get("ids") or {}
    base = next_number(ids, prefix)
    width = max(1, args.count)
    for i in range(width):
        print(format_id(prefix, base + i))
    return 0


def _set_status(root: Path, target: str, to: str, *, apply: bool, reason: str | None,
                label: str) -> int:
    if to not in STATUS_DOMAIN:
        print(f"[registry] 不正な status: {to}（許容: {', '.join(STATUS_DOMAIN)}）", file=sys.stderr)
        return 2
    doc = load_registry(root)
    entry = (doc.get("ids") or {}).get(target)
    if not isinstance(entry, dict):
        print(f"[registry] 未登録の ID: {target}", file=sys.stderr)
        return 1

    current = str(entry.get("status") or "")
    if current == to:
        print(f"[registry] {target}: 既に status={to}（変更なし）")
        return 0
    allowed = TRANSITIONS.get(current, set())
    if to not in allowed:
        print(f"[registry] 状態機違反: {target} は {current} → {to} へ遷移できません。"
              f"（{current} から許される遷移: {', '.join(sorted(allowed)) or 'なし'}）\n"
              f"           逆行は禁止です。修正は changed を経由してください（規則 02 §6）。",
              file=sys.stderr)
        return 1

    if to == "baselined":
        trace = _load_trace(root)
        hits = blockers_for(doc, trace, target)
        if hits:
            print(f"[registry] {target} を baselined へ昇格できません。未解除の阻塞項があります:",
                  file=sys.stderr)
            for b in hits:
                print(f"     - {b['id']} [{b['kind']}] {b['text']}  "
                      f"（対象: {', '.join(b['relates_to']) or '—'}）", file=sys.stderr)
            print("           規則 02 §4: 未解決 Q-ID を残したまま baselined に昇格してはならない。",
                  file=sys.stderr)
            return 1

    def mutate(lines: list[str], _doc: dict) -> None:
        _set_field(lines, target, "status", to)
        if reason:
            _set_field(lines, target, "void_reason" if to == "void" else "status_reason", reason)

    def expect(parsed: dict):
        got = ((parsed.get("ids") or {}).get(target) or {}).get("status")
        return None if got == to else f"{target} の status が {got} のまま"

    return _edit(root, mutate, apply=apply, label=label or f"set-status {target} -> {to}",
                 expect=expect)


def cmd_set_status(root: Path, args) -> int:
    return _set_status(root, args.id, args.to, apply=args.apply, reason=args.reason,
                       label=f"set-status {args.id} -> {args.to}")


def cmd_deprecate(root: Path, args) -> int:
    return _set_status(root, args.id, "void", apply=args.apply, reason=args.reason,
                       label=f"deprecate {args.id}")


def cmd_mark_stale(root: Path, args) -> int:
    doc = load_registry(root)
    if args.id not in (doc.get("ids") or {}):
        print(f"[registry] 未登録の ID: {args.id}", file=sys.stderr)
        return 1
    stale = {
        "since": args.since or dt.date.today().isoformat(),
        "reason": args.reason,
        "trigger": args.trigger,
        "by": args.by,
    }

    def mutate(lines: list[str], _doc: dict) -> None:
        _set_field(lines, args.id, "stale", stale)

    def expect(parsed: dict):
        got = ((parsed.get("ids") or {}).get(args.id) or {}).get("stale")
        return None if isinstance(got, dict) and got.get("since") == stale["since"] else "stale 未反映"

    return _edit(root, mutate, apply=args.apply, label=f"mark-stale {args.id}", expect=expect)


def cmd_clear_stale(root: Path, args) -> int:
    doc = load_registry(root)
    if args.id not in (doc.get("ids") or {}):
        print(f"[registry] 未登録の ID: {args.id}", file=sys.stderr)
        return 1

    def mutate(lines: list[str], _doc: dict) -> None:
        _remove_field(lines, args.id, "stale")

    def expect(parsed: dict):
        got = ((parsed.get("ids") or {}).get(args.id) or {}).get("stale")
        return "stale が残っている" if got else None

    return _edit(root, mutate, apply=args.apply, label=f"clear-stale {args.id}", expect=expect)


def cmd_answer(root: Path, args) -> int:
    doc = load_registry(root)
    entry = (doc.get("ids") or {}).get(args.qid)
    if not isinstance(entry, dict):
        print(f"[registry] 未登録の ID: {args.qid}", file=sys.stderr)
        return 1

    def mutate(lines: list[str], _doc: dict) -> None:
        _set_field(lines, args.qid, "answer", args.text)
        _set_field(lines, args.qid, "answer_by", args.by)
        _set_field(lines, args.qid, "answered_at", dt.date.today().isoformat())

    def expect(parsed: dict):
        got = ((parsed.get("ids") or {}).get(args.qid) or {}).get("answer")
        return None if got == args.text else "answer 未反映"

    return _edit(root, mutate, apply=args.apply, label=f"answer {args.qid}", expect=expect)


# --------------------------------------------------------------------------
# verify / blockers
# --------------------------------------------------------------------------

def verify(root: Path) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    path = registry_path(root)
    if not path.is_file():
        return {"ok": False, "errors": [{"check": "exists", "detail": str(path)}],
                "warnings": [], "stats": {}}

    text = _read_text(path)
    doc = load_registry(root)
    ids = doc.get("ids") or {}
    prefixes = ((doc.get("registry") or {}).get("prefixes") or {})

    for key in duplicate_top_keys(text):
        errors.append({"check": "duplicate_key", "detail": f"ID キーが重複: {key}"})

    for key, entry in ids.items():
        key = str(key)
        if not ENTRY_KEY_RE.match(key):
            errors.append({"check": "key_shape", "detail": f"ID の形が不正: {key}"})
            continue
        prefix = key.split("-")[0]
        if prefix not in REGISTRY_PREFIXES:
            errors.append({"check": "prefix", "detail": f"未知の接頭辞: {key}"})
        elif prefixes and prefix not in prefixes:
            errors.append({"check": "prefix_declared",
                           "detail": f"registry.prefixes に未宣言: {prefix}（{key}）"})
        if not isinstance(entry, dict):
            errors.append({"check": "entry_shape", "detail": f"{key} の値が map ではない"})
            continue
        status = str(entry.get("status") or "")
        if status not in STATUS_DOMAIN:
            errors.append({"check": "status", "detail": f"{key} の status が不正: {status!r}"})
        for pk in PARENT_KEYS:
            parent = entry.get(pk)
            if not parent:
                continue
            parent = str(parent)
            if parent not in ids:
                errors.append({"check": "parent_missing",
                               "detail": f"{key}.{pk} = {parent} は未登録"})
            elif str((ids.get(parent) or {}).get("status") or "") == "void":
                errors.append({"check": "parent_void",
                               "detail": f"{key}.{pk} = {parent} は void"})
        used_by = entry.get("used_by")
        if used_by:
            target = root / str(used_by)
            if not target.is_file():
                warnings.append({"check": "used_by_missing",
                                 "detail": f"{key}.used_by が存在しない: {used_by}"})
        elif status != "void":
            warnings.append({"check": "used_by_unset", "detail": f"{key} に used_by が無い"})

    seen_origin: dict[str, str] = {}
    for key, entry in ids.items():
        if not isinstance(entry, dict):
            continue
        ok = entry.get("origin_key")
        if not ok:
            continue
        ok = str(ok)
        if ok in seen_origin:
            errors.append({"check": "origin_duplicate",
                           "detail": f"origin_key='{ok}' が {seen_origin[ok]} と {key} で重複"})
        else:
            seen_origin[ok] = str(key)

    actual = count_by_prefix(ids)
    summary = doc.get("prefix_count_summary")
    if not isinstance(summary, dict):
        errors.append({"check": "count_summary", "detail": "prefix_count_summary が無い"})
    else:
        for prefix in REGISTRY_PREFIXES:
            # 未記載は「0 件」と読む（旧版は -1 で必ず落とした）。接頭辞を新設した直後、
            # 台帳にまだ 1 件も無い段階で summary を赤くしないため。件数が 0 でないのに
            # 行が無ければ、下の不一致として正しく落ちる。
            if int(summary.get(prefix, 0)) != actual.get(prefix, 0):
                errors.append({
                    "check": "count_summary",
                    "detail": f"prefix_count_summary.{prefix} = {summary.get(prefix)} "
                              f"だが実際は {actual.get(prefix, 0)}",
                })

    stats = {
        "total_ids": len(ids),
        "by_prefix": actual,
        "duplicate_keys": len(duplicate_top_keys(text)),
        "unresolved_blockers": len(unresolved_blockers(doc)),
    }
    return {"ok": not errors, "errors": errors, "warnings": warnings, "stats": stats}


def cmd_verify(root: Path, args) -> int:
    result = verify(root)
    stats = result["stats"]
    print(f"[registry] verify: total_ids={stats.get('total_ids', 0)} "
          f"errors={len(result['errors'])} warnings={len(result['warnings'])} "
          f"unresolved_blockers={stats.get('unresolved_blockers', 0)}")
    for item in result["errors"]:
        print(f"  !! [{item['check']}] {item['detail']}", file=sys.stderr)
    for item in result["warnings"]:
        print(f"  ?? [{item['check']}] {item['detail']}", file=sys.stderr)
    # 連番の空隙は**誤りではない**。prefix_blocks（Phase 3）が未落地で、
    # ブロック予約は構造的に空隙を生むため、ここでは情報としてのみ出す。
    gaps = _gaps(load_registry(root).get("ids") or {})
    if gaps:
        print(f"[registry] 参考: 連番の空隙（誤りではない）: {', '.join(gaps)}")

    if args.json:
        out = (root / args.json) if not os.path.isabs(args.json) else Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[registry] report -> {rel(root, out)}")

    if result["errors"]:
        return 1
    if args.strict and result["warnings"]:
        return 1
    return 0


def _gaps(ids: dict) -> list[str]:
    out: list[str] = []
    for prefix in REGISTRY_PREFIXES:
        pat = re.compile(rf"^{re.escape(prefix)}-(\d+)$")
        numbers = sorted(int(m.group(1)) for k in ids if (m := pat.match(str(k))))
        if not numbers:
            continue
        missing = [n for n in range(numbers[0], numbers[-1] + 1) if n not in numbers]
        if missing:
            out.append(f"{prefix}: {', '.join(format_id(prefix, n) for n in missing)}")
    return out


def cmd_blockers(root: Path, args) -> int:
    doc = load_registry(root)
    items = unresolved_blockers(doc)
    if args.json:
        payload = json.dumps(items, ensure_ascii=False, indent=2)
        if args.json == "-":
            print(payload)
        else:
            out = (root / args.json) if not os.path.isabs(args.json) else Path(args.json)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(payload, encoding="utf-8")
            print(f"[registry] report -> {rel(root, out)}")
    if not items:
        print("[registry] blockers: 未解除の阻塞項はありません。")
        return 0
    print(f"[registry] blockers: 未解除 {len(items)} 件")
    for b in items:
        print(f"  - {b['id']} [{b['kind']}] {b['text']}  対象: {', '.join(b['relates_to']) or '—'}")
    return 1 if args.strict else 0


def _load_trace(root: Path) -> dict:
    path = traceability_path(root)
    if not path.is_file():
        return {}
    with open(path, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    return doc if isinstance(doc, dict) else {}


# --------------------------------------------------------------------------
# self-test（合成ツリー。実在の ids.yml には一切触れない）
# --------------------------------------------------------------------------

_SYNTHETIC_IDS = """\
registry:
  description: "self-test 用の合成台帳"
  owner: AI-SE
  version: 0.0.0
  prefixes:
    R: "Requirements"
    Q: "Quality"
    F: "Functional"
    I: "Item"
    D: "Data"
    L: "Logic"
    E: "Error"
    TC: "Test Case"
    CR: "Change Request"
    BUG: "Bug"

ids:
  R-101:
    status: baselined
    name: "合成要求"
    used_by: docs/10_requirements/R-101-x.yaml
  F-042:
    status: baselined
    name: "合成機能"
    r_id: R-101
    used_by: docs/20_basic_design/F-042-x.yaml
  BUG-001:
    status: void
    name: "無効票"
    description: "void の記入例"
    used_by: docs/00_registry/ids.yml

prefix_count_summary:
  R: 1
  Q: 0
  F: 1
  I: 0
  D: 0
  L: 0
  E: 0
  TC: 0
  CR: 0
  BUG: 1
"""

_SYNTHETIC_TRACE = """\
meta:
  root: R-101
back_links:
  F-042: [R-101]
forward_links:
  R-101: [F-042]
"""


class _NS:
    """self-test 用の擬似名前空間。"""

    def __init__(self, **kw):
        self.__dict__.update(kw)


def self_test(verbose: bool = True) -> tuple[bool, list[str]]:
    failures: list[str] = []
    checks: list[str] = []

    def check(label: str, condition: bool) -> None:
        if condition:
            checks.append(label)
        else:
            failures.append(label)

    with tempfile.TemporaryDirectory(prefix="tcai-registry-selftest-") as tmp:
        root = Path(tmp)
        reg_dir = root / "docs" / "00_registry"
        reg_dir.mkdir(parents=True)
        (reg_dir / "ids.yml").write_text(_SYNTHETIC_IDS, encoding="utf-8")
        (reg_dir / "traceability.yml").write_text(_SYNTHETIC_TRACE, encoding="utf-8")
        (root / "docs" / "10_requirements").mkdir(parents=True)
        (root / "docs" / "20_basic_design").mkdir(parents=True)
        (root / "docs" / "10_requirements" / "R-101-x.yaml").write_text("x: 1\n", encoding="utf-8")
        (root / "docs" / "20_basic_design" / "F-042-x.yaml").write_text("x: 1\n", encoding="utf-8")

        # --- 1. verify（合成台帳は健全） ---
        res = verify(root)
        check("verify: 合成台帳が健全", res["ok"])
        check("verify: 総数 3", res["stats"]["total_ids"] == 3)

        # --- 2. next ---
        check("next: I の次は I-001", format_id("I", next_number(load_registry(root)["ids"], "I")) == "I-001")
        check("next: R の次は R-102", format_id("R", next_number(load_registry(root)["ids"], "R")) == "R-102")

        # --- 3. alloc はドライランが既定（書かない） ---
        before = _read_text(reg_dir / "ids.yml")
        rc = cmd_alloc(root, _NS(prefix="I", key="画面A", name="項目A", note=None, kind=None,
                                 block=False, relates_to=None, used_by=None, apply=False))
        check("alloc: ドライランは Exit 0", rc == 0)
        check("alloc: ドライランは書かない", _read_text(reg_dir / "ids.yml") == before)

        # --- 4. alloc --apply で発号 ---
        rc = cmd_alloc(root, _NS(prefix="I", key="画面A", name="項目A", note=None, kind=None,
                                 block=False, relates_to=None, used_by=None, apply=True))
        doc = load_registry(root)
        check("alloc: --apply で Exit 0", rc == 0)
        check("alloc: I-001 が発号される", "I-001" in (doc.get("ids") or {}))
        check("alloc: origin_key が記録される",
              (doc["ids"]["I-001"] or {}).get("origin_key") == "画面A")
        check("alloc: prefix_count_summary が同期される",
              (doc.get("prefix_count_summary") or {}).get("I") == 1)

        # --- 5. 冪等（同じ key は同じ ID） ---
        rc = cmd_alloc(root, _NS(prefix="I", key="画面A", name="項目A", note=None, kind=None,
                                 block=False, relates_to=None, used_by=None, apply=True))
        doc = load_registry(root)
        check("alloc: 再実行も Exit 0（冪等）", rc == 0)
        check("alloc: 同じ key で番号が増えない",
              sum(1 for k in doc["ids"] if str(k).startswith("I-")) == 1)

        # --- 6. 同一業務鍵に別の名前を与えたら拒否 ---
        rc = cmd_alloc(root, _NS(prefix="I", key="画面A", name="別の名前", note=None, kind=None,
                                 block=False, relates_to=None, used_by=None, apply=True))
        check("alloc: 同一 key に別名は Exit 1", rc == 1)

        # --- 7. void 番号は再利用しない ---
        cmd_deprecate(root, _NS(id="I-001", reason="試験", apply=True))
        rc = cmd_alloc(root, _NS(prefix="I", key="画面B", name="項目B", note=None, kind=None,
                                 block=False, relates_to=None, used_by=None, apply=True))
        doc = load_registry(root)
        check("deprecate: I-001 が void", (doc["ids"]["I-001"] or {}).get("status") == "void")
        check("alloc: void 番号を再利用しない", "I-002" in doc["ids"] and rc == 0)
        # 同じ origin_key を再投入した場合。void を「割当て済み」として返してはいけない
        # （作废番号を現役として使わせることになる）し、黙って別番号も振らない。
        rc = cmd_alloc(root, _NS(prefix="I", key="画面A", name="項目A", note=None, kind=None,
                                 block=False, relates_to=None, used_by=None, apply=True))
        after = load_registry(root)
        check("alloc: void 済み key の再投入は Exit 1", rc == 1)
        check("alloc: void 済み key の再投入で新番号を振らない",
              "I-003" not in (after.get("ids") or {}))
        check("alloc: void 済み key の再投入で I-001 を書き換えない",
              (after["ids"]["I-001"] or {}).get("status") == "void")

        # --- 8. 阻塞项が baselined を止める ---
        rc = cmd_alloc(root, _NS(prefix="Q", key="Q:画面A:enter", name=None, note=None,
                                 kind="question", block=True, relates_to=["R-101"],
                                 used_by=None, apply=True))
        doc = load_registry(root)
        check("alloc: Q-001 が発号される", "Q-001" in (doc.get("ids") or {}))
        rc = _set_status(root, "R-101", "baselined", apply=True, reason=None, label="")
        # R-101 は既に baselined なので「変更なし」で 0 になる → draft へは戻せないため
        # 直接 blockers_for を検証する
        hits = blockers_for(doc, _load_trace(root), "F-042")
        check("blockers: R-101 を対象とする未解除項が F-042 を阻塞する",
              [b["id"] for b in hits] == ["Q-001"])
        check("blockers: R-101 自身も阻塞される",
              [b["id"] for b in blockers_for(doc, _load_trace(root), "R-101")] == ["Q-001"])

        # --- 9. answer で解除 ---
        rc = cmd_answer(root, _NS(qid="Q-001", text="発火する", by="SE-001", apply=True))
        doc = load_registry(root)
        check("answer: Exit 0", rc == 0)
        check("answer: answer が入る", (doc["ids"]["Q-001"] or {}).get("answer") == "発火する")
        check("answer: 阻塞が解除される", blockers_for(doc, _load_trace(root), "F-042") == [])

        # --- 10. 状態機（逆行禁止） ---
        rc = _set_status(root, "R-101", "open", apply=True, reason=None, label="")
        check("状態機: baselined -> open を拒否", rc == 1)
        rc = _set_status(root, "R-101", "done", apply=True, reason=None, label="")
        check("状態機: baselined -> done を許可", rc == 0)

        # --- 11. mark-stale / clear-stale ---
        rc = cmd_mark_stale(root, _NS(id="F-042", reason="上流変更", trigger="R-101",
                                      by="SE-001", since="2026-01-01", apply=True))
        doc = load_registry(root)
        stale = (doc["ids"]["F-042"] or {}).get("stale")
        check("mark-stale: Exit 0 かつ status は不変", rc == 0 and
              isinstance(stale, dict) and (doc["ids"]["F-042"] or {}).get("status") == "baselined")
        check("mark-stale: trigger が記録される", isinstance(stale, dict) and
              stale.get("trigger") == "R-101")
        rc = cmd_clear_stale(root, _NS(id="F-042", apply=True))
        doc = load_registry(root)
        check("clear-stale: Exit 0 かつ stale が消える",
              rc == 0 and not (doc["ids"]["F-042"] or {}).get("stale"))

        # --- 12. verify が違反を捕まえる ---
        bad = _SYNTHETIC_IDS.replace("  R-101:\n", "  R-101:\n    status: baselined\n    name: \"重複R\"\n    used_by: docs/10_requirements/R-101-x.yaml\n  R-101:\n")
        (reg_dir / "ids.yml").write_text(bad, encoding="utf-8")
        res = verify(root)
        check("verify: 重複キーを捕まえる",
              any(e["check"] == "duplicate_key" for e in res["errors"]))

        bad2 = _SYNTHETIC_IDS.replace("  R: 1", "  R: 99")
        (reg_dir / "ids.yml").write_text(bad2, encoding="utf-8")
        res = verify(root)
        check("verify: prefix_count_summary の不一致を捕まえる",
              any(e["check"] == "count_summary" for e in res["errors"]))

        bad3 = _SYNTHETIC_IDS.replace("    r_id: R-101", "    r_id: R-999")
        (reg_dir / "ids.yml").write_text(bad3, encoding="utf-8")
        res = verify(root)
        check("verify: 父リンクの未登録を捕まえる",
              any(e["check"] == "parent_missing" for e in res["errors"]))

        bad4 = _SYNTHETIC_IDS.replace('    status: baselined\n    name: "合成要求"',
                                      '    status: できた\n    name: "合成要求"')
        (reg_dir / "ids.yml").write_text(bad4, encoding="utf-8")
        res = verify(root)
        check("verify: status 値域違反を捕まえる",
              any(e["check"] == "status" for e in res["errors"]))

        # --- 13. 連番の空隙は誤りではない ---
        (reg_dir / "ids.yml").write_text(_SYNTHETIC_IDS, encoding="utf-8")
        cmd_alloc(root, _NS(prefix="I", key="画面C", name="項目C", note=None, kind=None,
                            block=False, relates_to=None, used_by=None, apply=True))
        # I-001 を手で消して空隙を作る
        text = _read_text(reg_dir / "ids.yml")
        text = text.replace("  I-001:\n", "  I-002:\n", 1)
        (reg_dir / "ids.yml").write_text(text, encoding="utf-8")
        res = verify(root)
        check("verify: 連番の空隙を誤りとしない",
              not any("空隙" in e["detail"] or "gap" in e["check"] for e in res["errors"]))

        # --- 14. コメントが保存される（再ダンプしていない証拠） ---
        (reg_dir / "ids.yml").write_text(_SYNTHETIC_IDS, encoding="utf-8")
        cmd_alloc(root, _NS(prefix="R", key="画面D", name="要求D", note=None, kind=None,
                            block=False, relates_to=None, used_by=None, apply=True))
        text = _read_text(reg_dir / "ids.yml")
        check("差分編集: registry の description 行が残る",
              'description: "self-test 用の合成台帳"' in text)

        # --- 15. 別の接頭辞で番号が独立している ---
        check("next: 接頭辞ごとに番号が独立",
              next_number(load_registry(root)["ids"], "TC") == 1)

    if verbose:
        for label in checks:
            print(f"  ok   {label}")
        for label in failures:
            print(f"  FAIL {label}")
        print(f"[registry] self-test: {len(checks)} passed, {len(failures)} failed")
    return (not failures), failures


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="registry",
        description="ID 台帳（ids.yml）唯一の書込み口。書込み系は既定でドライラン。",
    )
    ap.add_argument("--root", help="リポジトリルート（既定: 自動探索）")
    ap.add_argument("--self-test", action="store_true", help="合成ツリーでの自己検証")
    sub = ap.add_subparsers(dest="command")

    p = sub.add_parser("alloc", help="業務鍵で発号する（冪等）")
    p.add_argument("prefix")
    p.add_argument("--key", required=True, help="業務鍵（例: 'R60Area 検索画面'）")
    p.add_argument("--name")
    p.add_argument("--note", help="description に入れる補足")
    p.add_argument("--kind", choices=["question", "issue"])
    p.add_argument("--block", action="store_true", help="未回答なら後続を止める")
    p.add_argument("--relates-to", nargs="*", default=None, help="関連 ID（ids.yml 内のみ。鍵名は related_ids）")
    p.add_argument("--used-by", help="成果物パス")
    p.add_argument("--apply", action="store_true")

    p = sub.add_parser("adopt", help="成果物で既に使われている番号を台帳へ追認登録する（冪等）")
    p.add_argument("id", help="既存の番号（例: TC-201）。**新しい番号は振らない**")
    p.add_argument("--key", required=True, help="業務鍵（例: 'R60Login TC-201 初期表示正常系'）")
    p.add_argument("--name")
    p.add_argument("--note", help="description に入れる補足")
    p.add_argument("--parent", help="親 ID（台帳に存在する R/F/D/L/E）")
    p.add_argument("--used-by", help="成果物パス")
    p.add_argument("--apply", action="store_true")

    p = sub.add_parser("next", help="次の可用番号を表示（書込みなし）")
    p.add_argument("prefix")
    p.add_argument("--count", type=int, default=1)

    p = sub.add_parser("set-status", help="status を遷移させる")
    p.add_argument("id")
    p.add_argument("--to", required=True, choices=list(STATUS_DOMAIN))
    p.add_argument("--reason")
    p.add_argument("--apply", action="store_true")

    p = sub.add_parser("deprecate", help="void にする（番号は再利用しない）")
    p.add_argument("id")
    p.add_argument("--reason", required=True)
    p.add_argument("--apply", action="store_true")

    p = sub.add_parser("mark-stale", help="上流変更で失効したことを記録する（status は変えない）")
    p.add_argument("id")
    p.add_argument("--reason", required=True)
    p.add_argument("--trigger", required=True, help="失効の引き金になった上流 ID")
    p.add_argument("--by", default="(未記入)", help="判定した人の識別子")
    p.add_argument("--since")
    p.add_argument("--apply", action="store_true")

    p = sub.add_parser("clear-stale", help="失効を解除する")
    p.add_argument("id")
    p.add_argument("--apply", action="store_true")

    p = sub.add_parser("answer", help="Q の回答を記入し阻塞を解除する")
    p.add_argument("qid")
    p.add_argument("--text", required=True)
    p.add_argument("--by", required=True, help="回答した人の識別子")
    p.add_argument("--apply", action="store_true")

    p = sub.add_parser("verify", help="台帳の自己検査（読むだけ）")
    p.add_argument("--strict", action="store_true", help="warning も不合格にする")
    p.add_argument("--json")

    p = sub.add_parser("blockers", help="未解除の阻塞項を列挙（読むだけ）")
    p.add_argument("--strict", action="store_true", help="阻塞があれば非ゼロ終了")
    p.add_argument("--json", nargs="?", const="-")

    return ap


def main(argv: list[str] | None = None) -> int:
    reconfigure_stdout()
    ap = build_parser()
    args = ap.parse_args(argv)

    if args.self_test:
        ok, failures = self_test()
        return 0 if ok else 1

    if not args.command:
        ap.print_help()
        return 2

    root = Path(args.root).resolve() if args.root else find_root()
    if not registry_path(root).is_file():
        print(f"[registry] ids.yml が見つかりません: {registry_path(root)}", file=sys.stderr)
        return 2

    handler = {
        "alloc": cmd_alloc,
        "adopt": cmd_adopt,
        "next": cmd_next,
        "set-status": cmd_set_status,
        "deprecate": cmd_deprecate,
        "mark-stale": cmd_mark_stale,
        "clear-stale": cmd_clear_stale,
        "answer": cmd_answer,
        "verify": cmd_verify,
        "blockers": cmd_blockers,
    }[args.command]
    try:
        return handler(root, args)
    except KeyError as exc:
        print(f"[registry] 対象の ID が台帳に見つかりません: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover
        print(f"[registry] 失敗: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
