# システムアーキテクチャ

devtools-release-notifierのシステムアーキテクチャ図です。

## 全体アーキテクチャ

```mermaid
graph TB
    subgraph "External Services"
        GHR[GitHub Releases<br/>Atom Feed]
        GHC[GitHub Commits<br/>Atom Feed]
        HB[Homebrew API<br/>JSON API]
        CLAUDE[Claude Code Action]
        DISCORD[Discord<br/>Webhook]
    end

    subgraph "GitHub Actions"
        SCHEDULE[Scheduled Trigger<br/>Every Day 10:00 UTC]
        MANUAL[Manual Trigger<br/>workflow_dispatch]
        RUNNER[GitHub Actions Runner]
        TRANSLATE[Translation Step<br/>claude-code-action]
        EXTRACT_SCRIPT[extract_claude_response.py<br/>Extract Translation]
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
    CLAUDE -->|execution_file| EXTRACT_SCRIPT
    EXTRACT_SCRIPT -->|translated content| SEND_SCRIPT
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

- GitHub Releases/Commits: Atomフィード形式でリリース情報を提供
- Homebrew API: JSON形式でパッケージ情報を提供
- Claude Code Action: AI による翻訳・要約サービス
- Discord Webhook: 通知配信サービス

### GitHub Actions

- Scheduled Trigger: 毎日10:00 UTCに自動実行
- Manual Trigger: 手動実行用のトリガー
- Runner: ワークフロー実行環境
- Translation Step: claude-code-actionを使用した翻訳処理
- send_to_discord.py: 翻訳されたコンテンツをDiscordに送信するスクリプト

### Application Core

#### UnifiedReleaseNotifier

- システムの中核となるオーケストレーター
- 各ツールの処理を統括
- 優先度ベースのソース選択
- キャッシュ管理
- エラーハンドリング

#### Source Module

- ReleaseSource: 情報源の抽象基底クラス
- GitHubReleaseSource: GitHub Releasesから情報取得
- GitHubCommitsSource: GitHub Commitsから情報取得
- HomebrewCaskSource: Homebrew APIから情報取得

#### Notification Module

- DiscordNotifier: Discord Webhookへの通知送信
- リッチ埋め込みメッセージ形式

#### Cache Module

- Version Cache: JSONファイル形式でバージョン情報を永続化
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
