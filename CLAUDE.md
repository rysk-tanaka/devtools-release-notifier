# devtools-release-notifier セットアップ指示書

このドキュメントは、Claude Codeがプロジェクトを自動的にセットアップするための指示書です。

## 📋 プロジェクト概要

開発ツール（Zed Editor、Dia Browser等）のリリース情報を自動取得し、GitHub Actionsでanthropics/claude-code-action@betaを使って日本語に翻訳してDiscordに通知するシステム。

## 📝 Markdown書式ガイドライン

このプロジェクトのすべてのMarkdownファイルは、以下のガイドラインに従ってください。

- 箇条書き前のコロン（:）は使用しない（例: 「以下の項目:」→「以下の項目。」）
- 太字（**）は使用しない
- シンプルで読みやすい表記を優先
- ファイル末尾に必ず改行を追加

## 🎯 実装要件

### アーキテクチャ

- Homebrew APIをベースに複数ツールを統一的に監視
- GitHub Releases/Commits をフォールバックとして使用
- 優先度ベースのソース選択機構
- 重要: GitHub Actionsのanthropics/claude-code-action@betaで翻訳（Pythonコードに翻訳機能なし）
- Discord Webhookによる通知配信
- ファイルベースのバージョンキャッシュ

### 技術スタック

- Python 3.14+
- uv (パッケージマネージャー)
- PyYAML (設定ファイル)
- httpx (HTTP通信 - 非同期対応可能)
- feedparser (RSS/Atom解析)
- pydantic (型検証)
- GitHub Actions (anthropics/claude-code-action@beta)

## 📁 ファイル構造

以下のファイル構造を作成してください：

```text
devtools-release-notifier/
├── pyproject.toml                     # 既存（依存関係を追加）
├── config.yml                         # 新規作成
├── cache/                             # 新規作成
│   └── .gitkeep
├── devtools_release_notifier/         # 新規作成（Pythonパッケージ）
│   ├── __init__.py
│   ├── notifier.py                    # メインスクリプト（翻訳機能なし）
│   ├── sources.py                     # 情報源クラス
│   └── discord_notifier.py            # Discord通知クラス
├── .github/
│   ├── workflows/
│   │   └── notifier.yml               # GitHub Actions設定
│   └── scripts/
│       └── send_to_discord.py         # 翻訳結果をDiscordに送信
└── .gitignore                         # 更新
```

## 🔧 実装手順

### ステップ1: pyproject.toml の更新

既存の `pyproject.toml` に以下の依存関係を追加してください：

```toml
[project]
name = "devtools-release-notifier"
version = "0.1.0"
description = "Automated release notifier for development tools with Japanese translation"
readme = "README.md"
requires-python = ">=3.14"
dependencies = [
    "httpx>=0.28.1",
    "pydantic>=2.12.4",
    "pydantic-settings>=2.11.0",
    "pyyaml>=6.0.1",
    "feedparser>=6.0.11",
]

[dependency-groups]
dev = [
    "mypy>=1.18.2",
    "pre-commit>=4.3.0",
    "pytest>=8.4.2",
    "respx>=0.22.0",
    "ruff>=0.14.3",
]

[project.scripts]
devtools-notifier = "devtools_release_notifier.notifier:main"
```

### ステップ2: config.yml の作成

プロジェクトルートに `config.yml` を作成し、以下の内容を記述してください。

重要な設定値

- Zed Editor: GitHub Releases（優先度1）、Homebrew Cask（優先度2）
- Dia Browser: Homebrew Cask（優先度1）、GitHub Commits（優先度2）
- キャッシュディレクトリ: ./cache
- 重要: 翻訳設定は削除（GitHub Actionsで行うため）

YAML構造

- `tools`: ツールのリスト
  - `name`: ツール名
  - `enabled`: 有効/無効
  - `sources`: 情報源のリスト（priority順）
    - `type`: "github_releases" | "homebrew_cask" | "github_commits"
    - `priority`: 優先度（1が最優先）
    - その他必要なパラメータ（owner, repo, atom_url, api_url等）
  - `notification`: Discord通知設定（webhook_env, color）
- `common`: 共通設定
  - `check_interval_hours`: 6
  - `cache_directory`: "./cache"

### ステップ3: Pythonパッケージの作成

#### 3-1. ディレクトリ構造

```bash
mkdir -p devtools_release_notifier
mkdir -p cache
touch cache/.gitkeep
mkdir -p .github/scripts
```

#### 3-2. devtools_release_notifier/__init__.py

シンプルなパッケージ初期化ファイルを作成してください。

- `__version__ = "0.1.0"` を定義

#### 3-3. devtools_release_notifier/sources.py

以下のクラスを実装してください。

重要: httpxを使用

- `import httpx` を使用
- HTTPリクエストは `httpx.get()` を使用
- エラーハンドリングは `httpx.HTTPError` を使用
- タイムアウトは `timeout=10.0` のように指定

ReleaseSource (抽象基底クラス)

- `__init__(config: Dict)`: 設定を受け取る
- `fetch_latest_version() -> Optional[Dict]`: 抽象メソッド

GitHubReleaseSource

- Atomフィード（`config['atom_url']`）を解析
- feedparserを使用してエントリーを取得
- 最新エントリーから以下を返す:

  ```python
  {
      'version': str,      # タイトル
      'content': str,      # summary
      'url': str,          # リンク
      'published': datetime,
      'source': 'github_releases'
  }
  ```

HomebrewCaskSource

- Homebrew JSON API（`config['api_url']`）から情報取得
- httpxを使用してGET: `httpx.get(api_url, timeout=10.0)`
- レスポンスは `response.raise_for_status()` でステータスチェック
- 以下の情報を抽出して返す:

  ```python
  {
      'version': str,         # data['version']
      'content': str,         # 生成したインストール情報
      'url': str,             # data['homepage']
      'download_url': str,    # data['url']
      'published': datetime.now(),
      'source': 'homebrew_cask'
  }
  ```

- エラーハンドリング: `except httpx.HTTPError as e`

GitHubCommitsSource

- Atomフィード（`config['atom_url']`）を解析
- GitHubReleaseSourceと同様の構造だが、source名が'github_commits'

#### 3-4. devtools_release_notifier/discord_notifier.py

DiscordNotifier クラス

- `send(webhook_url: str, tool_name: str, content: str, url: str, color: int) -> bool`
- httpxを使用: `httpx.post(webhook_url, json=payload, timeout=10.0)`
- Discord Webhook形式でPOST:

  ```python
  {
      "embeds": [{
          "title": f"🚀 {tool_name} - 新しいバージョン",
          "description": content[:4000],  # Discord制限
          "url": url,
          "color": color,
          "timestamp": datetime.utcnow().isoformat(),
          "footer": {"text": "devtools-release-notifier"}
      }]
  }
  ```

- レスポンス処理: `response.raise_for_status()` でステータスチェック
- エラーハンドリング: `except httpx.HTTPError as e`

#### 3-5. devtools_release_notifier/notifier.py（メインスクリプト）

重要: 翻訳機能は実装しない

UnifiedReleaseNotifier クラス

初期化 (`__init__`)

- config.ymlを読み込み（yamlモジュール使用）
- キャッシュディレクトリを作成
- DiscordNotifierを初期化
- 重要: Translatorは使用しない

ソース取得 (`get_source`)

- source_typeに応じて適切なSourceクラスを返す
- マッピング:
  - "github_releases" → GitHubReleaseSource
  - "homebrew_cask" → HomebrewCaskSource
  - "github_commits" → GitHubCommitsSource

キャッシュ管理

- `get_cache_path(tool_name: str) -> Path`: ツール名からキャッシュファイルパスを生成
  - 例: "Zed Editor" → "cache/zed_editor_version.json"
- `load_cached_version(tool_name: str) -> Optional[Dict]`: JSONファイルから読み込み
- `save_cached_version(tool_name: str, version_info: Dict)`: JSONファイルに保存
  - datetimeオブジェクトは`.isoformat()`で文字列化

ツール処理 (`process_tool`)

1. 有効性チェック（`enabled: false`ならスキップ）
2. sourcesを優先度順にソート
3. 優先度順にソースを試行し、最初に成功したソースから情報取得
4. キャッシュと比較（`cached['version'] == latest_info['version']`）
5. 新しいバージョンなら:
   - 重要: 翻訳は行わない
   - `--output`オプションが指定されていれば、リリース情報を収集
   - `--no-notify`が指定されていなければDiscord通知
   - キャッシュ更新

実行 (`run`)

- 全ツールに対してprocess_toolを実行
- 開始・終了メッセージを表示（絵文字使用）
- 処理状況のログ出力
- `--output`オプションが指定されている場合、新しいリリース情報をJSONファイルに出力

コマンドラインオプション

```python
import argparse

parser = argparse.ArgumentParser(description='Development tools release notifier')
parser.add_argument('--output', type=str, help='Output new releases to JSON file')
parser.add_argument('--no-notify', action='store_true', help='Skip Discord notification')
args = parser.parse_args()
```

出力JSON形式 (--output)

```json
[
  {
    "tool_name": "Zed Editor",
    "version": "v0.100.0",
    "content": "Release notes...",
    "url": "https://github.com/zed-industries/zed/releases/tag/v0.100.0",
    "color": 5814783,
    "webhook_env": "DISCORD_WEBHOOK"
  }
]
```

エントリーポイント (`main`)

- config.ymlの存在確認
- コマンドライン引数をパース
- UnifiedReleaseNotifierを初期化して実行
- エラーハンドリング:
  - `KeyboardInterrupt`: ユーザー中断メッセージ
  - `Exception`: エラーメッセージとトレースバック表示

### ステップ4: GitHub Actions の設定

`.github/workflows/notifier.yml` を作成してください。

トリガー

- schedule: 1日1回 10:00 UTC (cron: '0 10 ** *')
- workflow_dispatch: 手動実行

ジョブフロー

1. リポジトリのチェックアウト（actions/checkout@v4）
2. uvのインストール（astral-sh/setup-uv@v3）
3. Pythonのインストール（uv python install）
4. 依存関係のインストール（uv sync）
5. 新しいリリースを取得（uv run devtools-notifier --output releases.json --no-notify）
6. 新しいリリースがあるかチェック（test -f releases.json）
7. anthropics/claude-code-action@betaで翻訳
8. 翻訳結果をDiscordに送信（.github/scripts/send_to_discord.py）
9. キャッシュファイルのコミット・プッシュ
   - git config設定
   - cache/*.json をadd
   - コミット（変更がある場合のみ）
   - continue-on-error: true

ワークフロー例

```yaml
name: Check Development Tools Releases

on:
  schedule:
    - cron: '0 10 * * *'  # 毎日10:00 UTC
  workflow_dispatch:      # 手動実行

jobs:
  check-releases:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup uv
        uses: astral-sh/setup-uv@v3

      - name: Install Python
        run: uv python install

      - name: Install dependencies
        run: uv sync

      - name: Check for new releases
        id: check
        run: |
          uv run devtools-notifier --output releases.json --no-notify
          if [ -f releases.json ]; then
            echo "has_releases=true" >> $GITHUB_OUTPUT
            echo "releases_data<<EOF" >> $GITHUB_OUTPUT
            cat releases.json >> $GITHUB_OUTPUT
            echo "EOF" >> $GITHUB_OUTPUT
          else
            echo "has_releases=false" >> $GITHUB_OUTPUT
          fi

      - name: Translate with Claude
        if: steps.check.outputs.has_releases == 'true'
        id: translate
        uses: anthropics/claude-code-action@beta
        with:
          prompt: |
            以下は開発ツールのリリース情報です。各ツールについて日本語で要約してください。

            ${{ steps.check.outputs.releases_data }}

            各ツールについて、以下の形式でJSON配列として出力してください：
            [
              {
                "tool_name": "Zed Editor",
                "translated_content": "## 📌 主な変更点\n- 変更1\n- 変更2\n- 変更3"
              }
            ]

            要約は3-5個の主な変更点を簡潔に記載してください。
          auth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}

      - name: Send to Discord
        if: steps.check.outputs.has_releases == 'true'
        env:
          DISCORD_WEBHOOK: ${{ secrets.DISCORD_WEBHOOK }}
        run: |
          uv run python .github/scripts/send_to_discord.py \
            releases.json \
            '${{ steps.translate.outputs.response }}'

      - name: Commit cache updates
        if: steps.check.outputs.has_releases == 'true'
        continue-on-error: true
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add cache/*.json
          git diff --staged --quiet || git commit -m "chore: update release cache [skip ci]"
          git push
```

### ステップ5: .github/scripts/send_to_discord.py の作成

Discord Webhookに翻訳結果を送信するスクリプトを作成してください。

仕様

- 第1引数: releases.json のパス
- 第2引数: claude-code-actionの翻訳結果（JSON文字列）
- 翻訳結果とリリース情報をマッチング（tool_nameで）
- 各ツールについてDiscord Webhookに送信（httpx使用）

実装

```python
#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime
import httpx


def send_to_discord(webhook_url: str, tool_name: str, version: str,
                    translated_content: str, url: str, color: int) -> bool:
    """Discord Webhookに送信"""
    payload = {
        "embeds": [{
            "title": f"🚀 {tool_name} - {version}",
            "description": translated_content[:4000],
            "url": url,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "devtools-release-notifier"}
        }]
    }

    try:
        response = httpx.post(webhook_url, json=payload, timeout=10.0)
        response.raise_for_status()
        print(f"✓ Sent notification for {tool_name}")
        return True
    except httpx.HTTPError as e:
        print(f"✗ Failed to send notification for {tool_name}: {e}")
        return False


def main():
    if len(sys.argv) != 3:
        print("Usage: send_to_discord.py <releases.json> <translated_json>")
        sys.exit(1)

    releases_file = sys.argv[1]
    translated_json = sys.argv[2]

    # Load releases data
    with open(releases_file, 'r') as f:
        releases = json.load(f)

    # Parse translated data
    try:
        translated = json.loads(translated_json)
    except json.JSONDecodeError:
        print("Error: Invalid JSON in translated data")
        sys.exit(1)

    # Create mapping
    translated_map = {item['tool_name']: item['translated_content']
                      for item in translated}

    # Send to Discord
    for release in releases:
        tool_name = release['tool_name']
        webhook_env = release.get('webhook_env', 'DISCORD_WEBHOOK')
        webhook_url = os.getenv(webhook_env)

        if not webhook_url:
            print(f"⚠️  Webhook URL not found for {tool_name} ({webhook_env})")
            continue

        translated_content = translated_map.get(tool_name, release['content'])

        send_to_discord(
            webhook_url=webhook_url,
            tool_name=tool_name,
            version=release['version'],
            translated_content=translated_content,
            url=release['url'],
            color=release['color']
        )


if __name__ == '__main__':
    main()
```

### ステップ6: .gitignore の更新

既存の `.gitignore` に以下を追加してください：

```gitignore
# Cache files
cache/*.json
!cache/.gitkeep

# Environment variables
.env
.env.local

# Release output
releases.json
```

## 🎨 実装の詳細仕様

### HTTPクライアント（httpx）の使用方法

- 同期リクエスト: `httpx.get()`, `httpx.post()`を直接使用
- タイムアウト: 常に`timeout=10.0`または`timeout=30.0`を指定
- ステータスチェック: `response.raise_for_status()`を呼び出し
- エラーハンドリング: `httpx.HTTPError`をキャッチ
- JSON解析: `response.json()`でJSONデータ取得

### エラーハンドリング

- 各ソースでの取得失敗は警告を表示して次のソースへ
- 全ソースで失敗した場合は警告を表示して次のツールへ
- Discord通知失敗時は警告を表示
- HTTPエラーは`httpx.HTTPError`でキャッチ

### ログ出力

- 絵文字を使用した視覚的なログ
  - 🔍 Processing...
  - ✓ Success
  - ✗ Error
  - ⚠️ Warning
  - ⏭️ Skipped
  - ℹ️ Info
  - 🎉 New version
  - 🚀 Starting
  - ✅ Completed
- ツールごとに処理状況を明示
- インデントを使用して階層構造を表現

### 型ヒント

- すべての関数に型ヒントを追加
- `Optional[Dict]`, `List[Dict]`等を適切に使用
- `from typing import`でインポート

### コーディングスタイル

- docstringを各クラス・メソッドに追加（簡潔に）
- PEP 8に準拠
- 適切な例外処理
- 定数は大文字（例: `API_URL`, `DEFAULT_TIMEOUT`）

### Python開発規約

以下の規約に従って開発を行ってください。

#### コマンド実行

- uv runの使用: Pythonコマンド（pytest、ruff、mypyなど）の実行には必ず`uv run`を使用
  - 理由: 仮想環境を自動管理し、実行エラーを防止
  - 例: `uv run pytest`（`source .venv/bin/activate && pytest`ではなく）

#### 型ヒント

- 辞書型: 型パラメータなしの`dict`を使用（`Dict[str, Any]`ではなく）
  - 理由: 辞書は柔軟な汎用データ構造として使用されることが多い
- すべての関数に型ヒントを追加
- `Optional[Dict]`, `List[Dict]`等を適切に使用

#### ファイル構成

- __init__.py: デフォルトで空（末尾の改行のみ）
  - 理由: 現代のPythonでは明示的なエクスポートは不要
- ファイル末尾: 必ず改行を追加
  - 理由: POSIX標準への準拠、diffの見やすさ向上

#### エラーハンドリング

- サービス層: カスタムエラーメッセージで例外を再ラップしない
  - 例外はそのまま伝播（`except Exception: raise`）
  - コンテキスト情報はhandler層でログ出力
  - 理由: エラーメッセージの重複を避け、スタックトレースを保持
- HTTPエラーは`httpx.HTTPError`でキャッチ

#### テスト（pytest）

- テストスタイル: 関数ベースのテストを推奨
- 環境変数モック: `monkeypatch`フィクスチャを使用
  - `monkeypatch.setenv(key, value)`: 設定
  - `monkeypatch.delenv(key, raising=False)`: 削除
- マジックナンバー: 数値は意味のある定数として定義（ruff PLR2004）
- 副作用の回避: 実際のAPIリクエストやファイル操作を避け、モックを使用（respx使用）
- モジュール再読み込み: 環境変数やグローバル状態を変更した場合は`importlib.reload()`を使用

## ✅ 実装完了の確認項目

以下をすべて実装してください：

- [ ] pyproject.tomlに依存関係を追加（httpx含む）
- [ ] config.ymlを作成（Zed、Diaの2ツール設定、翻訳設定なし）
- [ ] cache/ディレクトリと.gitkeepを作成
- [ ] devtools_release_notifier/__init__.pyを作成
- [ ] devtools_release_notifier/sources.pyを作成（3つのSourceクラス、httpx使用）
- [ ] devtools_release_notifier/discord_notifier.pyを作成（httpx使用）
- [ ] devtools_release_notifier/notifier.pyを作成（翻訳機能なし、--output/--no-notifyオプション追加）
- [ ] .github/workflows/notifier.ymlを作成（anthropics/claude-code-action@beta使用）
- [ ] .github/scripts/send_to_discord.pyを作成
- [ ] .gitignoreを更新

## 🚀 実装後の動作確認

実装完了後、以下のコマンドで動作確認してください：

```bash
# 依存関係のインストール
uv sync

# 実行（翻訳なし、通知なし）
uv run devtools-notifier --output releases.json --no-notify

# releases.jsonの内容を確認
cat releases.json

# 実行（通知あり）
export DISCORD_WEBHOOK="https://discord.com/api/webhooks/..."
uv run devtools-notifier
```

## 📚 参考情報

### API仕様

- Homebrew JSON API: `https://formulae.brew.sh/api/cask/{cask_name}.json`
- GitHub Releases Atom: `https://github.com/{owner}/{repo}/releases.atom`
- Discord Webhook: POST with embed object
- anthropics/claude-code-action@beta: GitHub Actions用のClaude Code統合

### 色コード

- Zed Editor: 5814783 (ブルー系)
- Dia Browser: 3447003 (パープル系)

### HTTPクライアント選択理由

- httpxはrequestsの後継として設計
- 非同期対応（将来の拡張性）
- HTTP/2サポート
- より良いタイムアウト管理

---

## 📝 Claude Code への指示

このドキュメントを読んで、以下を実行してください：

1. 上記のファイル構造をすべて作成
2. 各ファイルに仕様通りのコードを実装
3. 重要: HTTP通信には必ずhttpxを使用（requestsは使わない）
4. 重要: translator.pyは作成しない（翻訳はGitHub Actionsで行う）
5. 重要: notifier.pyに--outputと--no-notifyオプションを実装
6. 重要: .github/scripts/send_to_discord.pyを作成
7. 型ヒント、docstring、エラーハンドリングを適切に実装
8. PEP 8に準拠したコードを記述

実装時の注意点

- 既存のpyproject.tomlは上書きせず、依存関係のみ追加
- config.ymlには実際に使用可能な設定値を記述（翻訳設定は含めない）
- すべてのHTTPリクエストにタイムアウトを指定
- エラー時は警告を表示して処理を継続（致命的エラー以外）
- httpx.HTTPErrorを使用してHTTPエラーをキャッチ
- GitHub Actionsでanthropics/claude-code-action@betaを使用して翻訳を行う
