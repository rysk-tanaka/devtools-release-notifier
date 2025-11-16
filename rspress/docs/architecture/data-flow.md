# データフロー

devtools-release-notifierのデータフロー図です。

## 全体のデータフロー

```mermaid
flowchart TD
    START([Start]) --> LOAD_CONFIG[Load config.yml]
    LOAD_CONFIG --> INIT[Initialize Components<br/>DiscordNotifier]

    INIT --> LOOP_START{For Each Tool<br/>in Config}

    LOOP_START --> CHECK_ENABLED{Tool<br/>Enabled?}
    CHECK_ENABLED -->|No| SKIP[Skip Tool]
    SKIP --> LOOP_END

    CHECK_ENABLED -->|Yes| SORT_SOURCES[Sort Sources<br/>by Priority]

    SORT_SOURCES --> SOURCE_LOOP{Try Each<br/>Source}

    SOURCE_LOOP --> FETCH[Fetch Latest<br/>Version Info]

    FETCH --> FETCH_SUCCESS{Fetch<br/>Success?}
    FETCH_SUCCESS -->|No| NEXT_SOURCE{More<br/>Sources?}
    NEXT_SOURCE -->|Yes| SOURCE_LOOP
    NEXT_SOURCE -->|No| WARN[Log Warning:<br/>All Sources Failed]
    WARN --> LOOP_END

    FETCH_SUCCESS -->|Yes| LOAD_CACHE[Load Cached<br/>Version]

    LOAD_CACHE --> COMPARE{Version<br/>Changed?}

    COMPARE -->|No| INFO[Log: No Update]
    INFO --> LOOP_END

    COMPARE -->|Yes| CHECK_OUTPUT{--output<br/>option?}

    CHECK_OUTPUT -->|Yes| COLLECT[Collect Release<br/>Info for JSON]
    CHECK_OUTPUT -->|No| CHECK_NOTIFY{--no-notify<br/>option?}

    COLLECT --> CHECK_NOTIFY

    CHECK_NOTIFY -->|Yes| SKIP_NOTIFY[Skip Notification]
    CHECK_NOTIFY -->|No| NOTIFY[Send Discord<br/>Notification]

    NOTIFY --> NOTIFY_SUCCESS{Notification<br/>Success?}
    NOTIFY_SUCCESS -->|No| ERR_LOG[Log Error]
    NOTIFY_SUCCESS -->|Yes| SUCCESS_LOG[Log Success]

    ERR_LOG --> UPDATE_CACHE
    SUCCESS_LOG --> UPDATE_CACHE[Update Cache<br/>Save New Version]
    SKIP_NOTIFY --> UPDATE_CACHE

    UPDATE_CACHE --> LOOP_END

    LOOP_END --> LOOP_START

    LOOP_START -->|No More Tools| OUTPUT_CHECK{--output<br/>specified?}
    OUTPUT_CHECK -->|Yes| OUTPUT_JSON[Write releases.json]
    OUTPUT_CHECK -->|No| END
    OUTPUT_JSON --> END([End])

    style START fill:#28a745,color:#fff
    style END fill:#dc3545,color:#fff
    style FETCH fill:#4a90e2,color:#fff
    style NOTIFY fill:#7289da,color:#fff
    style UPDATE_CACHE fill:#f39c12,color:#fff
    style OUTPUT_JSON fill:#f39c12,color:#fff
```

## データ変換フロー

```mermaid
flowchart LR
    subgraph "GitHub Releases"
        GHR_RAW[Atom Feed<br/>XML]
        GHR_PARSED[Parsed Entry]
        GHR_DICT[Version Dict]

        GHR_RAW --> |feedparser| GHR_PARSED
        GHR_PARSED --> |extract| GHR_DICT
    end

    subgraph "Homebrew API"
        HB_RAW[JSON Response]
        HB_PARSED[Parsed Object]
        HB_DICT[Version Dict]

        HB_RAW --> |json.loads| HB_PARSED
        HB_PARSED --> |transform| HB_DICT
    end

    subgraph "Unified Format"
        UNIFIED["(
            version: str,
            content: str,
            url: str,
            published: datetime,
            source: str
        )"]
    end

    GHR_DICT --> UNIFIED
    HB_DICT --> UNIFIED

    subgraph "JSON Output (--output)"
        JSON_OUTPUT["(
            tool_name: str,
            version: str,
            content: str,
            url: str,
            color: int,
            webhook_env: str
        )"]
    end

    UNIFIED --> JSON_OUTPUT

    subgraph "GitHub Actions Translation"
        TRANS_IN[releases.json]
        CLAUDE_TRANS[claude-code-action<br/>Translation]
        TRANS_OUT[Translated JSON]

        TRANS_IN --> CLAUDE_TRANS
        CLAUDE_TRANS --> TRANS_OUT
    end

    JSON_OUTPUT --> TRANS_IN

    subgraph "Discord Message"
        DISCORD_EMBED[{
            title: str,
            description: str,
            url: str,
            color: int,
            timestamp: str,
            footer: obj
        }]
    end

    TRANS_OUT --> |send_to_discord.py| DISCORD_EMBED

    style UNIFIED fill:#4a90e2,color:#fff
    style JSON_OUTPUT fill:#f39c12,color:#fff
    style CLAUDE_TRANS fill:#8e44ad,color:#fff
    style DISCORD_EMBED fill:#7289da,color:#fff
```

## 優先度ベースのソース選択フロー

```mermaid
flowchart TD
    START([Process Tool]) --> GET_SOURCES[Get All Sources<br/>from Config]

    GET_SOURCES --> SORT[Sort by Priority<br/>1, 2, 3, ...]

    SORT --> INIT_INDEX[Index = 0]

    INIT_INDEX --> LOOP{Index <<br/>Sources Length?}

    LOOP -->|Yes| GET_SOURCE[Get Source<br/>at Index]

    GET_SOURCE --> TRY_FETCH[Try Fetch from<br/>Source]

    TRY_FETCH --> SUCCESS{Fetch<br/>Success?}

    SUCCESS -->|Yes| USE_DATA[Use Fetched Data]
    USE_DATA --> DONE([Done])

    SUCCESS -->|No| LOG_FAIL[Log Warning:<br/>Source Failed]

    LOG_FAIL --> INCREMENT[Index++]

    INCREMENT --> LOOP

    LOOP -->|No| ALL_FAILED[All Sources Failed]

    ALL_FAILED --> LOG_ERROR[Log Error:<br/>No Data Available]

    LOG_ERROR --> DONE

    style START fill:#28a745,color:#fff
    style DONE fill:#dc3545,color:#fff
    style USE_DATA fill:#50c878,color:#fff
    style ALL_FAILED fill:#ffc107,color:#000
```
