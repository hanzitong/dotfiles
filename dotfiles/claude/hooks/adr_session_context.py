#!/usr/bin/env python3
"""SessionStart フック: プロジェクトの中の ADR のうち、状態が「採用」と「提案」のものの一覧を、セッションの文脈に入れる。

目的: Claude が、アーキテクチャの相談や設計の変更を始める前に、いま有効な決定を知っている状態にする。
知らないまま提案すると、採用済みの ADR と矛盾する提案をしてしまう。

ADR のディレクトリ（ADR-*.md のファイルを直下に持つディレクトリ）の探し方は、adr_lint.py と同じである。
1つのプロジェクトに ADR のディレクトリがいくつあっても、ディレクトリごとに一覧を出す。
ADR のディレクトリがないプロジェクトでは、何もしない。

手で実行する（いまの使い方。adr-context スキルが使う）
    python3 ~/.claude/hooks/adr_session_context.py <ディレクトリ> [<ディレクトリ> ...]

フックとして使う（社内の設定でユーザーのフックが許されたときの使い方）
    引数なしで呼ぶと、標準入力から Claude Code のフックの JSON を読み、
    標準出力に JSON（hookSpecificOutput.additionalContext）を書く。SessionStart に登録する。
"""
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# adr_lint.py を import したときに、dotfiles の中に __pycache__ を作らない。
sys.dont_write_bytecode = True
from adr_lint import (  # noqa: E402  （上の設定を、import より先に効かせるため）
    ADR_FILE_GLOB,
    INDEX_LISTING_TABLE_HEADER,
    LINKED_ADR_ID_PATTERN,
    find_adr_dirs,
    read_markdown_tables,
)

# セッションの開始のたびに探すので、adr_lint.py の手での実行より浅くして、時間をかけない。
_MAX_ADR_DIR_SEARCH_DEPTH: int = 3
# 一覧に題名まで並べる状態。ほかの状態（置き換え済み、廃止）は、件数だけを出す。
_LISTED_ADR_STATUSES: tuple[str, ...] = ("採用", "提案")


def _summarize_adr_listing(adr_dir: Path, project_dir: Path) -> list[str]:
    """
    目的: 1つの ADR のディレクトリについて、いま有効な決定（採用）と、検討中の決定（提案）を、
    Claude が短く読める行にまとめる。

    INDEX.md の「一覧」の表を読む。INDEX.md がなければ、そのことを1行で返す。
    project_dir は、行の中に出すパスを短くするためだけに使う。
    """
    index_file_path: Path = adr_dir / "INDEX.md"
    index_path_for_display: Path = (
        index_file_path.relative_to(project_dir)
        if index_file_path.is_relative_to(project_dir)
        else index_file_path
    )
    if not index_file_path.is_file():
        return [f"[ADR の一覧] {index_path_for_display} がありません。"]

    listing_rows: list[list[str]] = read_markdown_tables(
        index_file_path.read_text(encoding="utf-8")
    ).get(INDEX_LISTING_TABLE_HEADER, [])
    listed_adr_lines_by_status: dict[str, list[str]] = {
        listed_status: [] for listed_status in _LISTED_ADR_STATUSES
    }
    unlisted_status_adr_cnt: int = 0
    for listing_row in listing_rows:
        if len(listing_row) != 4:
            continue
        linked_id_cell, listed_title, listed_status, _listed_decision_date = listing_row
        linked_id_match: re.Match[str] | None = LINKED_ADR_ID_PATTERN.match(linked_id_cell)
        if not linked_id_match:
            continue
        if listed_status in listed_adr_lines_by_status:
            listed_adr_lines_by_status[listed_status].append(f"- {linked_id_match.group(1)}: {listed_title}")
        else:
            unlisted_status_adr_cnt += 1

    summary_lines: list[str] = [
        f"[ADR の一覧] {index_path_for_display} の「一覧」より（このセッションの開始時点）"
    ]
    for listed_status, listed_adr_lines in listed_adr_lines_by_status.items():
        summary_lines.append(f"状態が「{listed_status}」の ADR: {len(listed_adr_lines)} 件")
        summary_lines.extend(listed_adr_lines)
    if unlisted_status_adr_cnt:
        summary_lines.append(
            f"状態が「置き換え済み」「廃止」の ADR: {unlisted_status_adr_cnt} 件（題名は INDEX.md を見る）"
        )
    return summary_lines


def _build_session_context_text(search_root_dirs: list[Path]) -> str:
    """
    目的: 見つけたすべての ADR のディレクトリの一覧と、ADR を扱うときの注意を、
    Claude に渡す1つの文にまとめる。

    ADR のディレクトリが1つもなければ、空の文字列を返す（呼ぶ側は、何も出力しない）。
    """
    context_lines: list[str] = []
    for search_root_dir in search_root_dirs:
        for found_adr_dir in find_adr_dirs(search_root_dir, _MAX_ADR_DIR_SEARCH_DEPTH):
            context_lines.extend(_summarize_adr_listing(found_adr_dir, search_root_dir))
    if not context_lines:
        return ""
    context_lines += [
        "- アーキテクチャの相談や設計の変更では、提案の前に、対象の INDEX.md と関係する ADR を読み、"
        "状態が「採用」の ADR と矛盾しないかを確かめる。",
        "- ADR と INDEX.md を書くとき、直すときは、adr スキルに従う。",
        "- 別のセッションやユーザーが更新していることがある。作業の前に INDEX.md を読み直す。",
    ]
    return "\n".join(context_lines)


def _run_as_hook() -> int:
    """
    目的: SessionStart フックとして、セッションの開始時、/clear のあと、文脈の圧縮のあとに、
    ADR の一覧を Claude の文脈に入れる。

    フックの失敗でセッションを止めないよう、どの場合も 0 を返す。
    """
    try:
        hook_input: dict[str, Any] = json.load(sys.stdin)
    except json.JSONDecodeError:
        hook_input = {}
    project_dir: Path = Path(os.environ.get("CLAUDE_PROJECT_DIR") or hook_input.get("cwd") or os.getcwd())
    session_context_text: str = _build_session_context_text([project_dir])
    if not session_context_text:
        return 0
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": session_context_text,
        }
    }, ensure_ascii=False))
    return 0


def _run_from_command_line(search_root_texts: list[str]) -> int:
    """
    目的: フックが動かない環境で、Claude やユーザーが、同じ一覧を手で表示できるようにする。

    終了コードは、一覧を出せたら 0、ADR のディレクトリが1つも見つからなければ 2。
    """
    search_root_dirs: list[Path] = [
        Path(search_root_text).expanduser().resolve() for search_root_text in search_root_texts
    ]
    session_context_text: str = _build_session_context_text(search_root_dirs)
    if not session_context_text:
        searched_dirs_text: str = ", ".join(str(search_root_dir) for search_root_dir in search_root_dirs)
        print(f"{searched_dirs_text} の下に、ADR のディレクトリ（{ADR_FILE_GLOB} を持つディレクトリ）がありません。")
        return 2
    print(session_context_text)
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(_run_from_command_line(sys.argv[1:]))
    try:
        sys.exit(_run_as_hook())
    except Exception:
        # フックの失敗で、セッションを止めない。
        sys.exit(0)
