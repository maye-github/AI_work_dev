"""trans-cosmos-ai SessionStart ブリーフ。

セッション開始時（startup / resume / clear / compact）に、
8 工程の現在地を数行で Claude の context へ差し込む。

★ これは「道しるべ」であって「航海士」ではない。
   **正確な現在ステップは skill 側（SKILL.md §1.1）が産出物から割り出す。**
   本ツールは状態ファイルを要約し、産出物の実在と突き合わせて**ずれを警告する**までを担う。
   ここで承認を推定してはならない（紅線③。承認は人が明示したときのみ）。

- 進行中のワークスペースが無ければ**何も出力しない**（無音・セッション開始を汚さない）。
- 例外はすべて握り潰し exit 0（SessionStart フックがセッションを壊してはならない）。

使い方:
    py -3 -X utf8 -m tools.coach_brief                 全ワークスペースを平文で
    py -3 -X utf8 -m tools.coach_brief R60Login        そのモジュールだけ（位置引数）
    py -3 -X utf8 -m tools.coach_brief --module R60Login  同上
    py -3 -X utf8 -m tools.coach_brief --hook          SessionStart フック用（JSON で出す）
    py -3 -X utf8 -m tools.coach_brief --self-test

★ --hook が要る理由: フックの素の stdout は **Claude の context にしか入らず、
   人には見えない**。--hook は同じ内容を JSON の `systemMessage` にも入れて画面へ出す。
   これが無いと「フックは動いているのに何も見えない」という状態になる。

- 標準ライブラリ + pyyaml のみ（NFR-6）。機密の実値を書かない（gate6 は tools/**/*.py も走査する）。

依存の唯一真源は `.claude/skills/trans-cosmos-ai-lifecycle-coach/SKILL.md` §3.1。
下の DEPS はその写しである（片方だけ直さないこと）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

# 直接 `py -3 tools/coach_brief.py` として起動された場合（SessionStart フックはこの形で呼ぶ）、
# sys.path[0] は tools/ になり `tools` パッケージが見えない。リポジトリルートを補う。
# `-m tools.coach_brief` で起動された場合は __package__ が入るので何もしない。
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.paths import find_root, rel, reconfigure_stdout  # noqa: E402

# SKILL.md §3.1「依存図」の写し。前提がすべて approved でなければ起動できない。
DEPS: dict[int, tuple[int, ...]] = {
    1: (),
    2: (1,),
    3: (2,),
    4: (3,),
    5: (3,),
    6: (3, 5),
    7: (2, 5, 6),
    8: (7,),
}
NODE_TOTAL = 8
COACH_REL = "docs/00_plan/coach"


def _load(path: Path) -> dict:
    """YAML を読む。壊れていても握り潰して空 dict を返す（フックを落とさない）。"""
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _current_node(nodes: dict[int, dict]) -> int | None:
    """依存が満たされていて、まだ approved でないノードのうち最小番号。"""
    for n in range(1, NODE_TOTAL + 1):
        if nodes.get(n, {}).get("state") == "approved":
            continue
        if all(nodes.get(d, {}).get("state") == "approved" for d in DEPS[n]):
            return n
    return None


def _has_work(nodes: dict[int, dict], changes: dict) -> bool:
    """進行中の作業があるか。無ければブリーフを出さない（無音）。"""
    if any(nodes.get(n, {}).get("state") != "approved" for n in range(1, NODE_TOTAL + 1)):
        return True
    return bool(changes.get("open_changes"))


def brief_for(root: Path, module_dir: Path) -> list[str]:
    """1 ワークスペース分のブリーフ行を返す。出すものが無ければ空リスト。"""
    case = _load(module_dir / "case.yml")
    if not case:
        return []

    nodes = {n: _load(module_dir / f"n{n:02d}.yml") for n in range(1, NODE_TOTAL + 1)}
    changes = _load(module_dir / "n09.yml")
    if not _has_work(nodes, changes):
        return []

    module = case.get("module") or module_dir.name
    kind = case.get("case_kind") or "-"
    approved = sum(1 for n in nodes.values() if n.get("state") == "approved")
    open_changes = len(changes.get("open_changes") or [])

    lines = [f"[coach] {module}（{kind}） {approved}/{NODE_TOTAL} 已承认"]

    cur = _current_node(nodes)
    if cur is None:
        lines.append("  8 工程全部已承认。之后只剩变更环（n09）。")
    else:
        node = nodes[cur]
        name = node.get("name") or "-"
        state = node.get("state") or "-"
        owner = node.get("owner") or "未认领"
        done = node.get("steps_done", 0)
        total = node.get("steps_total", 0)
        lines.append(f"  当前位置: 节点{cur} {name}（state={state} / {done}/{total} 步 / owner={owner}）")

        arts = node.get("artifacts") or []
        if arts:
            missing = [a for a in arts if not (root / a).exists()]
            if missing:
                lines.append(
                    f"  ⚠ 产出物 {len(arts) - len(missing)}/{len(arts)} 实存"
                    f"（缺: {missing[0]}{' 等' if len(missing) > 1 else ''}）"
                    " ← 状态与磁盘不一致，以磁盘为准"
                )
            else:
                lines.append(f"  产出物 {len(arts)}/{len(arts)} 实存")

        # 未確定事項の件数を **分類別**に出す（人が裁定した category）。
        # 「どこを見れば裁定の結果が分かるか」を毎回ここで示す（2026-10-16 ユーザー指摘）。
        qs = [q for q in (node.get("open_questions") or []) if isinstance(q, dict)]
        if qs:
            by: dict[str, int] = {}
            for q in qs:
                c = q.get("category") or "未裁定"
                by[c] = by.get(c, 0) + 1
            parts = " / ".join(f"{k} {by[k]}" for k in ("A", "B", "C", "未裁定") if k in by)
            line = f"  未确定事项 {len(qs)} 件（{parts}）"
            # ★「分類した」≠「決まった」。answer が埋まっていない件数を出す（SKILL.md §7 鉄則 18）。
            unanswered = [q for q in qs if not q.get("answer")]
            if unanswered:
                line += f"／★未回答 {len(unanswered)} 件"
                if any(q.get("block") for q in unanswered):
                    line += "（阻塞あり → 承认不可）"
            lines.append(line)

    if open_changes:
        lines.append(f"  ⚠ 未处理的变更 {open_changes} 件（n09.yml）")

    handoff = module_dir / "handoff.md"
    if handoff.is_file():
        lines.append(f"  有交接票: {rel(root, handoff)}（开始前先读）")

    lines.append("  ▶ 继续请打 `/trans-cosmos-ai-lifecycle-coach`（它从产出文件算出准确位置）")
    return lines


def collect(root: Path, modules: list[str] | None = None) -> list[str]:
    """ワークスペースのブリーフを連結する。

    modules を渡すとそのモジュールだけに絞る（大文字小文字は区別しない）。
    指定したモジュールが無ければ、黙って空を返さず**その旨を 1 行で告げる**
    （「無言」と「打ち間違い」が区別できなくなるのを防ぐ）。
    """
    coach = root / COACH_REL
    if not coach.is_dir():
        return []
    want = {m.lower() for m in (modules or [])}
    found: set[str] = set()
    out: list[str] = []
    for module_dir in sorted(p for p in coach.iterdir() if p.is_dir()):
        if want and module_dir.name.lower() not in want:
            continue
        found.add(module_dir.name.lower())
        block = brief_for(root, module_dir)
        if block:
            out.extend(block)
        elif want:
            out.append(f"[coach] {module_dir.name} —— 没有进行中的工作（已全部承认／无未处理变更）")
    for name in sorted(want - found):
        out.append(f"[coach] 找不到模块 {name}（docs/00_plan/coach/ 下没有这个目录）")
    return out


def _parse_args(argv: list[str]) -> tuple[bool, list[str]]:
    """(--hook か, モジュール名の一覧)。位置引数もモジュール名として受ける。"""
    hook = False
    modules: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--hook":
            hook = True
        elif a in ("--module", "-m"):
            i += 1
            if i < len(argv):
                modules.append(argv[i])
        elif a.startswith("--module="):
            modules.append(a.split("=", 1)[1])
        elif not a.startswith("-"):
            modules.append(a)
        i += 1
    return hook, modules


def _self_test() -> int:
    """合成ワークスペースで検証する（実ディスクに触らない）。"""
    import tempfile

    passed = failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        coach = root / COACH_REL
        coach.mkdir(parents=True)

        def write(module: str, n01_state: str, arts: list[str], open_changes: list) -> Path:
            d = coach / module
            d.mkdir(exist_ok=True)
            (d / "case.yml").write_text(
                f"module: {module}\ncase_kind: tutorial\n", encoding="utf-8"
            )
            for n in range(1, NODE_TOTAL + 1):
                state = n01_state if n == 1 else "not_started"
                art = arts if n == 1 else []
                (d / f"n{n:02d}.yml").write_text(
                    f"node: {n}\nname: \"node{n}\"\nstate: {state}\nowner: null\n"
                    f"steps_total: 5\nsteps_done: 0\n"
                    f"artifacts: {art!r}\n".replace("'", '"'),
                    encoding="utf-8",
                )
            (d / "n09.yml").write_text(
                f"node: 9\nopen_changes: {open_changes!r}\nclosed_changes: []\n".replace("'", '"'),
                encoding="utf-8",
            )
            return d

        def check(label: str, cond: bool) -> None:
            nonlocal passed, failed
            if cond:
                passed += 1
                print(f"  ok   {label}")
            else:
                failed += 1
                print(f"  FAIL {label}")

        # 1) 進行中 → ブリーフが出る
        write("M1", "not_started", [], [])
        lines = collect(root)
        check("進行中なら出力する", len(lines) > 0)
        check("現在地はノード1", any("节点1" in x for x in lines))
        check("入口コマンドを案内する", any("lifecycle-coach" in x for x in lines))

        # 2) 産出物の欠落を警告する
        write("M2", "not_started", ["tutorial/M2/存在しない.md"], [])
        lines = collect(root)
        check("産出物の欠落を警告する", any("缺:" in x for x in lines))

        # 3) 全承認かつ変更なし → 無音
        for f in coach.rglob("*.yml"):
            txt = f.read_text(encoding="utf-8")
            f.write_text(txt.replace("not_started", "approved"), encoding="utf-8")
        check("全承認かつ変更なしは無音", collect(root) == [])

        # 4) 全承認でも未処理の要変更があれば出す
        (coach / "M1" / "n09.yml").write_text(
            "node: 9\nopen_changes: [{case_ref: \"BUG-002\"}]\nclosed_changes: []\n",
            encoding="utf-8",
        )
        lines = collect(root)
        check("未処理の変更があれば出す", any("未处理的变更" in x for x in lines))

        # 5) 壊れた YAML でも例外を出さない
        (coach / "M1" / "case.yml").write_text("module: [壊れている\n", encoding="utf-8")
        try:
            collect(root)
            check("壊れた YAML を握り潰す", True)
        except Exception:  # pragma: no cover
            check("壊れた YAML を握り潰す", False)

        # 6) --module でモジュールを絞れる（大文字小文字は無視）
        write("M3", "not_started", [], [])
        lines = collect(root, ["m3"])
        check("--module で絞れる", any("M3" in x for x in lines) and not any("M1" in x for x in lines))

        # 9) 未確定事項を分類別の件数で出す
        (coach / "M3" / "n01.yml").write_text(
            'node: 1\nname: "n1"\nstate: in_progress\nowner: null\n'
            "steps_total: 5\nsteps_done: 3\nartifacts: []\n"
            "open_questions:\n"
            '  - {q_ref: Q-001, text: "a", kind: question, category: A, block: false}\n'
            '  - {q_ref: Q-002, text: "b", kind: question, category: B, block: false}\n'
            '  - {q_ref: Q-003, text: "c", kind: question, category: C, block: false}\n',
            encoding="utf-8",
        )
        lines = collect(root, ["M3"])
        check(
            "未確定事項を分類別件数で出す",
            any("未确定事项 3 件" in x and "A 1" in x and "B 1" in x and "C 1" in x for x in lines),
        )
        check("未回答件数を出す（分類≠決定）", any("未回答 3 件" in x for x in lines))
        (coach / "M3" / "n01.yml").write_text(
            'node: 1\nname: "n1"\nstate: in_progress\nowner: null\n'
            "steps_total: 5\nsteps_done: 3\nartifacts: []\n"
            "open_questions:\n"
            '  - {q_ref: Q-005, text: "e", kind: question, category: A, block: true, answer: "回答済み"}\n',
            encoding="utf-8",
        )
        check(
            "全部回答済みなら未回答を出さない",
            not any("未回答" in x for x in collect(root, ["M3"])),
        )
        (coach / "M3" / "n01.yml").write_text(
            'node: 1\nname: "n1"\nstate: in_progress\nowner: null\n'
            "steps_total: 5\nsteps_done: 3\nartifacts: []\n"
            "open_questions:\n"
            '  - {q_ref: Q-006, text: "f", kind: question, category: A, block: true, answer: null}\n',
            encoding="utf-8",
        )
        check(
            "阻塞ありかつ未回答なら承認不可と告げる",
            any("承认不可" in x for x in collect(root, ["M3"])),
        )
        (coach / "M3" / "n01.yml").write_text(
            'node: 1\nname: "n1"\nstate: in_progress\nowner: null\n'
            "steps_total: 5\nsteps_done: 3\nartifacts: []\n"
            "open_questions:\n"
            '  - {q_ref: Q-004, text: "d", kind: question, category: null, block: false}\n',
            encoding="utf-8",
        )
        check(
            "未裁定があればそれも出す",
            any("未裁定 1" in x for x in collect(root, ["M3"])),
        )

        # 7) 無いモジュールを指定したら黙らず告げる
        lines = collect(root, ["NOPE"])
        check("無いモジュールは告げる", any("找不到模块" in x for x in lines))

        # 8) 引数解析（位置引数もモジュール名として受ける）
        check("--hook を解釈する", _parse_args(["--hook"])[0] is True)
        check("位置引数をモジュール名とする", _parse_args(["R60Login"]) == (False, ["R60Login"]))
        check("--module=X 形式を解釈する", _parse_args(["--module=X"]) == (False, ["X"]))

    print(f"[coach_brief:self-test] {'PASS' if failed == 0 else 'FAIL'} {passed}/{passed + failed} pass")
    return 0 if failed == 0 else 1


def main(argv: list[str] | None = None) -> int:
    reconfigure_stdout()
    args = list(sys.argv[1:] if argv is None else argv)
    if "--self-test" in args:
        return _self_test()
    hook, modules = _parse_args([a for a in args if a != "--self-test"])
    try:
        lines = collect(find_root(), modules)
    except Exception:  # pragma: no cover - フックを絶対に落とさない
        return 0
    if not lines:
        return 0
    text = "\n".join(lines)
    if hook:
        # SessionStart フックの素の stdout は Claude の context に入るだけで、
        # **人の目には見えない**。systemMessage に同じ内容を入れて画面へも出す。
        # （これが無いと「フックは動いているのに何も見えない」になる）
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "SessionStart",
                        "additionalContext": text,
                    },
                    "systemMessage": text,
                },
                ensure_ascii=False,
            )
        )
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
