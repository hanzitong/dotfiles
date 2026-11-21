# hooks/

Claude Code のフックに使うスクリプトの置き場所です。
スクリプトの実体は `~/dotfiles/dotfiles/claude/hooks/` にあります。`setup_dotfiles.sh` が、`~/.claude/hooks/` に、1ファイルずつシンボリックリンクを作ります。

## いまの状態: 登録済みだが、動かない

2つのスクリプトを、`~/.claude/settings.json`（実体は dotfiles の `settings.json`）にフックとして登録しています。
ただし、社内の管理設定で `allowManagedHooksOnly` が true になっているため、動きません。
この設定があると、組織が配るフックだけが動き、ユーザーの設定に書いたフックは無視されます。
社内の管理設定で `allowManagedHooksOnly` が true でなくなると、登録したフックがそのまま動き出します。

| スクリプト | フックの種類 | 何をするか |
|---|---|---|
| `adr_session_context.py` | SessionStart | 開始時、`/clear` のあと、文脈の圧縮のあとに、プロジェクトの中の ADR のうち、状態が「採用」と「提案」のものの一覧を Claude に渡す |
| `adr_lint.py` | PostToolUse（Edit、Write、MultiEdit、Bash） | Claude が ADR や INDEX.md を書き換えたあとに、書式を検査し、見つけた問題を Claude に返す |

## ADR のディレクトリの見つけ方

2つのスクリプトは、ADR の置き場所を決め打ちしません。どのプロジェクトでも、同じスクリプトを使えます。

- ADR のディレクトリとは、`ADR-*.md` のファイルを直下に持つディレクトリのことです。
- 渡されたディレクトリ（フックではプロジェクトのディレクトリ）の下を、決まった深さまで探します。1つのプロジェクトに ADR のディレクトリが複数あれば（例: `coffee_system/ADR/` と `assembly_system/ADR/`）、すべてを扱います。
- 名前が「.」で始まるディレクトリと、`backup`、`backups`、`archive`、`node_modules`、`__pycache__`、`venv`、`site-packages` の中は探しません。
  - 理由: `backup` などには、古い書式のまま残した ADR の写しがあり、検査すると古い誤りを報告してしまうためです。
- `adr_lint.py` は、フックとして動くとき、Edit や Write で書き換えたファイルのすぐ上のディレクトリだけを検査します。Bash のときは、コマンドに ADR の番号（`ADR-0000`）か `INDEX.md` が出てきたら、プロジェクトの中のすべての ADR のディレクトリを検査します。

## いまの使い方: 手で実行する

```bash
# プロジェクトの中のすべての ADR のディレクトリを検査する
python3 ~/.claude/hooks/adr_lint.py <プロジェクトのディレクトリ>
# 1つの ADR のディレクトリだけを検査する
python3 ~/.claude/hooks/adr_lint.py <ADR のディレクトリ>
# 状態が「採用」と「提案」の ADR の一覧を表示する
python3 ~/.claude/hooks/adr_session_context.py <プロジェクトのディレクトリ>
```

`adr_lint.py` の終了コードは、問題がなければ 0、問題があれば 1、ADR のディレクトリが見つからなければ 2 です。

フックの代わりに、Claude が次のスキルに従って、同じスクリプトを実行します。

| スキル | 代わりをするフック | 実行するスクリプト |
|---|---|---|
| `adr-context` | SessionStart | `adr_session_context.py` |
| `adr-lint` | PostToolUse | `adr_lint.py` |

`adr_lint.py` の実行は、adr スキルの「書き終えたあとの確認」の節にも、`/adr-new` と `/adr-check` の手順にも入っています。
スキルは Claude が従うことに頼るので、フックほど確実ではありません。

## 検査の内容（adr_lint.py）

adr スキル（`~/.claude/skills/adr/SKILL.md`）の決まりに合わせています。スキルの決まりを変えたら、このスクリプトも直します。

- ADR のファイル名が、決まった形か
- 1行目の題名が、決まった形か
- 冒頭の行（ID、決定日、INDEX.md への案内）があるか
- 見出しの種類と順番（背景、選択肢、決定、理由、影響と残る課題。確かめ方は任意で、置くときは最後）が、決まりどおりか
- 選択肢が2つ以上あるか
- 採用した方法に「（採用）」が付いているか
  - 例外: 状態が「提案」の ADR では、adr_lint.py はこの点を検査しない。
- ADR のファイルに、状態の行がないか
- ADR のファイルに、「追記」「訂正」の印がないか
- 2026-10-16 以降の ADR に、冒頭の要約（1文）があるか
- 2026-10-16 以降の ADR に、理由の確信の度合い（高、中、低）があるか
- INDEX.md の一覧とファイルが、1対1で対応しているか
- INDEX.md の題名と決定日が、ファイルと一致しているか
- 状態、関係、更新の記録の種類に、決められた語を使っているか
- 「置き換え済み」の ADR に、置き換える側の ADR があるか
- 削除した番号のファイルが、残っていないか

## 参考

- フックの仕組み: https://code.claude.com/docs/en/hooks
- 設定の項目（`allowManagedHooksOnly` など）: https://code.claude.com/docs/en/settings
