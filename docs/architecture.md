# システムアーキテクチャ

devtools-release-notifierのシステムアーキテクチャ図です。

## 全体アーキテクチャ

```mermaid
graph TB
    subgraph "External Services"
        GHR[GitHub Releases<br/>Atom Feed]
        GHC[GitHub Commits<br/>Atom Feed]
        HB[Homebrew API<br/>JSON API]
        CLAUDE[Claude Code Action<br/>anthropics/claude-code-action@beta]
        DISCORD[Discord<br/>Webhook]
    end

    subgraph "GitHub Actions"
        SCHEDULE[Scheduled Trigger<br/>Every Day 10:00 UTC]
        MANUAL[Manual Trigger<br/>workflow_dispatch]
        RUNNER[GitHub Actions Runner]
        TRANSLATE[Translation Step<br/>claude-code-action]
        SEND_SCRIPT[send_to_discord.py<br/>Send Translated Content]
    end

    subgraph "Application Core"
        MAIN[UnifiedReleaseNotifier<br/>Main Orchestrator]
        CONFIG[config.yml<br/>Configuration]

        subgraph "Source Module"
            SRC_BASE[ReleaseSource<br/>Abstract Base]
            SRC_GHR[GitHubReleaseSource]
            SRC_GHC[GitHubCommitsSource]
            SRC_HB[HomebrewCaskSource]
        end

        subgraph "Notification Module"
            NOTIF[DiscordNotifier<br/>Message Sender]
        end

        subgraph "Cache Module"
            CACHE[Version Cache<br/>JSON Files]
        end
    end

    SCHEDULE --> RUNNER
    MANUAL --> RUNNER
    RUNNER --> MAIN

    CONFIG --> MAIN
    MAIN --> SRC_BASE
    SRC_BASE --> SRC_GHR
    SRC_BASE --> SRC_GHC
    SRC_BASE --> SRC_HB

    SRC_GHR --> GHR
    SRC_GHC --> GHC
    SRC_HB --> HB

    MAIN -->|releases.json| RUNNER
    RUNNER --> TRANSLATE
    TRANSLATE --> CLAUDE
    CLAUDE -->|translated content| SEND_SCRIPT
    SEND_SCRIPT --> DISCORD

    MAIN --> NOTIF
    NOTIF --> DISCORD

    MAIN --> CACHE
    CACHE --> RUNNER

    style MAIN fill:#4a90e2,color:#fff
    style CONFIG fill:#50c878,color:#fff
    style CACHE fill:#f39c12,color:#fff
    style CLAUDE fill:#8e44ad,color:#fff
    style DISCORD fill:#7289da,color:#fff
    style TRANSLATE fill:#8e44ad,color:#fff
    style SEND_SCRIPT fill:#7289da,color:#fff
```

## コンポーネント説明

### External Services

- **GitHub Releases/Commits**: Atomフィード形式でリリース情報を提供
- **Homebrew API**: JSON形式でパッケージ情報を提供
- **Claude Code Action**: anthropics/claude-code-action@betaによる翻訳・要約サービス
- **Discord Webhook**: 通知配信サービス

### GitHub Actions

- **Scheduled Trigger**: 毎日10:00 UTCに自動実行
- **Manual Trigger**: 手動実行用のトリガー
- **Runner**: ワークフロー実行環境
- **Translation Step**: claude-code-actionを使用した翻訳処理
- **send_to_discord.py**: 翻訳されたコンテンツをDiscordに送信するスクリプト

### Application Core

#### UnifiedReleaseNotifier

- システムの中核となるオーケストレーター
- 各ツールの処理を統括
- 優先度ベースのソース選択
- キャッシュ管理
- エラーハンドリング

#### Source Module

- **ReleaseSource**: 情報源の抽象基底クラス
- **GitHubReleaseSource**: GitHub Releasesから情報取得
- **GitHubCommitsSource**: GitHub Commitsから情報取得
- **HomebrewCaskSource**: Homebrew APIから情報取得

#### Notification Module

- **DiscordNotifier**: Discord Webhookへの通知送信
- リッチ埋め込みメッセージ形式

#### Cache Module

- **Version Cache**: JSONファイル形式でバージョン情報を永続化
- 重複通知の防止

## データストア

```mermaid
erDiagram
    CACHE_FILE {
        string version
        string content
        string url
        string published
        string source
    }
    CONFIG_FILE {
        array tools
        object common
    }

    CONFIG_FILE ||--o{ TOOL : contains
    TOOL {
        string name
        boolean enabled
        array sources
        object translation
        object notification
    }

    TOOL ||--o{ SOURCE : has
    SOURCE {
        string type
        int priority
        string atom_url
        string api_url
        string owner
        string repo
        string cask_name
    }
```

## デプロイメント構成

```mermaid
graph LR
    subgraph "GitHub"
        REPO[Repository<br/>Source Code]
        ACTIONS[GitHub Actions<br/>CI/CD]
        SECRETS[Secrets<br/>Environment Variables]
    end

    subgraph "Runtime"
        PYTHON[Python 3.14+<br/>Runtime]
        UV[uv<br/>Package Manager]
        APP[Application<br/>devtools-notifier]
    end

    subgraph "External APIs"
        API1[GitHub API]
        API2[Homebrew API]
        API3[Claude API]
        API4[Discord API]
    end

    REPO --> ACTIONS
    SECRETS --> ACTIONS
    ACTIONS --> PYTHON
    PYTHON --> UV
    UV --> APP

    APP --> API1
    APP --> API2
    APP --> API3
    APP --> API4

    style REPO fill:#24292e,color:#fff
    style ACTIONS fill:#2088ff,color:#fff
    style APP fill:#4a90e2,color:#fff
```

## セキュリティ考慮事項

```mermaid
graph TB
    subgraph "Secrets Management"
        GH_SECRETS[GitHub Secrets]
        ENV_VARS[Environment Variables]
    end

    subgraph "API Authentication"
        DISCORD_TOKEN[Discord Webhook URLs]
        CLAUDE_TOKEN[Claude OAuth Token]
    end

    subgraph "Access Control"
        READONLY[Read-only APIs<br/>GitHub, Homebrew]
        WRITEONLY[Write-only APIs<br/>Discord Webhook]
        AUTH[Authenticated APIs<br/>Claude API]
    end

    GH_SECRETS --> ENV_VARS
    ENV_VARS --> DISCORD_TOKEN
    ENV_VARS --> CLAUDE_TOKEN

    DISCORD_TOKEN --> WRITEONLY
    CLAUDE_TOKEN --> AUTH

    style GH_SECRETS fill:#28a745,color:#fff
    style AUTH fill:#ffa500,color:#fff
```

## スケーラビリティ

現在の設計は以下の点でスケーラブルです：

1. **ツールの追加**: `config.yml`に新しいツールを追加するだけで対応可能
2. **情報源の追加**: 新しいSourceクラスを実装するだけで対応可能
3. **翻訳サービスの追加**: Translatorクラスを拡張するだけで対応可能
4. **非同期処理**: httpxを使用しているため、将来的に非同期処理に移行可能

## 将来の拡張可能性

```mermaid
graph TB
    CURRENT[Current System]

    subgraph "Future Extensions"
        ASYNC[Async Processing<br/>Concurrent Checks]
        DB[Database<br/>SQLite/PostgreSQL]
        WEB[Web Dashboard<br/>Monitoring UI]
        SLACK[Slack Integration]
        EMAIL[Email Notifications]
        MULTI_LANG[Multi-language Support]
    end

    CURRENT --> ASYNC
    CURRENT --> DB
    CURRENT --> WEB
    CURRENT --> SLACK
    CURRENT --> EMAIL
    CURRENT --> MULTI_LANG

    style CURRENT fill:#4a90e2,color:#fff
    style ASYNC fill:#50c878,color:#fff
    style DB fill:#f39c12,color:#fff
    style WEB fill:#e74c3c,color:#fff
```

## 技術選択の理由

### httpx

- 非同期対応（将来の拡張性）
- HTTP/2サポート
- より良いタイムアウト管理
- requestsの後継として設計

### uv

- 高速なパッケージ解決
- 一貫した依存関係管理
- 仮想環境の自動管理

### pydantic

- 型安全なデータ検証
- 設定管理の簡素化
- 将来的なAPI統合の容易性

### feedparser

- 実績のあるRSS/Atom解析ライブラリ
- GitHub Atomフィードとの互換性

### Claude API

- 高品質な日本語翻訳
- 技術文書の適切な要約
- コンテキスト理解能力
