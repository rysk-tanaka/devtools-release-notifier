# devtools-release-notifier

開発ツールのリリース情報を自動取得し、GitHub Actionsで日本語に翻訳してDiscordに通知する汎用システムです。

## 概要

このプロジェクトは、開発者が使用するツールの最新リリース情報を自動的に監視し、Discordチャンネルに日本語で通知します。複数の情報源から情報を取得し、優先度に基づいて最適なソースを選択する仕組みを持っています。

設定ファイル（`config.yml`）でツールを追加するだけで、任意の開発ツールを監視できます。

## 主な機能

- 複数情報源の統合監視
  - Homebrew API（優先）
  - GitHub Releases
  - GitHub Commits
  - 優先度ベースの自動フォールバック

- AI翻訳による高品質な日本語化
  - GitHub ActionsでClaude Code Actionを使用
  - リリース内容の要約（3-5個の主な変更点）
  - 技術用語の適切な翻訳

- Discord通知の自動配信
  - リッチな埋め込みメッセージ形式
  - ツールごとのカスタムカラー
  - バージョン情報と変更点の明示

- 効率的なキャッシュ管理
  - ファイルベースのバージョンキャッシュ
  - 重複通知の防止
  - GitHub Actionsとの統合

## 技術スタック

- Python 3.14+: 最新のPython機能を活用
- uv: 高速なパッケージマネージャー
- httpx: 次世代HTTPクライアント（非同期対応）
- PyYAML: 柔軟な設定ファイル管理
- feedparser: RSS/Atomフィード解析
- pydantic: 型安全なデータ検証
- GitHub Actions: CI/CDとClaude Code Actionによる翻訳
- Discord Webhook: 通知配信

## プロジェクト構造

```text
devtools-release-notifier/
├── devtools_release_notifier/    # メインパッケージ
│   ├── __init__.py              # パッケージ初期化
│   ├── notifier.py              # メインスクリプト
│   ├── sources/                 # 情報源クラス
│   ├── notifiers/               # 通知クラス
│   ├── models/                  # Pydanticモデル
│   └── scripts/                 # GitHub Actions統合スクリプト
│       ├── __init__.py
│       ├── extract_claude_response.py  # Claude応答抽出
│       └── send_to_discord.py         # Discord送信とMarkdownログ保存
├── tests/                       # テストコード
│   ├── scripts/                 # スクリプトの単体テスト
│   ├── models/                  # モデルの単体テスト
│   └── ...                      # その他のテスト
├── cache/                       # バージョンキャッシュ
├── docs/                        # 設計ドキュメント（ソース）
│   ├── README.md               # プロジェクト概要
│   └── architecture/           # アーキテクチャドキュメント
│       ├── index.md           # システムアーキテクチャ
│       ├── data-flow.md       # データフロー
│       ├── class-diagram.md   # クラス図
│       └── sequence-diagram.md # シーケンス図
├── rspress/                     # ドキュメントサイト
│   ├── docs/
│   │   ├── index.md            # トップページ（リリース情報メイン）
│   │   ├── architecture/       # 設計ドキュメント（docs/から同期）
│   │   └── releases/           # リリースログ（自動生成）
│   ├── scripts/
│   │   └── sync-docs.sh        # docs/ から rspress/docs/ への同期
│   ├── rspress.config.ts
│   └── package.json
├── .github/
│   └── workflows/
│       ├── notifier.yml         # リリース通知ワークフロー
│       └── deploy-docs.yml      # ドキュメントデプロイ
├── config.yml                   # 設定ファイル
├── pyproject.toml              # プロジェクト定義
└── README.md                   # このファイル
```

## セットアップ

### 前提条件

- Python 3.14以上
- uvパッケージマネージャー（推奨）
- Discord Webhook URL
- Claude Code OAuthトークン（GitHub Actionsで翻訳機能を使う場合のみ必要）

### インストール手順

1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/devtools-release-notifier.git
cd devtools-release-notifier
```

2. 依存関係のインストール

```bash
# uvを使用（推奨）
uv sync

# または、pipを使用
pip install -e .
```

3. 環境変数の設定

以下の環境変数を設定してください：

```bash
# Discord Webhook URL（必須）
export DISCORD_WEBHOOK="https://discord.com/api/webhooks/your-webhook-url"

# Claude API OAuth Token（オプション、翻訳機能を使う場合）
export CLAUDE_CODE_OAUTH_TOKEN="your-claude-oauth-token"
```

または、`.env`ファイルを作成して設定することもできます。

4. 設定ファイルの確認

`config.yml`を確認し、必要に応じて監視するツールや設定を調整してください。

## 使い方

### ローカルでの実行

```bash
# 基本的な実行（Discord通知あり）
uv run devtools-notifier

# 新しいリリース情報をJSONファイルに出力（翻訳なし、通知なし）
uv run devtools-notifier --output releases.json --no-notify

# 通知なしで実行
uv run devtools-notifier --no-notify
```

オプション

- `--output FILE`: 新しいリリース情報をJSONファイルに出力
- `--no-notify`: Discord通知をスキップ

### GitHub Actionsでの自動実行

このプロジェクトは、GitHub Actionsを使用して自動的に実行されます：

- スケジュール実行: 毎日 10:00 UTC
- 手動実行: GitHub ActionsのUIから実行可能
- 翻訳: Claude Code Actionで自動翻訳

#### GitHub Secretsの設定

リポジトリの Settings → Secrets and variables → Actions で以下のSecretを設定してください：

- `DISCORD_WEBHOOK`: 通知先のDiscord Webhook URL（必須）
- `CLAUDE_CODE_OAUTH_TOKEN`: Claude Code OAuthトークン（GitHub Actionsのワークフローで`claude_code_oauth_token`パラメータとして使用）

## 設定

### config.yml

`config.yml`で監視するツールと情報源を設定します：

```yaml
tools:
  - name: "Zed Editor"
    enabled: true
    sources:
      - type: github_releases
        priority: 1
        owner: zed-industries
        repo: zed
        atom_url: "https://github.com/zed-industries/zed/releases.atom"
      - type: homebrew_cask
        priority: 2
        cask_name: zed
        api_url: "https://formulae.brew.sh/api/cask/zed.json"
    notification:
      webhook_env: DISCORD_WEBHOOK
      color: 5814783  # Blue

common:
  check_interval_hours: 6
  cache_directory: "./cache"
```

### 設定項目の説明

- tools: 監視するツールのリスト
  - name: ツール名
  - enabled: 監視の有効/無効
  - sources: 情報源のリスト（優先度順）
    - type: 情報源の種類（github_releases, homebrew_cask, github_commits）
    - priority: 優先度（1が最優先）
  - notification: Discord通知設定
    - webhook_env: Webhook URLを格納する環境変数名（通常は"DISCORD_WEBHOOK"）
    - color: 埋め込みメッセージの色（10進数）

- common: 共通設定
  - check_interval_hours: チェック間隔（時間）
  - cache_directory: キャッシュディレクトリ

## アーキテクチャ

システムアーキテクチャの詳細については、[設計ドキュメント](docs/architecture/index.md)を参照してください。

主要なコンポーネント：

1. Sources（情報源）: 複数のAPIから情報を取得
2. GitHub Actions: Claude Code Actionで日本語に翻訳・要約
3. DiscordNotifier（通知）: Discord Webhookで通知配信とMarkdownログ保存
4. Cache（キャッシュ）: バージョン情報を永続化

ドキュメントサイト: [GitHub Pages](https://rysk-tanaka.github.io/devtools-release-notifier/) で閲覧可能

## 開発

### 開発環境のセットアップ

```bash
# 依存関係（開発ツール含む）のインストール
uv sync

# pre-commitフックのインストール
uv run pre-commit install
```

### コードフォーマット・リント

```bash
# ruffでフォーマット
uv run ruff format .

# ruffでリント
uv run ruff check .

# mypyで型チェック
uv run mypy devtools_release_notifier
```

### テスト

```bash
# すべてのテストを実行
uv run pytest

# カバレッジ付きで実行
uv run pytest --cov=devtools_release_notifier
```

### Python開発規約

このプロジェクトは以下の規約に従います：

- コマンド実行: `uv run`を使用
- 型ヒント: すべての関数に型ヒントを追加
- エラーハンドリング: 適切な例外処理とログ出力
- コードスタイル: PEP 8準拠、ruffでフォーマット

詳細は[CLAUDE.md](CLAUDE.md)を参照してください。

### 新しいツールの追加

新しい開発ツールの監視を追加する方法については、[貢献ガイド](docs/CONTRIBUTING.md)を参照してください。

簡単な手順。

1. `config.yml`にツール設定を追加
2. rspressドキュメントを更新（`_meta.json`、`index.md`、ツール専用ページ）
3. ローカルで動作確認（`uv run devtools-notifier --output releases.json --no-notify`）
4. プルリクエストを作成

詳細な手順、設定例、トラブルシューティングは[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)を参照してください。

## トラブルシューティング

### Discord通知が送信されない

- Discord Webhook URLが正しく設定されているか確認
- Webhook URLが有効か確認（Discord側で削除されていないか）
- ネットワーク接続を確認

### 翻訳が動作しない

- `CLAUDE_CODE_OAUTH_TOKEN`が設定されているか確認
- トークンが有効か確認
- 翻訳なしで通知だけ受け取る場合は、環境変数を設定しない

### キャッシュのリセット

```bash
# キャッシュファイルを削除
rm cache/*.json
```

## 関連リンク

- [設計ドキュメント](docs/architecture/index.md) - システムアーキテクチャの詳細
- [ドキュメントサイト](https://rysk-tanaka.github.io/devtools-release-notifier/) - リリース情報と設計ドキュメント
- [Claude API Documentation](https://docs.anthropic.com/en/api/)
- [Discord Webhook Documentation](https://discord.com/developers/docs/resources/webhook)
- [Homebrew API Documentation](https://formulae.brew.sh/)
