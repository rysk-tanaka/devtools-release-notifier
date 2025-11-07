# シーケンス図

devtools-release-notifierの主要な処理シーケンスを示します。

## メイン処理シーケンス

```mermaid
sequenceDiagram
    actor User
    participant GHA as GitHub Actions
    participant Main as main()
    participant URN as UnifiedReleaseNotifier
    participant Config as config.yml

    User->>GHA: Trigger (Schedule/Manual)
    GHA->>Main: Execute

    Main->>Config: Check existence
    alt Config not found
        Main->>User: Error: config.yml not found
        Main->>Main: Exit
    end

    Main->>URN: __init__(config_path)
    URN->>Config: Load YAML
    Config-->>URN: Return config dict

    URN->>URN: Create cache directory
    URN->>URN: Initialize Translator
    URN->>URN: Initialize DiscordNotifier

    Main->>URN: run()

    URN->>User: Log: Starting notification check

    loop For each tool in config
        URN->>URN: process_tool(tool)
    end

    URN->>User: Log: Completed notification check
    URN-->>Main: Return

    Main-->>GHA: Exit 0
    GHA->>GHA: Commit cache files
    GHA->>GHA: Push to repository
```

## ツール処理シーケンス（詳細）

```mermaid
sequenceDiagram
    participant URN as UnifiedReleaseNotifier
    participant Source as ReleaseSource
    participant Cache as Cache Files
    participant Trans as Translator
    participant Discord as DiscordNotifier
    participant User

    URN->>URN: process_tool(tool)

    alt Tool disabled
        URN->>User: Log: Tool skipped
        URN->>URN: Return
    end

    URN->>User: Log: Processing tool

    URN->>URN: Sort sources by priority

    loop Try each source
        URN->>Source: fetch_latest_version()
        Source-->>URN: version_info or None

        alt Fetch successful
            URN->>URN: Break loop
        else Fetch failed
            URN->>User: Warning: Source failed
        end
    end

    alt All sources failed
        URN->>User: Warning: All sources failed
        URN->>URN: Return
    end

    URN->>Cache: load_cached_version(tool_name)
    Cache-->>URN: cached_version or None

    alt Version unchanged
        URN->>User: Info: No update
        URN->>URN: Return
    end

    URN->>User: Log: New version detected

    URN->>Trans: translate_and_summarize(tool_name, version, content)
    Trans-->>URN: translated_content

    URN->>URN: Get webhook URL from env

    alt Webhook URL not found
        URN->>User: Error: Webhook URL not found
        URN->>URN: Return
    end

    URN->>Discord: send(webhook_url, tool_name, content, url, color)
    Discord-->>URN: success/failure

    alt Notification sent
        URN->>User: Log: Notification sent
        URN->>Cache: save_cached_version(tool_name, version_info)
    else Notification failed
        URN->>User: Error: Notification failed
    end
```

## GitHub Releases ソース取得シーケンス

```mermaid
sequenceDiagram
    participant URN as UnifiedReleaseNotifier
    participant GHR as GitHubReleaseSource
    participant httpx
    participant GitHub as GitHub API
    participant FP as feedparser

    URN->>GHR: fetch_latest_version()

    GHR->>httpx: get(atom_url, timeout=10.0)
    httpx->>GitHub: HTTP GET /releases.atom
    GitHub-->>httpx: Atom XML Response

    alt HTTP Error
        httpx-->>GHR: raise httpx.HTTPError
        GHR->>GHR: Log error
        GHR-->>URN: Return None
    end

    httpx-->>GHR: Response (200 OK)
    GHR->>httpx: raise_for_status()

    GHR->>FP: parse(atom_xml)
    FP-->>GHR: Parsed feed object

    alt No entries
        GHR->>GHR: Log warning
        GHR-->>URN: Return None
    end

    GHR->>GHR: Extract latest entry
    GHR->>GHR: Build version_info dict
    GHR-->>URN: Return version_info
```

## Homebrew API ソース取得シーケンス

```mermaid
sequenceDiagram
    participant URN as UnifiedReleaseNotifier
    participant HB as HomebrewCaskSource
    participant httpx
    participant Homebrew as Homebrew API

    URN->>HB: fetch_latest_version()

    HB->>httpx: get(api_url, timeout=10.0)
    httpx->>Homebrew: HTTP GET /api/cask/{name}.json
    Homebrew-->>httpx: JSON Response

    alt HTTP Error
        httpx-->>HB: raise httpx.HTTPError
        HB->>HB: Log error
        HB-->>URN: Return None
    end

    httpx-->>HB: Response (200 OK)
    HB->>httpx: raise_for_status()

    HB->>httpx: response.json()
    httpx-->>HB: Parsed JSON dict

    HB->>HB: Extract version
    HB->>HB: Generate install info
    HB->>HB: Extract homepage URL
    HB->>HB: Build version_info dict
    HB-->>URN: Return version_info
```

## 翻訳処理シーケンス

```mermaid
sequenceDiagram
    participant URN as UnifiedReleaseNotifier
    participant Trans as Translator
    participant httpx
    participant Claude as Claude API

    URN->>Trans: translate_and_summarize(tool_name, version, content)

    alt Service not "claude"
        Trans-->>URN: Return original content
    end

    alt OAuth token not available
        Trans->>Trans: Log warning
        Trans-->>URN: Return original content
    end

    Trans->>Trans: Build translation prompt

    Trans->>httpx: post(api_url, headers, json, timeout=30.0)
    httpx->>Claude: HTTP POST /v1/messages

    Claude->>Claude: Process with claude-sonnet-4-20250514

    alt HTTP Error or Timeout
        Claude-->>httpx: Error
        httpx-->>Trans: raise httpx.HTTPError
        Trans->>Trans: Log error
        Trans-->>URN: Return original content
    end

    Claude-->>httpx: JSON Response
    httpx-->>Trans: Response (200 OK)

    Trans->>httpx: raise_for_status()
    Trans->>httpx: response.json()
    httpx-->>Trans: Parsed JSON

    Trans->>Trans: Extract content[0].text
    Trans-->>URN: Return translated content
```

## Discord通知シーケンス

```mermaid
sequenceDiagram
    participant URN as UnifiedReleaseNotifier
    participant DN as DiscordNotifier
    participant httpx
    participant Discord as Discord Webhook

    URN->>DN: send(webhook_url, tool_name, content, url, color)

    DN->>DN: Build embed object
    DN->>DN: Set title, description, color
    DN->>DN: Set URL, timestamp, footer
    DN->>DN: Truncate description to 4000 chars

    DN->>httpx: post(webhook_url, json, timeout=10.0)
    httpx->>Discord: HTTP POST webhook

    alt HTTP Error
        Discord-->>httpx: Error Response
        httpx-->>DN: raise httpx.HTTPError
        DN->>DN: Log error
        DN-->>URN: Return False
    end

    Discord-->>httpx: 204 No Content
    httpx-->>DN: Response (204)

    DN->>httpx: raise_for_status()
    DN-->>URN: Return True
```

## キャッシュ読み込みシーケンス

```mermaid
sequenceDiagram
    participant URN as UnifiedReleaseNotifier
    participant FS as File System

    URN->>URN: load_cached_version(tool_name)
    URN->>URN: get_cache_path(tool_name)

    URN->>FS: Check file exists

    alt File not exists
        FS-->>URN: False
        URN-->>URN: Return None
    end

    FS-->>URN: True
    URN->>FS: Read file
    FS-->>URN: JSON string

    URN->>URN: json.loads()

    alt JSON parse error
        URN->>URN: Log error
        URN-->>URN: Return None
    end

    URN-->>URN: Return cached dict
```

## キャッシュ保存シーケンス

```mermaid
sequenceDiagram
    participant URN as UnifiedReleaseNotifier
    participant FS as File System

    URN->>URN: save_cached_version(tool_name, version_info)
    URN->>URN: get_cache_path(tool_name)

    URN->>URN: Convert datetime to ISO format
    URN->>URN: Serialize to JSON

    URN->>FS: Create cache directory if needed
    URN->>FS: Write JSON to file
    FS-->>URN: Success

    URN->>URN: Log: Cache updated
```

## エラーハンドリングシーケンス

```mermaid
sequenceDiagram
    participant Main as main()
    participant URN as UnifiedReleaseNotifier
    participant Source as ReleaseSource
    participant User

    Main->>URN: run()

    URN->>Source: fetch_latest_version()

    alt httpx.HTTPError
        Source->>Source: Catch exception
        Source->>User: Log: HTTP Error (status, URL)
        Source-->>URN: Return None
        URN->>User: Warning: Source failed
        URN->>URN: Try next source
    end

    alt Network/Timeout Error
        Source->>Source: Catch exception
        Source->>User: Log: Network Error
        Source-->>URN: Return None
        URN->>User: Warning: Source failed
        URN->>URN: Try next source
    end

    alt Parse Error (feedparser/json)
        Source->>Source: Catch exception
        Source->>User: Log: Parse Error
        Source-->>URN: Return None
        URN->>User: Warning: Source failed
        URN->>URN: Try next source
    end

    alt Fatal Error (KeyboardInterrupt)
        URN->>URN: Catch KeyboardInterrupt
        URN->>User: Info: Interrupted by user
        URN-->>Main: Exit
    end

    alt Unknown Error
        URN->>URN: Catch Exception
        URN->>User: Error: Unexpected error + traceback
        URN-->>Main: Exit with error
    end
```

## GitHub Actions統合シーケンス

```mermaid
sequenceDiagram
    participant Schedule as Cron Schedule
    participant GHA as GitHub Actions
    participant Env as Environment
    participant Script as devtools-notifier
    participant Cache as Cache Files
    participant Git as Git Repository

    alt Scheduled Trigger
        Schedule->>GHA: Every Monday 10:00 UTC
    else Manual Trigger
        User->>GHA: workflow_dispatch
    end

    GHA->>GHA: Checkout repository
    GHA->>GHA: Setup uv
    GHA->>GHA: Install Python
    GHA->>GHA: uv sync

    GHA->>Env: Load GitHub Secrets
    Env->>Env: DISCORD_WEBHOOK
    Env->>Env: CLAUDE_CODE_OAUTH_TOKEN

    GHA->>Script: uv run devtools-notifier
    Script->>Script: Process all tools
    Script->>Cache: Update cache files
    Script-->>GHA: Exit 0

    GHA->>Git: git config user
    GHA->>Git: git add cache/*.json

    alt Cache changed
        GHA->>Git: git commit
        GHA->>Git: git push
        Git-->>GHA: Success
    else No changes
        GHA->>GHA: Skip commit
    end

    GHA-->>Schedule: Complete
```

## 優先度ベースのフォールバックシーケンス

```mermaid
sequenceDiagram
    participant URN as UnifiedReleaseNotifier
    participant S1 as Source (Priority 1)
    participant S2 as Source (Priority 2)
    participant S3 as Source (Priority 3)
    participant User

    URN->>URN: Sort sources by priority

    URN->>S1: fetch_latest_version()

    alt S1 Success
        S1-->>URN: version_info
        URN->>User: Log: Using Priority 1 source
        URN->>URN: Process version
    else S1 Failed
        S1-->>URN: None
        URN->>User: Warning: Priority 1 failed

        URN->>S2: fetch_latest_version()

        alt S2 Success
            S2-->>URN: version_info
            URN->>User: Log: Using Priority 2 source
            URN->>URN: Process version
        else S2 Failed
            S2-->>URN: None
            URN->>User: Warning: Priority 2 failed

            URN->>S3: fetch_latest_version()

            alt S3 Success
                S3-->>URN: version_info
                URN->>User: Log: Using Priority 3 source
                URN->>URN: Process version
            else S3 Failed
                S3-->>URN: None
                URN->>User: Error: All sources failed
                URN->>URN: Skip tool
            end
        end
    end
```

## 設定読み込みシーケンス

```mermaid
sequenceDiagram
    participant Main as main()
    participant URN as UnifiedReleaseNotifier
    participant FS as File System
    participant YAML as PyYAML

    Main->>URN: __init__(config_path)

    URN->>FS: Check config.yml exists

    alt File not found
        FS-->>URN: FileNotFoundError
        URN->>URN: Raise error
        URN-->>Main: Exit
    end

    URN->>FS: Read config.yml
    FS-->>URN: YAML string

    URN->>YAML: yaml.safe_load()

    alt YAML parse error
        YAML-->>URN: YAMLError
        URN->>URN: Raise error
        URN-->>Main: Exit
    end

    YAML-->>URN: Config dict

    URN->>URN: Validate config structure
    URN->>URN: Extract common settings
    URN->>URN: Extract tools list

    alt Missing required keys
        URN->>URN: Raise KeyError
        URN-->>Main: Exit
    end

    URN->>URN: Initialize components
    URN-->>Main: Ready
```

## 完全な実行フローシーケンス

```mermaid
sequenceDiagram
    participant User
    participant GHA as GitHub Actions
    participant Main as main()
    participant URN as UnifiedReleaseNotifier
    participant Sources
    participant Translator
    participant Discord
    participant Cache

    User->>GHA: Trigger workflow

    GHA->>Main: Execute script
    Main->>URN: Initialize

    URN->>Cache: Load config.yml
    URN->>URN: Create components

    Main->>URN: run()

    loop For each tool
        URN->>Sources: fetch_latest_version()
        Sources-->>URN: version_info

        URN->>Cache: load_cached_version()
        Cache-->>URN: cached_version

        alt New version
            URN->>Translator: translate_and_summarize()
            Translator-->>URN: translated_content

            URN->>Discord: send()
            Discord-->>URN: success

            URN->>Cache: save_cached_version()
        end
    end

    URN-->>Main: Complete
    Main-->>GHA: Exit 0

    GHA->>Cache: Commit changes
    GHA->>GHA: Push to repository
    GHA-->>User: Workflow complete
```
