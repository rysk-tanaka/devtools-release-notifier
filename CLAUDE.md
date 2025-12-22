# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

開発ツール（Zed Editor、Dia Browser、Claude Code、Raycast等）のリリース情報を自動取得し、GitHub Actionsでclaude-code-action@v1を使って日本語に翻訳してDiscordに通知するシステム。

## 開発コマンド

```bash
# 依存関係のインストール
uv sync

# リンター・フォーマッター
uv run ruff format .
uv run ruff check .

# 型チェック
uv run mypy .

# テスト
uv run pytest                    # 全テスト実行
uv run pytest -v                 # 詳細出力
uv run pytest tests/test_foo.py  # 特定ファイル実行
uv run pytest -k test_name       # 特定テスト実行

# 実行
uv run devtools-notifier --output releases.json --no-notify  # ローカルテスト（通知なし）
uv run devtools-notifier                                      # Discord通知あり
```

## アーキテクチャ

### コンポーネント構成

```text
config.yml → Sources → ReleaseInfo → DiscordNotifier → Discord
                                   → GitHub Actions(claude-code-action) → 翻訳 → Discord
                                   → Markdown logs(rspress)
```

1. Sources（`sources/`）: 複数APIから情報取得（優先度ベースでフォールバック）
   - `GitHubReleaseSource`: GitHub Releases Atomフィード
   - `HomebrewCaskSource`: Homebrew JSON API
   - `GitHubCommitsSource`: GitHub Commits Atomフィード
   - `ChangelogSource`: CHANGELOGファイル（Markdown）パース

2. Models（`models/`）: Pydanticによる型検証
   - `config.py`: 設定ファイル構造
   - `release.py`: リリース情報とキャッシュ
   - `output.py`: JSON出力形式
   - `discord.py`: Discord Webhook形式

3. Notifiers（`notifiers/`）: Discord通知

4. Scripts（`scripts/`）: GitHub Actions連携
   - `extract_claude_response.py`: claude-code-actionの実行ファイルからJSON抽出
   - `send_to_discord.py`: 翻訳結果の送信とMarkdownログ保存

### 処理フロー

GitHub Actionsワークフロー（`.github/workflows/notifier.yml`）:

1. `devtools-notifier --output releases.json --no-notify` で新リリース検出
2. claude-code-action@v1 で日本語翻訳
3. `extract_claude_response.py` で翻訳JSON抽出
4. `send_to_discord.py` でDiscord送信とMarkdown保存
5. キャッシュとログをコミット

## コーディング規約

### Python

- Python 3.14+
- 型ヒント必須（`dict`型パラメータなし、Union型は`X | Y`形式）
- HTTPクライアント: httpx（`timeout=10.0`必須、`httpx.HTTPError`でキャッチ）
- datetime: `datetime.now(UTC)`使用（`datetime.utcnow()`は非推奨）
- Discord timestamp: `datetime.now(UTC).isoformat().replace("+00:00", "Z")`
- `__init__.py`: 空ファイル（末尾改行のみ）

### テスト

- 関数ベースのテスト推奨
- 環境変数モック: `monkeypatch`フィクスチャ使用
- HTTPモック: `respx`使用
- マジックナンバー: 定数として定義（ruff PLR2004）

### Markdown

- 箇条書き前のコロン不使用（「以下の項目:」→「以下の項目。」）
- 太字不使用

## 新規ツール追加手順

1. `config.yml` にツール設定追加
2. `rspress/docs/releases/_meta.json` にナビゲーション追加（アルファベット順）
3. `rspress/docs/releases/{tool-slug}/index.md` 作成
4. ローカルテスト: `uv run devtools-notifier --output releases.json --no-notify`

### config.yml設定例

```yaml
- name: "{Tool Name}"
  enabled: true
  sources:
    - type: "github_releases"  # または homebrew_cask, github_commits, changelog
      priority: 1
      atom_url: "https://github.com/{owner}/{repo}/releases.atom"
      owner: "{owner}"
      repo: "{repo}"
  notification:
    webhook_env: "DISCORD_WEBHOOK"
    color: 5814783  # 10進数（0-16777215）
```

### changelog ソースタイプ

CHANGELOGファイルからバージョン情報を取得する。

```yaml
- type: "changelog"
  priority: 2
  raw_url: "https://raw.githubusercontent.com/{owner}/{repo}/main/CHANGELOG.md"
  version_pattern: "simple"  # または "keepachangelog"、カスタム正規表現
  content_url: "https://github.com/{owner}/{repo}/blob/main/CHANGELOG.md"
```

プリセットパターン。

- `simple`: `## 2.0.69` 形式（Claude Code等）
- `keepachangelog`: `## [1.0.0] - 2024-01-15` 形式（Keep a Changelog標準）

カスタム正規表現も指定可能（例: `^Version (\d+\.\d+\.\d+)`）

## GitHub Secrets

- `DISCORD_WEBHOOK`: Discord Webhook URL
- `CLAUDE_CODE_OAUTH_TOKEN`: Claude Code OAuthトークン（翻訳用）
