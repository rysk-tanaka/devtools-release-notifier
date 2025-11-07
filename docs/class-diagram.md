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

## インターフェース詳細

### ReleaseSource Interface

```mermaid
classDiagram
    class ReleaseSource {
        <<interface>>
        +fetch_latest_version() Optional~dict~
    }

    note for ReleaseSource "Returns:\n{\n  'version': str,\n  'content': str,\n  'url': str,\n  'published': datetime,\n  'source': str\n}\nor None if fetch fails"
```

### DiscordNotifier Interface

```mermaid
classDiagram
    class DiscordNotifier {
        +send(webhook_url: str, tool_name: str, content: str, url: str, color: int) bool
    }

    note for DiscordNotifier "Returns:\nTrue if notification sent successfully\nFalse if failed"
```

## メソッド詳細

### UnifiedReleaseNotifier Methods

```mermaid
sequenceDiagram
    participant Client
    participant URN as UnifiedReleaseNotifier
    participant Source
    participant Discord

    Client->>URN: __init__(config_path)
    URN->>URN: Load config.yml
    URN->>URN: Create cache directory
    URN->>Discord: Create DiscordNotifier

    Client->>URN: run(args)
    loop For each tool
        URN->>URN: process_tool(tool)
        URN->>Source: fetch_latest_version()
        Source-->>URN: version_info

        URN->>URN: load_cached_version(tool_name)
        URN->>URN: Compare versions

        alt New version detected
            alt --output specified
                URN->>URN: Collect release info
            end
            alt --no-notify not specified
                URN->>Discord: send(webhook_url, ...)
                Discord-->>URN: success
            end
            URN->>URN: save_cached_version(tool_name, version_info)
        end
    end
    alt --output specified
        URN->>URN: Write releases.json
    end
```

## 型定義

```mermaid
classDiagram
    class VersionInfoDict {
        <<TypedDict>>
        +str version
        +str content
        +str url
        +datetime published
        +str source
    }

    class ConfigDict {
        <<TypedDict>>
        +List~ToolDict~ tools
        +CommonDict common
    }

    class ToolDict {
        <<TypedDict>>
        +str name
        +bool enabled
        +List~SourceDict~ sources
        +TranslationDict translation
        +NotificationDict notification
    }

    class SourceDict {
        <<TypedDict>>
        +str type
        +int priority
        +Optional~str~ atom_url
        +Optional~str~ api_url
        +Optional~str~ owner
        +Optional~str~ repo
        +Optional~str~ cask_name
    }

    class TranslationDict {
        <<TypedDict>>
        +str target_lang
    }

    class NotificationDict {
        <<TypedDict>>
        +str webhook_env
        +int color
    }

    class CommonDict {
        <<TypedDict>>
        +int check_interval_hours
        +str cache_directory
        +str translation_service
    }

    ConfigDict "1" *-- "many" ToolDict
    ConfigDict "1" *-- "1" CommonDict
    ToolDict "1" *-- "many" SourceDict
    ToolDict "1" *-- "1" TranslationDict
    ToolDict "1" *-- "1" NotificationDict
```

## エラーハンドリングクラス

```mermaid
classDiagram
    class httpxHTTPError {
        <<exception>>
    }

    class YAMLError {
        <<exception>>
    }

    class KeyError {
        <<exception>>
    }

    class FileNotFoundError {
        <<exception>>
    }

    class Exception {
        <<base>>
    }

    Exception <|-- httpxHTTPError
    Exception <|-- YAMLError
    Exception <|-- KeyError
    Exception <|-- FileNotFoundError

    note for httpxHTTPError "Handled in:\n- sources.py\n- discord_notifier.py"

    note for YAMLError "Handled in:\n- notifier.py (config loading)"

    note for KeyError "Handled in:\n- notifier.py (config access)"

    note for FileNotFoundError "Handled in:\n- notifier.py (config file)"
```

## Factory Pattern

```mermaid
classDiagram
    class SourceFactory {
        <<static>>
        +create_source(source_config: dict) ReleaseSource
    }

    class ReleaseSource {
        <<abstract>>
    }

    class GitHubReleaseSource
    class GitHubCommitsSource
    class HomebrewCaskSource

    SourceFactory ..> ReleaseSource : creates
    SourceFactory ..> GitHubReleaseSource : creates
    SourceFactory ..> GitHubCommitsSource : creates
    SourceFactory ..> HomebrewCaskSource : creates

    ReleaseSource <|-- GitHubReleaseSource
    ReleaseSource <|-- GitHubCommitsSource
    ReleaseSource <|-- HomebrewCaskSource

    note for SourceFactory "Implemented as get_source() method\nin UnifiedReleaseNotifier class"
```

## Cache Manager (Implicit)

```mermaid
classDiagram
    class CacheManager {
        <<implicit in UnifiedReleaseNotifier>>
        -Path cache_dir
        +get_cache_path(tool_name: str) Path
        +load_cached_version(tool_name: str) Optional~dict~
        +save_cached_version(tool_name: str, version_info: dict) None
    }

    class FileSystem {
        <<external>>
        +read(path: Path) str
        +write(path: Path, content: str) None
        +exists(path: Path) bool
    }

    CacheManager --> FileSystem : uses

    note for CacheManager "Methods are part of\nUnifiedReleaseNotifier class\nfor simplicity"
```

## 継承階層

```mermaid
graph TD
    ABC[abc.ABC] --> ReleaseSource
    ReleaseSource --> GitHubReleaseSource
    ReleaseSource --> GitHubCommitsSource
    ReleaseSource --> HomebrewCaskSource

    style ABC fill:#e74c3c,color:#fff
    style ReleaseSource fill:#f39c12,color:#fff
    style GitHubReleaseSource fill:#50c878,color:#fff
    style GitHubCommitsSource fill:#50c878,color:#fff
    style HomebrewCaskSource fill:#50c878,color:#fff
```
