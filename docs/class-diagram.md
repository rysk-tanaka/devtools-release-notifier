# クラス図

devtools-release-notifierのクラス構造とその関係を示します。

## 主要クラス図

```mermaid
classDiagram
    class UnifiedReleaseNotifier {
        -dict config
        -Path cache_dir
        -DiscordNotifier discord_notifier
        -list new_releases
        +__init__(config_path: str)
        +run() None
        +process_tool(tool: dict) None
        +get_source(source_config: dict) ReleaseSource
        +get_cache_path(tool_name: str) Path
        +load_cached_version(tool_name: str) Optional~dict~
        +save_cached_version(tool_name: str, version_info: dict) None
        +output_releases_json(filepath: str) None
    }

    class ReleaseSource {
        <<abstract>>
        #dict config
        +__init__(config: dict)
        +fetch_latest_version()* Optional~dict~
    }

    class GitHubReleaseSource {
        -str atom_url
        +__init__(config: dict)
        +fetch_latest_version() Optional~dict~
        -parse_atom_feed(xml: str) Optional~dict~
    }

    class GitHubCommitsSource {
        -str atom_url
        +__init__(config: dict)
        +fetch_latest_version() Optional~dict~
        -parse_atom_feed(xml: str) Optional~dict~
    }

    class HomebrewCaskSource {
        -str api_url
        -str cask_name
        +__init__(config: dict)
        +fetch_latest_version() Optional~dict~
        -generate_install_info(data: dict) str
    }

    class DiscordNotifier {
        +send(webhook_url: str, tool_name: str, content: str, url: str, color: int) bool
        -build_embed(tool_name: str, content: str, url: str, color: int) dict
    }

    ReleaseSource <|-- GitHubReleaseSource : implements
    ReleaseSource <|-- GitHubCommitsSource : implements
    ReleaseSource <|-- HomebrewCaskSource : implements

    UnifiedReleaseNotifier --> ReleaseSource : uses
    UnifiedReleaseNotifier --> DiscordNotifier : uses

    UnifiedReleaseNotifier ..> GitHubReleaseSource : creates
    UnifiedReleaseNotifier ..> GitHubCommitsSource : creates
    UnifiedReleaseNotifier ..> HomebrewCaskSource : creates
```

## データモデル

```mermaid
classDiagram
    class Config {
        +List~Tool~ tools
        +Common common
    }

    class Tool {
        +str name
        +bool enabled
        +List~Source~ sources
        +Translation translation
        +Notification notification
    }

    class Source {
        +str type
        +int priority
        +Optional~str~ atom_url
        +Optional~str~ api_url
        +Optional~str~ owner
        +Optional~str~ repo
        +Optional~str~ cask_name
    }

    class Translation {
        +str target_lang
    }

    class Notification {
        +str webhook_env
        +int color
    }

    class Common {
        +int check_interval_hours
        +str cache_directory
        +str translation_service
    }

    class VersionInfo {
        +str version
        +str content
        +str url
        +datetime published
        +str source
    }

    class DiscordEmbed {
        +str title
        +str description
        +str url
        +int color
        +str timestamp
        +Footer footer
    }

    class Footer {
        +str text
    }

    Config "1" *-- "many" Tool
    Config "1" *-- "1" Common
    Tool "1" *-- "many" Source
    Tool "1" *-- "1" Translation
    Tool "1" *-- "1" Notification
    DiscordEmbed "1" *-- "1" Footer
```

## モジュール構成

```mermaid
graph TB
    subgraph "devtools_release_notifier Package"
        INIT[__init__.py<br/>__version__]

        subgraph "notifier.py"
            MAIN_CLASS[UnifiedReleaseNotifier]
            MAIN_FUNC[main]
        end

        subgraph "sources.py"
            BASE[ReleaseSource]
            GHR[GitHubReleaseSource]
            GHC[GitHubCommitsSource]
            HB[HomebrewCaskSource]
        end

        subgraph "discord_notifier.py"
            NOTIF[DiscordNotifier]
        end
    end

    MAIN_CLASS --> BASE
    MAIN_CLASS --> GHR
    MAIN_CLASS --> GHC
    MAIN_CLASS --> HB
    MAIN_CLASS --> NOTIF

    MAIN_FUNC --> MAIN_CLASS

    BASE <|-- GHR
    BASE <|-- GHC
    BASE <|-- HB

    style INIT fill:#50c878,color:#fff
    style MAIN_CLASS fill:#4a90e2,color:#fff
    style BASE fill:#f39c12,color:#fff
    style NOTIF fill:#7289da,color:#fff
```

## 依存関係図

```mermaid
graph LR
    subgraph "Standard Library"
        OS[os]
        JSON[json]
        PATH[pathlib]
        DT[datetime]
        ABC[abc]
        TRACE[traceback]
    end

    subgraph "Third-party Libraries"
        HTTPX[httpx]
        YAML[yaml]
        FP[feedparser]
    end

    subgraph "Application Modules"
        NOTIFIER[notifier.py]
        SOURCES[sources.py]
        DISCORD[discord_notifier.py]
    end

    NOTIFIER --> OS
    NOTIFIER --> JSON
    NOTIFIER --> PATH
    NOTIFIER --> YAML
    NOTIFIER --> TRACE

    NOTIFIER --> SOURCES
    NOTIFIER --> DISCORD

    SOURCES --> ABC
    SOURCES --> DT
    SOURCES --> HTTPX
    SOURCES --> FP

    DISCORD --> DT
    DISCORD --> HTTPX

    style NOTIFIER fill:#4a90e2,color:#fff
    style SOURCES fill:#f39c12,color:#fff
    style DISCORD fill:#7289da,color:#fff
```
