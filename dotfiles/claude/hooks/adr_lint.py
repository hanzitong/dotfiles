#!/usr/bin/env python3
"""ADR と管理台帳（INDEX.md）の書式を検査する。手で実行することも、フックとして使うこともできる。

目的: adr スキル（~/.claude/skills/adr/SKILL.md）が決めた書式の誤りを、目で見るのではなく、
機械で確実に見つける。特に、ADR を足したり置き換えたりしたときの、INDEX.md の直し忘れを見つける。
中身の点検（選択肢は十分か、理由は納得できるかなど）は、このスクリプトの役割ではない。

ADR のディレクトリとは、ADR-*.md のファイルを直下に持つディレクトリのことである。
どのプロジェクトのどこにあっても、このスクリプトは同じように見つけて検査する。

手で実行する（いまの使い方）
    python3 ~/.claude/hooks/adr_lint.py <ディレクトリ> [<ディレクトリ> ...]
    - 引数には、ADR のディレクトリそのものか、その上のディレクトリ（プロジェクトなど）を渡す。
      上のディレクトリを渡すと、その下にある ADR のディレクトリを探して、すべて検査する。
    - 終了コード: 問題がなければ 0、問題があれば 1、ADR のディレクトリが見つからなければ 2。

フックとして使う（社内の設定でユーザーのフックが許されたときの使い方）
    引数なしで呼ぶと、標準入力から Claude Code のフックの JSON を読む。PostToolUse に登録する。
    - Edit / Write / MultiEdit が、ADR のディレクトリの中のファイルを書き換えたあとに、そのディレクトリを検査する。
    - Bash のコマンドの中に「ADR-0000 の形の番号」か「INDEX.md」が出てきたあと、
      または Bash を ADR のディレクトリの中で実行したあとに、プロジェクトの中の ADR のディレクトリを検査する。
    - 問題がなければ、何も出力しない。

何を検査するか（adr スキルの決まりに合わせている。スキルの決まりを変えたら、このスクリプトも直す）
- ADR のファイル名、1行目の題名、冒頭の3行（ID、決定日、INDEX.md への案内）
- 見出しの種類と順番: 背景、選択肢、決定、理由、影響と残る課題、確かめ方（確かめ方だけは任意）
- 選択肢が2つ以上あり、採用した方法に「（採用）」が付いている（状態が「提案」なら検査しない）
- ADR のファイルに、状態の行や、「追記」「訂正」の印を書いていない
- 2026-10-16 以降の ADR に、冒頭の要約（1文）と、理由の「確信の度合い」（高、中、低）がある
- INDEX.md の一覧とファイルが1対1で対応し、題名と決定日が一致している
- 状態、関係、更新の記録の種類が、決められた語である
- 「置き換え済み」の ADR には、置き換える側の ADR がある。削除した番号のファイルが残っていない
"""
import fnmatch
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, NamedTuple

# ほかのスクリプト（adr_session_context.py）も、ADR のディレクトリを、この形のファイルの有無で見分ける。
ADR_FILE_GLOB: str = "ADR-*.md"
# INDEX.md の「一覧」の表の、見出しの行。adr_session_context.py も、この表を読む。
INDEX_LISTING_TABLE_HEADER: tuple[str, ...] = ("ID", "タイトル", "状態", "決定日")
# 一覧の ID の欄: [ADR-0001](ADR-0001-xxx.md)
LINKED_ADR_ID_PATTERN: re.Pattern[str] = re.compile(r"^\[(ADR-\d{4})\]\(([^)]+)\)$")

_REQUIRED_ADR_HEADINGS: list[str] = ["背景", "選択肢", "決定", "理由", "影響と残る課題"]
_ALLOWED_ADR_HEADINGS_IN_ORDER: list[str] = _REQUIRED_ADR_HEADINGS + ["確かめ方"]
_ALLOWED_ADR_STATUSES: set[str] = {"提案", "採用", "置き換え済み", "廃止"}
_ALLOWED_ADR_RELATIONS: set[str] = {"置き換える", "前提にする", "関連する"}
_ALLOWED_UPDATE_LOG_TYPES: set[str] = {"新規", "追記", "訂正", "置き換え", "削除"}

_INDEX_DELETED_TABLE_HEADER: tuple[str, ...] = ("ID", "書いてあった内容", "削除した理由")
_INDEX_RELATION_TABLE_HEADER: tuple[str, ...] = ("元", "関係", "先", "補足")
_INDEX_UPDATE_LOG_TABLE_HEADER: tuple[str, ...] = ("日付", "ID", "種類", "内容")

_ADR_FILENAME_PATTERN: re.Pattern[str] = re.compile(r"^ADR-(\d{4})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
_ADR_TITLE_LINE_PATTERN: re.Pattern[str] = re.compile(r"^# (ADR-\d{4}): (.+?)\s*$")
_ISO_DATE_PATTERN: re.Pattern[str] = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_FIRST_ISO_DATE_PATTERN: re.Pattern[str] = re.compile(r"\d{4}-\d{2}-\d{2}")
_ADR_ID_PATTERN: re.Pattern[str] = re.compile(r"^ADR-\d{4}$")
_CHANGE_MARK_PATTERN: re.Pattern[str] = re.compile(
    r"[【（(\[]\s*(?:追記|訂正)|(?:追記|訂正)\s*[（(]?\s*\d{4}-\d{2}-\d{2}"
)
_STATUS_LINE_PATTERN: re.Pattern[str] = re.compile(r"^-\s*状態\s*[:：]")
_CONFIDENCE_LINE_PATTERN: re.Pattern[str] = re.compile(r"^-\s*確信の度合い\s*[:：]\s*(高|中|低)")
_ADR_HINT_IN_BASH_COMMAND_PATTERN: re.Pattern[str] = re.compile(r"\bADR-\d{4}|INDEX\.md")
_INDEX_LINK_LINE: str = "- 状態と他の ADR との関係: [INDEX.md](INDEX.md) を参照"

# 要約と確信の度合いは、この日から書く。これより前の ADR には求めない。
_NEW_FORMAT_SINCE_DATE: str = "2026-10-16"
# ADR の冒頭の行（ID、決定日、案内、要約）を探す範囲。1行目の題名は含めない。
_ADR_HEAD_LINE_CNT: int = 9

# プロジェクトの下を探すときの深さ。<プロジェクト>/<システム>/ADR は、深さ 2 に当たる。
_MAX_ADR_DIR_SEARCH_DEPTH: int = 4
# 探すときに入らないディレクトリ。名前が「.」で始まるディレクトリにも入らない。
# backup などには、古い書式のまま残した ADR の写しがあり、検査すると古い誤りを報告してしまう。
_SKIPPED_DIR_NAMES_IN_SEARCH: set[str] = {
    "node_modules", "__pycache__", "venv", "site-packages", "backup", "backups", "archive",
}
# フックが Claude に返す問題の数の上限。多すぎると、Claude の文脈を埋めてしまう。
_MAX_REPORTED_PROBLEMS_IN_HOOK: int = 25


class _AdrFileSummary(NamedTuple):
    """
    目的: 1つの ADR のファイルから読み取った値を、INDEX.md との突き合わせに渡す。
    ファイルの検査と INDEX.md の検査を分けたまま、同じファイルを2回読まずに済ませるためにある。

    読み取れなかった値は None にする（その問題は、ファイルの検査がすでに報告している）。
    """

    adr_id_from_filename: str | None
    title_from_first_line: str | None
    decision_date_text: str | None
    option_headings: list[str]


def find_adr_dirs(search_root_dir: Path, max_search_depth: int) -> list[Path]:
    """
    目的: ADR の置き場所を決め打ちせずに、プロジェクトの中の ADR のディレクトリをすべて見つける。
    1つのリポジトリに、システムごとの ADR のディレクトリ（例: coffee_system/ADR、assembly_system/ADR）が
    いくつあっても、引数を変えずに扱えるようにするためにある。adr_session_context.py からも使う。

    ADR のディレクトリとは、ADR-*.md のファイルを直下に持つディレクトリである。
    search_root_dir そのものが ADR のディレクトリなら、それも含める。
    max_search_depth が 0 なら、search_root_dir だけを確かめる。
    名前が「.」で始まるディレクトリと、依存やキャッシュのディレクトリには入らない。
    戻り値は、見つけた順（ディレクトリ名の順）に並ぶ。
    """
    found_adr_dirs: list[Path] = []
    for walked_dir_text, child_dir_names, child_file_names in os.walk(search_root_dir):
        walked_dir: Path = Path(walked_dir_text)
        if any(fnmatch.fnmatch(file_name, ADR_FILE_GLOB) for file_name in child_file_names):
            found_adr_dirs.append(walked_dir)

        walked_dir_depth: int = len(walked_dir.relative_to(search_root_dir).parts)
        if walked_dir_depth >= max_search_depth:
            child_dir_names.clear()
            continue
        # os.walk は、この list の中身に入っていく。書き換えると、入る先を絞れる。
        child_dir_names[:] = sorted(
            dir_name
            for dir_name in child_dir_names
            if not dir_name.startswith(".") and dir_name not in _SKIPPED_DIR_NAMES_IN_SEARCH
        )
    return found_adr_dirs


def read_markdown_tables(markdown_text: str) -> dict[tuple[str, ...], list[list[str]]]:
    """
    目的: INDEX.md の表（一覧、削除した ADR、関係、更新の記録）を、見出しの行で見分けて取り出す。
    表の位置や順番が変わっても、見出しの行が同じなら読めるようにするためにある。
    adr_session_context.py からも使う。

    戻り値のキーは、見出しの行のセルの並び。値は、区切りの行と空の行を除いた、本体の行のセルの並び。
    同じ見出しの表が2つあれば、行をつなげる。
    """
    tables_by_header: dict[tuple[str, ...], list[list[str]]] = {}
    current_table_rows: list[list[str]] = []
    # 末尾に空の行を足して、最後の表も、表の外に出たところで登録されるようにする。
    for markdown_line in markdown_text.splitlines() + [""]:
        stripped_line: str = markdown_line.strip()
        if stripped_line.startswith("|") and stripped_line.endswith("|"):
            current_table_rows.append([cell.strip() for cell in stripped_line[1:-1].split("|")])
            continue
        # 見出しの行と区切りの行の2行がそろっているものだけを、表として扱う。
        if len(current_table_rows) >= 2:
            table_header: tuple[str, ...] = tuple(current_table_rows[0])
            table_body_rows: list[list[str]] = [
                table_row for table_row in current_table_rows[2:] if any(table_row)
            ]
            tables_by_header.setdefault(table_header, []).extend(table_body_rows)
        current_table_rows = []
    return tables_by_header


def _strip_code_fence_lines(markdown_lines: list[str]) -> list[str]:
    """
    目的: ADR の本文に書いた見本（``` で囲んだコードブロック）の中の見出しや印を、
    本物の見出しや印と取り違えないようにする。

    コードブロックの中の行と、``` の行を除いた行を返す。
    """
    lines_outside_code_fence: list[str] = []
    is_inside_code_fence: bool = False
    for markdown_line in markdown_lines:
        if markdown_line.lstrip().startswith("```"):
            is_inside_code_fence = not is_inside_code_fence
            continue
        if not is_inside_code_fence:
            lines_outside_code_fence.append(markdown_line)
    return lines_outside_code_fence


def _check_adr_file(adr_file_path: Path, found_problems: list[str]) -> _AdrFileSummary:
    """
    目的: 1つの ADR のファイルが、adr スキルの書式（ファイル名、冒頭の行、見出し、選択肢、印）を
    守っているかを確かめる。INDEX.md と突き合わせる値も、あわせて読み取る。

    見つけた問題は found_problems に足す。
    """
    adr_file_name: str = adr_file_path.name
    filename_match: re.Match[str] | None = _ADR_FILENAME_PATTERN.match(adr_file_name)
    adr_id_from_filename: str | None = f"ADR-{filename_match.group(1)}" if filename_match else None
    if not filename_match:
        found_problems.append(
            f"{adr_file_name}: ファイル名が「ADR-<4桁の番号>-<英小文字とハイフンの名前>.md」の形ではない"
        )

    adr_lines: list[str] = adr_file_path.read_text(encoding="utf-8").splitlines()
    title_line_match: re.Match[str] | None = (
        _ADR_TITLE_LINE_PATTERN.match(adr_lines[0]) if adr_lines else None
    )
    title_from_first_line: str | None = None
    if not title_line_match:
        found_problems.append(f"{adr_file_name}: 1行目が「# ADR-0000: 決定の内容」の形ではない")
    else:
        title_from_first_line = title_line_match.group(2)
        if adr_id_from_filename and title_line_match.group(1) != adr_id_from_filename:
            found_problems.append(
                f"{adr_file_name}: 1行目の番号 {title_line_match.group(1)} が、"
                f"ファイル名の番号 {adr_id_from_filename} と違う"
            )

    adr_head_lines: list[str] = adr_lines[1 : 1 + _ADR_HEAD_LINE_CNT]
    if adr_id_from_filename and f"- ID: {adr_id_from_filename}" not in adr_head_lines:
        found_problems.append(f"{adr_file_name}: 冒頭に「- ID: {adr_id_from_filename}」の行がない")
    decision_date_line: str | None = next(
        (head_line for head_line in adr_head_lines if head_line.startswith("- 決定日:")), None
    )
    decision_date_text: str | None = (
        decision_date_line.split(":", 1)[1].strip() if decision_date_line else None
    )
    if not decision_date_line:
        found_problems.append(
            f"{adr_file_name}: 冒頭に「- 決定日: YYYY-MM-DD」の行がない（提案なら「未決定（YYYY-MM-DD に提案）」）"
        )
    if _INDEX_LINK_LINE not in adr_head_lines:
        found_problems.append(f"{adr_file_name}: 冒頭に「{_INDEX_LINK_LINE}」の行がない")
    for head_line in adr_head_lines:
        if _STATUS_LINE_PATTERN.match(head_line):
            found_problems.append(
                f"{adr_file_name}: 状態の行「{head_line.strip()}」がある。状態は INDEX.md にだけ書く"
            )

    adr_body_lines: list[str] = _strip_code_fence_lines(adr_lines)
    section_headings: list[str] = [
        body_line[3:].strip() for body_line in adr_body_lines if body_line.startswith("## ")
    ]
    unknown_headings: list[str] = [
        heading for heading in section_headings if heading not in _ALLOWED_ADR_HEADINGS_IN_ORDER
    ]
    if unknown_headings:
        found_problems.append(
            f"{adr_file_name}: 決まっていない見出し {unknown_headings} がある。"
            f"使える見出しは {_ALLOWED_ADR_HEADINGS_IN_ORDER}"
        )
    missing_headings: list[str] = [
        heading for heading in _REQUIRED_ADR_HEADINGS if heading not in section_headings
    ]
    if missing_headings:
        found_problems.append(f"{adr_file_name}: 見出し {missing_headings} がない")
    allowed_headings_found: list[str] = [
        heading for heading in section_headings if heading in _ALLOWED_ADR_HEADINGS_IN_ORDER
    ]
    if len(allowed_headings_found) != len(set(allowed_headings_found)):
        found_problems.append(f"{adr_file_name}: 同じ見出しが2回以上ある")
    elif allowed_headings_found != sorted(allowed_headings_found, key=_ALLOWED_ADR_HEADINGS_IN_ORDER.index):
        expected_heading_order: list[str] = [
            heading for heading in _ALLOWED_ADR_HEADINGS_IN_ORDER if heading in allowed_headings_found
        ]
        found_problems.append(f"{adr_file_name}: 見出しの順番が {expected_heading_order} になっていない")

    # 「選択肢」の節の ### の見出しを、方法の数として数える。比較のまとめの見出しは、方法ではない。
    option_headings: list[str] = []
    is_inside_options_section: bool = False
    for body_line in adr_body_lines:
        if body_line.startswith("## "):
            is_inside_options_section = body_line[3:].strip() == "選択肢"
        elif is_inside_options_section and body_line.startswith("### ") and "比較のまとめ" not in body_line:
            option_headings.append(body_line[4:].strip())
    if len(option_headings) < 2:
        found_problems.append(f"{adr_file_name}: 「選択肢」に、方法が2つ以上ない（見出し ### で数えた）")

    first_decision_date_match: re.Match[str] | None = _FIRST_ISO_DATE_PATTERN.search(
        decision_date_text or ""
    )
    # 日付の文字列は YYYY-MM-DD なので、文字列の大小で前後を比べられる。
    if first_decision_date_match and first_decision_date_match.group(0) >= _NEW_FORMAT_SINCE_DATE:
        summary_line: str | None = next(
            (head_line for head_line in adr_head_lines if head_line.startswith("- 要約:")), None
        )
        if not summary_line:
            found_problems.append(
                f"{adr_file_name}: 冒頭に「- 要約: 〜」の行がない（{_NEW_FORMAT_SINCE_DATE} 以降の ADR に必要）"
            )
        elif summary_line.count("。") > 1:
            found_problems.append(f"{adr_file_name}: 要約が2文以上になっている。1文にまとめる")

        is_inside_reason_section: bool = False
        reason_has_confidence_line: bool = False
        for body_line in adr_body_lines:
            if body_line.startswith("## "):
                is_inside_reason_section = body_line[3:].strip() == "理由"
            elif is_inside_reason_section and _CONFIDENCE_LINE_PATTERN.match(body_line):
                reason_has_confidence_line = True
        if not reason_has_confidence_line:
            found_problems.append(
                f"{adr_file_name}: 「理由」に「- 確信の度合い: 高、中、低のどれか」の行がない"
                f"（{_NEW_FORMAT_SINCE_DATE} 以降の ADR に必要）"
            )

    for body_line in adr_body_lines:
        if _CHANGE_MARK_PATTERN.search(body_line):
            found_problems.append(
                f"{adr_file_name}: 変更の印らしき「{body_line.strip()[:40]}」がある。"
                "変更の経緯は INDEX.md の更新の記録にだけ書く"
            )
            break

    return _AdrFileSummary(
        adr_id_from_filename=adr_id_from_filename,
        title_from_first_line=title_from_first_line,
        decision_date_text=decision_date_text,
        option_headings=option_headings,
    )


def _lint_adr_dir(adr_dir: Path) -> list[str]:
    """
    目的: 1つの ADR のディレクトリについて、各 ADR のファイルの書式と、INDEX.md との食い違いを、
    まとめて洗い出す。どの ADR がいま有効かを INDEX.md で正しくたどれる状態を保つためにある。

    見つけた問題の文を返す。問題がなければ、空の list を返す。
    """
    found_problems: list[str] = []
    adr_file_summaries_by_id: dict[str, _AdrFileSummary] = {}
    for adr_file_path in sorted(adr_dir.glob(ADR_FILE_GLOB)):
        adr_file_summary: _AdrFileSummary = _check_adr_file(adr_file_path, found_problems)
        if adr_file_summary.adr_id_from_filename:
            adr_file_summaries_by_id[adr_file_summary.adr_id_from_filename] = adr_file_summary

    index_file_path: Path = adr_dir / "INDEX.md"
    if not index_file_path.is_file():
        found_problems.append("INDEX.md がない。adr スキルの assets/index-template.md をもとに作る")
        return found_problems
    index_tables_by_header: dict[tuple[str, ...], list[list[str]]] = read_markdown_tables(
        index_file_path.read_text(encoding="utf-8")
    )
    listing_rows: list[list[str]] = index_tables_by_header.get(INDEX_LISTING_TABLE_HEADER, [])
    deleted_adr_rows: list[list[str]] = index_tables_by_header.get(_INDEX_DELETED_TABLE_HEADER, [])
    relation_rows: list[list[str]] = index_tables_by_header.get(_INDEX_RELATION_TABLE_HEADER, [])
    update_log_rows: list[list[str]] = index_tables_by_header.get(_INDEX_UPDATE_LOG_TABLE_HEADER, [])

    # --- 一覧 ---
    listed_status_by_adr_id: dict[str, str] = {}
    for listing_row in listing_rows:
        if len(listing_row) != 4:
            found_problems.append(f"INDEX.md の一覧: 列の数が4ではない行がある: {listing_row}")
            continue
        linked_id_cell, listed_title, listed_status, listed_decision_date = listing_row
        linked_id_match: re.Match[str] | None = LINKED_ADR_ID_PATTERN.match(linked_id_cell)
        if not linked_id_match:
            found_problems.append(
                f"INDEX.md の一覧: ID の欄が「[ADR-0000](ファイル名)」の形ではない: {linked_id_cell}"
            )
            continue
        listed_adr_id, linked_adr_file_name = linked_id_match.groups()
        if listed_adr_id in listed_status_by_adr_id:
            found_problems.append(f"INDEX.md の一覧: {listed_adr_id} が2回ある")
        listed_status_by_adr_id[listed_adr_id] = listed_status
        if listed_status not in _ALLOWED_ADR_STATUSES:
            found_problems.append(
                f"INDEX.md の一覧: {listed_adr_id} の状態「{listed_status}」は、"
                f"決められた語 {sorted(_ALLOWED_ADR_STATUSES)} ではない"
            )
        if listed_status == "提案":
            if listed_decision_date != "未決定":
                found_problems.append(
                    f"INDEX.md の一覧: 提案の {listed_adr_id} の決定日は「未決定」にする"
                    f"（いまは「{listed_decision_date}」）"
                )
        elif not _ISO_DATE_PATTERN.match(listed_decision_date):
            found_problems.append(
                f"INDEX.md の一覧: {listed_adr_id} の決定日「{listed_decision_date}」が YYYY-MM-DD の形ではない"
            )
        if not (adr_dir / linked_adr_file_name).is_file():
            found_problems.append(
                f"INDEX.md の一覧: {listed_adr_id} のリンク先 {linked_adr_file_name} のファイルがない"
            )
        if listed_adr_id not in adr_file_summaries_by_id:
            continue

        listed_adr_file_summary: _AdrFileSummary = adr_file_summaries_by_id[listed_adr_id]
        if (
            listed_adr_file_summary.title_from_first_line
            and listed_adr_file_summary.title_from_first_line != listed_title
        ):
            found_problems.append(f"{listed_adr_id}: INDEX.md の題名と、ADR の1行目の題名が違う")
        decision_date_in_adr_file: str | None = listed_adr_file_summary.decision_date_text
        if decision_date_in_adr_file is not None:
            if _ISO_DATE_PATTERN.match(listed_decision_date) and not decision_date_in_adr_file.startswith(
                listed_decision_date
            ):
                found_problems.append(
                    f"{listed_adr_id}: 決定日が、INDEX.md（{listed_decision_date}）と"
                    f" ADR（{decision_date_in_adr_file}）で違う"
                )
            if listed_decision_date == "未決定" and not decision_date_in_adr_file.startswith("未決定"):
                found_problems.append(
                    f"{listed_adr_id}: INDEX.md では未決定だが、ADR の決定日は「{decision_date_in_adr_file}」"
                )
        if listed_status != "提案" and not any(
            "（採用）" in option_heading for option_heading in listed_adr_file_summary.option_headings
        ):
            found_problems.append(f"{listed_adr_id}: 採用した方法の見出しに「（採用）」がない")

    for unlisted_adr_id in sorted(set(adr_file_summaries_by_id) - set(listed_status_by_adr_id)):
        found_problems.append(f"{unlisted_adr_id}: ファイルはあるが、INDEX.md の一覧に行がない")

    # --- 削除した ADR ---
    deleted_adr_ids: set[str] = {
        deleted_adr_row[0]
        for deleted_adr_row in deleted_adr_rows
        if deleted_adr_row and _ADR_ID_PATTERN.match(deleted_adr_row[0])
    }
    for deleted_adr_id in sorted(deleted_adr_ids):
        if deleted_adr_id in adr_file_summaries_by_id:
            found_problems.append(f"{deleted_adr_id}: 削除した ADR に載っているが、ファイルが残っている")
        if deleted_adr_id in listed_status_by_adr_id:
            found_problems.append(f"{deleted_adr_id}: 削除した ADR に載っているが、一覧にも残っている")

    # --- 関係 ---
    replaced_adr_ids: set[str] = set()
    for relation_row in relation_rows:
        if len(relation_row) != 4:
            found_problems.append(f"INDEX.md の関係: 列の数が4ではない行がある: {relation_row}")
            continue
        source_adr_id, relation_kind, target_adr_id, _relation_note = relation_row
        if relation_kind not in _ALLOWED_ADR_RELATIONS:
            found_problems.append(
                f"INDEX.md の関係: 「{relation_kind}」は、決められた語 {sorted(_ALLOWED_ADR_RELATIONS)} ではない"
                f"（{source_adr_id} → {target_adr_id}）"
            )
        for related_adr_id in (source_adr_id, target_adr_id):
            if related_adr_id not in listed_status_by_adr_id:
                found_problems.append(
                    f"INDEX.md の関係: {related_adr_id} が一覧にない（{source_adr_id} {relation_kind} {target_adr_id}）"
                )
        if relation_kind == "置き換える":
            replaced_adr_ids.add(target_adr_id)
            if listed_status_by_adr_id.get(target_adr_id) not in (None, "置き換え済み"):
                found_problems.append(
                    f"INDEX.md: {source_adr_id} が {target_adr_id} を置き換えるのに、"
                    f"{target_adr_id} の状態が「置き換え済み」ではない"
                )
    for listed_adr_id, listed_status in listed_status_by_adr_id.items():
        if listed_status == "置き換え済み" and listed_adr_id not in replaced_adr_ids:
            found_problems.append(
                f"INDEX.md: {listed_adr_id} は「置き換え済み」だが、関係に「置き換える」の行がない"
            )

    # --- 更新の記録 ---
    logged_adr_ids: set[str] = set()
    for update_log_row in update_log_rows:
        if len(update_log_row) != 4:
            found_problems.append(f"INDEX.md の更新の記録: 列の数が4ではない行がある: {update_log_row}")
            continue
        logged_date, logged_adr_id, update_log_type, _logged_content = update_log_row
        logged_adr_ids.add(logged_adr_id)
        if not _ISO_DATE_PATTERN.match(logged_date):
            found_problems.append(f"INDEX.md の更新の記録: 日付「{logged_date}」が YYYY-MM-DD の形ではない")
        if update_log_type not in _ALLOWED_UPDATE_LOG_TYPES:
            found_problems.append(
                f"INDEX.md の更新の記録: 種類「{update_log_type}」は、"
                f"決められた語 {sorted(_ALLOWED_UPDATE_LOG_TYPES)} ではない"
            )
    for unlogged_adr_id in sorted(set(listed_status_by_adr_id) - logged_adr_ids):
        found_problems.append(f"INDEX.md の更新の記録: {unlogged_adr_id} の行が1つもない")
    return found_problems


def _find_adr_dirs_touched_by_tool(hook_input: dict[str, Any]) -> tuple[str, list[Path]] | None:
    """
    目的: フックとして呼ばれたときに、直前のツールの操作が ADR に触れたかを判断し、検査する先を決める。
    ADR と関係のない編集やコマンドのたびに検査して、Claude の作業を遅らせないためにある。

    戻り値は、きっかけ（"edit" か "bash"）と、検査する ADR のディレクトリ。
    ADR に触れていなければ、None を返す。
    """
    used_tool_name: str | None = hook_input.get("tool_name")
    used_tool_input: dict[str, Any] = hook_input.get("tool_input") or {}
    hook_cwd: Path = Path(hook_input.get("cwd") or os.getcwd())

    if used_tool_name in ("Edit", "Write", "MultiEdit"):
        edited_file_path_text: str | None = used_tool_input.get("file_path")
        if not edited_file_path_text:
            return None
        edited_file_path: Path = Path(edited_file_path_text)
        if not edited_file_path.is_absolute():
            edited_file_path = hook_cwd / edited_file_path
        # 書き換えたファイルの、すぐ上のディレクトリだけを見る。
        touched_adr_dirs: list[Path] = find_adr_dirs(edited_file_path.resolve().parent, max_search_depth=0)
        return ("edit", touched_adr_dirs) if touched_adr_dirs else None

    if used_tool_name == "Bash":
        bash_command_text: str = used_tool_input.get("command") or ""
        cwd_adr_dirs: list[Path] = find_adr_dirs(hook_cwd, max_search_depth=0)
        if cwd_adr_dirs:
            return ("bash", cwd_adr_dirs)
        if not _ADR_HINT_IN_BASH_COMMAND_PATTERN.search(bash_command_text):
            return None
        # コマンドの文字列からは、どの ADR のディレクトリかを確実には読み取れないので、プロジェクトの中をすべて見る。
        project_dir: Path = Path(os.environ.get("CLAUDE_PROJECT_DIR") or hook_cwd)
        project_adr_dirs: list[Path] = find_adr_dirs(project_dir, _MAX_ADR_DIR_SEARCH_DEPTH)
        return ("bash", project_adr_dirs) if project_adr_dirs else None
    return None


def _run_as_hook() -> int:
    """
    目的: PostToolUse フックとして、Claude が ADR を書き換えた直後に書式の誤りを Claude に知らせ、
    その場で直させる。

    ファイルを書き換えたときは、"decision": "block" で、直すよう強く伝える。
    Bash のときは、何を書き換えたかが確かでないので、additionalContext で情報として添えるだけにする。
    フックの失敗で Claude の作業を止めないよう、どの場合も 0 を返す。
    """
    try:
        hook_input: dict[str, Any] = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    hook_targets: tuple[str, list[Path]] | None = _find_adr_dirs_touched_by_tool(hook_input)
    if hook_targets is None:
        return 0
    hook_trigger_kind, target_adr_dirs = hook_targets

    found_problems_with_dir: list[str] = []
    for target_adr_dir in target_adr_dirs:
        found_problems_with_dir.extend(
            f"{target_adr_dir}: {found_problem}" for found_problem in _lint_adr_dir(target_adr_dir)
        )
    if not found_problems_with_dir:
        return 0

    reported_problems: list[str] = found_problems_with_dir[:_MAX_REPORTED_PROBLEMS_IN_HOOK]
    unreported_problem_cnt: int = len(found_problems_with_dir) - len(reported_problems)
    hook_message_lines: list[str] = (
        [f"ADR の書式の検査（{Path(__file__).name}）で、次の問題が見つかりました。"]
        + [f"- {reported_problem}" for reported_problem in reported_problems]
        + ([f"- ほかに {unreported_problem_cnt} 件"] if unreported_problem_cnt > 0 else [])
        + [
            "直してください。書いている途中で、このあと直す予定であれば、そのまま続けてください。",
            "ユーザーや別のセッションが書いた箇所であれば、勝手に直さず、ユーザーに伝えてください。",
        ]
    )
    hook_message: str = "\n".join(hook_message_lines)
    hook_output: dict[str, Any]
    if hook_trigger_kind == "edit":
        hook_output = {"decision": "block", "reason": hook_message}
    else:
        hook_output = {
            "hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": hook_message}
        }
    print(json.dumps(hook_output, ensure_ascii=False))
    return 0


def _run_from_command_line(search_root_texts: list[str]) -> int:
    """
    目的: フックが動かない環境で、Claude やユーザーが、ADR の書式を手で検査できるようにする。

    引数の各ディレクトリの下にある ADR のディレクトリを探し、ディレクトリごとに結果を表示する。
    終了コードは、問題がなければ 0、問題があれば 1、ADR のディレクトリが1つも見つからなければ 2。
    """
    target_adr_dirs: list[Path] = []
    for search_root_text in search_root_texts:
        search_root_dir: Path = Path(search_root_text).expanduser().resolve()
        if not search_root_dir.is_dir():
            print(f"{search_root_dir} は、ディレクトリではありません。")
            continue
        found_adr_dirs: list[Path] = find_adr_dirs(search_root_dir, _MAX_ADR_DIR_SEARCH_DEPTH)
        if not found_adr_dirs:
            print(f"{search_root_dir} の下に、ADR のディレクトリ（{ADR_FILE_GLOB} を持つディレクトリ）がありません。")
        target_adr_dirs.extend(found_adr_dirs)
    if not target_adr_dirs:
        return 2

    some_adr_dir_has_problems: bool = False
    for target_adr_dir in target_adr_dirs:
        found_problems: list[str] = _lint_adr_dir(target_adr_dir)
        if not found_problems:
            print(f"ADR の書式の検査（{target_adr_dir}）: 問題は見つかりませんでした。")
            continue
        some_adr_dir_has_problems = True
        print(f"ADR の書式の検査（{target_adr_dir}）: 次の問題が見つかりました。")
        for found_problem in found_problems:
            print(f"- {found_problem}")
    return 1 if some_adr_dir_has_problems else 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(_run_from_command_line(sys.argv[1:]))
    try:
        sys.exit(_run_as_hook())
    except Exception:
        # フックの失敗で、Claude の作業を止めない。
        sys.exit(0)
