# devtools-release-notifier セットアップ指示書

このドキュメントは、Claude Codeがプロジェクトを自動的にセットアップするための指示書です。

## 📋 プロジェクト概要

開発ツール（Zed Editor、Dia Browser）のリリース情報を自動取得し、Claude APIで日本語に翻訳してDiscordに通知するシステム。

## 🎯 実装要件

### アーキテクチャ

- Homebrew APIをベースに複数ツールを統一的に監視
- GitHub Releases/Commits をフォールバックとして使用
- 優先度ベースのソース選択機構
- Claude APIによる高品質な日本語翻訳
- Discord Webhookによる通知配信
- ファイルベースのバージョンキャッシュ

### 技術スタック

- Python 3.14+
- uv (パッケージマネージャー)
- PyYAML (設定ファイル)
- httpx (HTTP通信 - 非同期対応可能)
- feedparser (RSS/Atom解析)
- pydantic (型検証)

## 📁 ファイル構造

以下のファイル構造を作成してください：

```
devtools-release-notifier/
├── pyproject.toml                     # 既存（依存関係を追加）
├── config.yml                         # 新規作成
├── cache/                             # 新規作成
│   └── .gitkeep
├── devtools_release_notifier/         # 新規作成（Pythonパッケージ）
│   ├── __init__.py
│   ├── notifier.py                    # メインスクリプト
│   ├── sources.py                     # 情報源クラス
│   ├── translator.py                  # 翻訳クラス
│   └── discord_notifier.py            # Discord通知クラス
├── .github/
│   └── workflows/
│       └── notifier.yml               # GitHub Actions設定
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

プロジェクトルートに `config.yml` を作成し、以下の内容を記述してください：

**重要な設定値:**

- Zed Editor: GitHub Releases（優先度1）、Homebrew Cask（優先度2）
- Dia Browser: Homebrew Cask（優先度1）、GitHub Commits（優先度2）
- 翻訳サービス: claude
- キャッシュディレクトリ: ./cache

**YAML構造:**

- `tools`: ツールのリスト
  - `name`: ツール名
  - `enabled`: 有効/無効
  - `sources`: 情報源のリスト（priority順）
    - `type`: "github_releases" | "homebrew_cask" | "github_commits"
    - `priority`: 優先度（1が最優先）
    - その他必要なパラメータ（owner, repo, atom_url, api_url等）
  - `translation`: 翻訳設定（target_lang: ja）
  - `notification`: Discord通知設定（webhook_env, color）
- `common`: 共通設定
  - `check_interval_hours`: 6
  - `cache_directory`: "./cache"
  - `translation_service`: "claude"

### ステップ3: Pythonパッケージの作成

#### 3-1. ディレクトリ構造

```bash
mkdir -p devtools_release_notifier
mkdir -p cache
touch cache/.gitkeep
```

#### 3-2. devtools_release_notifier/**init**.py

シンプルなパッケージ初期化ファイルを作成してください。

- `__version__ = "0.1.0"` を定義

#### 3-3. devtools_release_notifier/sources.py

以下のクラスを実装してください：

**重要: httpxを使用**

- `import httpx` を使用
- HTTPリクエストは `httpx.get()` を使用
- エラーハンドリングは `httpx.HTTPError` を使用
- タイムアウトは `timeout=10.0` のように指定

**ReleaseSource (抽象基底クラス)**

- `__init__(config: Dict)`: 設定を受け取る
- `fetch_latest_version() -> Optional[Dict]`: 抽象メソッド

**GitHubReleaseSource**

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

**HomebrewCaskSource**

- Homebrew JSON API（`config['api_url']`）から情報取得
- **httpxを使用してGET**: `httpx.get(api_url, timeout=10.0)`
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

**GitHubCommitsSource**

- Atomフィード（`config['atom_url']`）を解析
- GitHubReleaseSourceと同様の構造だが、source名が'github_commits'

#### 3-4. devtools_release_notifier/translator.py

**Translator クラス**

- `__init__(service: str, oauth_token: Optional[str])`
- `translate_and_summarize(tool_name: str, version: str, content: str) -> str`
  - serviceが"claude"かつoauth_tokenがある場合: Claude APIで翻訳
  - それ以外: そのまま返す

**Claude API統合（httpx使用）**

- `import httpx` を使用
- エンドポイント: `https://api.anthropic.com/v1/messages`
- モデル: `claude-sonnet-4-20250514`
- max_tokens: 2000
- **HTTPリクエスト**: `httpx.post(api_url, headers=headers, json=payload, timeout=30.0)`
- プロンプト: リリース情報を日本語で要約（3-5個の主な変更点を簡潔に）
- ヘッダー:
  - `Authorization: Bearer {oauth_token}`
  - `Content-Type: application/json`
  - `anthropic-version: 2023-06-01`
- レスポンス処理: `response.raise_for_status()` → `result = response.json()`
- エラーハンドリング: `except httpx.HTTPError as e`

#### 3-5. devtools_release_notifier/discord_notifier.py

**DiscordNotifier クラス**

- `send(webhook_url: str, tool_name: str, content: str, url: str, color: int) -> bool`
- **httpxを使用**: `httpx.post(webhook_url, json=payload, timeout=10.0)`
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

#### 3-6. devtools_release_notifier/notifier.py（メインスクリプト）

**UnifiedReleaseNotifier クラス**

**初期化 (`__init__`)**

- config.ymlを読み込み（yamlモジュール使用）
- キャッシュディレクトリを作成
- Translator、DiscordNotifierを初期化

**ソース取得 (`get_source`)**

- source_typeに応じて適切なSourceクラスを返す
- マッピング:
  - "github_releases" → GitHubReleaseSource
  - "homebrew_cask" → HomebrewCaskSource
  - "github_commits" → GitHubCommitsSource

**キャッシュ管理**

- `get_cache_path(tool_name: str) -> Path`: ツール名からキャッシュファイルパスを生成
  - 例: "Zed Editor" → "cache/zed_editor_version.json"
- `load_cached_version(tool_name: str) -> Optional[Dict]`: JSONファイルから読み込み
- `save_cached_version(tool_name: str, version_info: Dict)`: JSONファイルに保存
  - datetimeオブジェクトは`.isoformat()`で文字列化

**ツール処理 (`process_tool`)**

1. 有効性チェック（`enabled: false`ならスキップ）
2. sourcesを優先度順にソート
3. 優先度順にソースを試行し、最初に成功したソースから情報取得
4. キャッシュと比較（`cached['version'] == latest_info['version']`）
5. 新しいバージョンなら:
   - 翻訳・要約（Translatorを使用）
   - Discord通知（DiscordNotifierを使用、環境変数からWebhook URL取得）
   - キャッシュ更新

**実行 (`run`)**

- 全ツールに対してprocess_toolを実行
- 開始・終了メッセージを表示（絵文字使用）
- 処理状況のログ出力

**エントリーポイント (`main`)**

- config.ymlの存在確認
- UnifiedReleaseNotifierを初期化して実行
- エラーハンドリング:
  - `KeyboardInterrupt`: ユーザー中断メッセージ
  - `Exception`: エラーメッセージとトレースバック表示

### ステップ4: GitHub Actions の設定

`.github/workflows/notifier.yml` を作成してください。

**トリガー:**

- schedule: 月曜日 10:00 UTC (cron: '0 10 ** 1')
- workflow_dispatch: 手動実行

**ジョブ:**

1. リポジトリのチェックアウト（actions/checkout@v4）
2. uvのインストール（astral-sh/setup-uv@v3）
3. Pythonのインストール（uv python install）
4. 依存関係のインストール（uv sync）
5. 通知スクリプトの実行（uv run devtools-notifier）
   - 環境変数: DISCORD_WEBHOOK_ZED, DISCORD_WEBHOOK_DIA, CLAUDE_CODE_OAUTH_TOKEN
6. キャッシュファイルのコミット・プッシュ
   - git config設定
   - cache/*.json をadd
   - コミット（変更がある場合のみ）
   - continue-on-error: true

### ステップ5: .gitignore の更新

既存の `.gitignore` に以下を追加してください：

```gitignore
# Cache files
cache/*.json
!cache/.gitkeep

# Environment variables
.env
.env.local
```

## 🎨 実装の詳細仕様

### HTTPクライアント（httpx）の使用方法

- **同期リクエスト**: `httpx.get()`, `httpx.post()`を直接使用
- **タイムアウト**: 常に`timeout=10.0`または`timeout=30.0`を指定
- **ステータスチェック**: `response.raise_for_status()`を呼び出し
- **エラーハンドリング**: `httpx.HTTPError`をキャッチ
- **JSON解析**: `response.json()`でJSONデータ取得

### エラーハンドリング

- 各ソースでの取得失敗は警告を表示して次のソースへ
- 全ソースで失敗した場合は警告を表示して次のツールへ
- 翻訳失敗時はフォールバック（翻訳なし）
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
- `Optional[Dict]`, `Dict[str, Any]`, `List[Dict]`等を適切に使用
- `from typing import`でインポート

### コーディングスタイル

- docstringを各クラス・メソッドに追加（簡潔に）
- PEP 8に準拠
- 適切な例外処理
- 定数は大文字（例: `API_URL`, `DEFAULT_TIMEOUT`）

### Python開発規約

以下の規約に従って開発を行ってください。

#### コマンド実行

- **uv runの使用**: Pythonコマンド（pytest、ruff、mypyなど）の実行には必ず`uv run`を使用
  - 理由: 仮想環境を自動管理し、実行エラーを防止
  - 例: `uv run pytest`（`source .venv/bin/activate && pytest`ではなく）

#### 型ヒント

- **辞書型**: 型パラメータなしの`dict`を使用（`Dict[str, Any]`ではなく）
  - 理由: 辞書は柔軟な汎用データ構造として使用されることが多い
- すべての関数に型ヒントを追加
- `Optional[Dict]`, `List[Dict]`等を適切に使用

#### ファイル構成

- ****init**.py**: デフォルトで空（末尾の改行のみ）
  - 理由: 現代のPythonでは明示的なエクスポートは不要
- **ファイル末尾**: 必ず改行を追加
  - 理由: POSIX標準への準拠、diffの見やすさ向上

#### エラーハンドリング

- **サービス層**: カスタムエラーメッセージで例外を再ラップしない
  - 例外はそのまま伝播（`except Exception: raise`）
  - コンテキスト情報はhandler層でログ出力
  - 理由: エラーメッセージの重複を避け、スタックトレースを保持
- HTTPエラーは`httpx.HTTPError`でキャッチ

#### テスト（pytest）

- **テストスタイル**: 関数ベースのテストを推奨
- **環境変数モック**: `monkeypatch`フィクスチャを使用
  - `monkeypatch.setenv(key, value)`: 設定
  - `monkeypatch.delenv(key, raising=False)`: 削除
- **マジックナンバー**: 数値は意味のある定数として定義（ruff PLR2004）
- **副作用の回避**: 実際のAPIリクエストやファイル操作を避け、モックを使用（respx使用）
- **モジュール再読み込み**: 環境変数やグローバル状態を変更した場合は`importlib.reload()`を使用

## ✅ 実装完了の確認項目

以下をすべて実装してください：

- [ ] pyproject.tomlに依存関係を追加（httpx含む）
- [ ] config.ymlを作成（Zed、Diaの2ツール設定）
- [ ] cache/ディレクトリと.gitkeepを作成
- [ ] devtools_release_notifier/**init**.pyを作成
- [ ] devtools_release_notifier/sources.pyを作成（3つのSourceクラス、httpx使用）
- [ ] devtools_release_notifier/translator.pyを作成（httpx使用）
- [ ] devtools_release_notifier/discord_notifier.pyを作成（httpx使用）
- [ ] devtools_release_notifier/notifier.pyを作成（メインロジック）
- [ ] .github/workflows/notifier.ymlを作成
- [ ] .gitignoreを更新

## 🚀 実装後の動作確認

実装完了後、以下のコマンドで動作確認してください：

```bash
# 依存関係のインストール
uv sync

# 実行（環境変数は適宜設定）
export DISCORD_WEBHOOK_ZED="https://discord.com/api/webhooks/..."
export DISCORD_WEBHOOK_DIA="https://discord.com/api/webhooks/..."
export CLAUDE_CODE_OAUTH_TOKEN="your-token"

uv run devtools-notifier
```

## 📚 参考情報

### API仕様

- **Homebrew JSON API**: `https://formulae.brew.sh/api/cask/{cask_name}.json`
- **GitHub Releases Atom**: `https://github.com/{owner}/{repo}/releases.atom`
- **Claude API**: `https://api.anthropic.com/v1/messages`
- **Discord Webhook**: POST with embed object

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
3. **重要**: HTTP通信には必ずhttpxを使用（requestsは使わない）
4. 型ヒント、docstring、エラーハンドリングを適切に実装
5. PEP 8に準拠したコードを記述

実装時の注意点：

- 既存のpyproject.tomlは上書きせず、依存関係のみ追加
- config.ymlには実際に使用可能な設定値を記述
- すべてのHTTPリクエストにタイムアウトを指定
- エラー時は警告を表示して処理を継続（致命的エラー以外）
- httpx.HTTPErrorを使用してHTTPエラーをキャッチ
