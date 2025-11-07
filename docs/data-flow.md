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

## 情報源からのデータ取得フロー

```mermaid
sequenceDiagram
    participant Main as UnifiedReleaseNotifier
    participant Source as ReleaseSource
    participant GitHub as GitHub API
    participant Homebrew as Homebrew API

    Main->>Source: fetch_latest_version()

    alt GitHub Releases/Commits
        Source->>GitHub: GET /{owner}/{repo}/releases.atom
        GitHub-->>Source: Atom Feed XML
        Source->>Source: Parse with feedparser
        Source->>Source: Extract version, content, url
        Source-->>Main: Return version info dict

    else Homebrew Cask
        Source->>Homebrew: GET /api/cask/{name}.json
        Homebrew-->>Source: JSON Response
        Source->>Source: Extract version, homepage
        Source->>Source: Generate install info
        Source-->>Main: Return version info dict
    end

    alt Fetch Failed
        Source-->>Main: Return None
        Main->>Main: Try next source
    end
```

## GitHub Actions翻訳フロー

```mermaid
flowchart TD
    START([GitHub Actions Start]) --> RUN_NOTIFIER[Run devtools-notifier<br/>--output releases.json --no-notify]

    RUN_NOTIFIER --> CHECK_FILE{releases.json<br/>exists?}

    CHECK_FILE -->|No| NO_RELEASES[No new releases]
    NO_RELEASES --> END

    CHECK_FILE -->|Yes| READ_JSON[Read releases.json]

    READ_JSON --> CLAUDE_ACTION[anthropics/claude-code-action@beta<br/>Translate to Japanese]

    CLAUDE_ACTION --> PARSE_RESPONSE[Parse Translated<br/>JSON Response]

    PARSE_RESPONSE --> SEND_SCRIPT[Run send_to_discord.py<br/>with translated content]

    SEND_SCRIPT --> SEND_SUCCESS{Send<br/>Success?}

    SEND_SUCCESS -->|Yes| COMMIT[Commit cache updates]
    SEND_SUCCESS -->|No| LOG_ERROR[Log Error]

    LOG_ERROR --> COMMIT
    COMMIT --> END([End])

    style START fill:#28a745,color:#fff
    style END fill:#dc3545,color:#fff
    style CLAUDE_ACTION fill:#8e44ad,color:#fff
    style SEND_SCRIPT fill:#7289da,color:#fff
```

## Discord通知フロー

```mermaid
flowchart TD
    START([Notification Request]) --> GET_WEBHOOK[Get Webhook URL<br/>from Environment]

    GET_WEBHOOK --> CHECK_WEBHOOK{Webhook URL<br/>Exists?}

    CHECK_WEBHOOK -->|No| ERROR[Log Error:<br/>Missing Webhook]
    ERROR --> RETURN_FALSE

    CHECK_WEBHOOK -->|Yes| BUILD_EMBED[Build Embed<br/>Message]

    BUILD_EMBED --> SET_TITLE[Set Title:<br/>Tool Name + Version]

    SET_TITLE --> SET_DESC[Set Description:<br/>Translated Content]

    SET_DESC --> SET_COLOR[Set Color:<br/>Tool-specific]

    SET_COLOR --> SET_URL[Set URL:<br/>Release/Homepage]

    SET_URL --> SET_TIMESTAMP[Set Timestamp:<br/>Current UTC]

    SET_TIMESTAMP --> SET_FOOTER[Set Footer:<br/>devtools-release-notifier]

    SET_FOOTER --> POST[HTTP POST to<br/>Discord Webhook]

    POST --> POST_SUCCESS{POST<br/>Success?}

    POST_SUCCESS -->|No| LOG_HTTP_ERROR[Log HTTP Error]
    LOG_HTTP_ERROR --> RETURN_FALSE[Return False]

    POST_SUCCESS -->|Yes| RETURN_TRUE[Return True]

    RETURN_FALSE --> END([End])
    RETURN_TRUE --> END

    style START fill:#28a745,color:#fff
    style END fill:#dc3545,color:#fff
    style POST fill:#7289da,color:#fff
    style RETURN_TRUE fill:#50c878,color:#fff
```

## キャッシュ管理フロー

```mermaid
flowchart TD
    subgraph "Load Cache"
        L_START([Load Request]) --> L_PATH[Generate Cache<br/>File Path]
        L_PATH --> L_EXISTS{File<br/>Exists?}
        L_EXISTS -->|No| L_NONE[Return None]
        L_EXISTS -->|Yes| L_READ[Read JSON File]
        L_READ --> L_PARSE[Parse JSON]
        L_PARSE --> L_RETURN[Return Dict]
    end

    subgraph "Save Cache"
        S_START([Save Request]) --> S_PATH[Generate Cache<br/>File Path]
        S_PATH --> S_CREATE[Create Cache Dir<br/>if Not Exists]
        S_CREATE --> S_SERIALIZE[Serialize to JSON<br/>ISO Format Dates]
        S_SERIALIZE --> S_WRITE[Write to File]
        S_WRITE --> S_END([End])
    end

    subgraph "Compare Versions"
        C_START([Compare Request]) --> C_LOAD[Load Cached<br/>Version]
        C_LOAD --> C_EXISTS{Cache<br/>Exists?}
        C_EXISTS -->|No| C_NEW[Return: New Version]
        C_EXISTS -->|Yes| C_COMPARE{Versions<br/>Match?}
        C_COMPARE -->|Yes| C_SAME[Return: No Change]
        C_COMPARE -->|No| C_NEW
    end

    style L_START fill:#28a745,color:#fff
    style S_START fill:#28a745,color:#fff
    style C_START fill:#28a745,color:#fff
    style S_END fill:#dc3545,color:#fff
    style C_NEW fill:#f39c12,color:#fff
    style C_SAME fill:#6c757d,color:#fff
```

## エラーハンドリングフロー

```mermaid
flowchart TD
    START([Error Occurs]) --> IDENTIFY{Error<br/>Type?}

    IDENTIFY -->|HTTP Error| HTTP[httpx.HTTPError]
    IDENTIFY -->|Network Error| NETWORK[Connection/Timeout]
    IDENTIFY -->|Parse Error| PARSE[JSON/XML Parse]
    IDENTIFY -->|Config Error| CONFIG[Missing Config]
    IDENTIFY -->|Other| OTHER[Generic Exception]

    HTTP --> LOG_HTTP[Log HTTP Status<br/>and URL]
    NETWORK --> LOG_NETWORK[Log Network<br/>Error Details]
    PARSE --> LOG_PARSE[Log Parse<br/>Error Details]
    CONFIG --> LOG_CONFIG[Log Missing<br/>Config Key]
    OTHER --> LOG_OTHER[Log Exception<br/>and Traceback]

    LOG_HTTP --> DECIDE{Fatal<br/>Error?}
    LOG_NETWORK --> DECIDE
    LOG_PARSE --> DECIDE
    LOG_CONFIG --> DECIDE
    LOG_OTHER --> DECIDE

    DECIDE -->|Yes| ABORT[Abort Process]
    DECIDE -->|No| FALLBACK[Use Fallback/<br/>Try Next Option]

    FALLBACK --> CONTINUE[Continue<br/>Processing]

    ABORT --> END([End])
    CONTINUE --> END

    style START fill:#dc3545,color:#fff
    style END fill:#28a745,color:#fff
    style FALLBACK fill:#ffc107,color:#000
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
        UNIFIED[{
            version: str,
            content: str,
            url: str,
            published: datetime,
            source: str
        }]
    end

    GHR_DICT --> UNIFIED
    HB_DICT --> UNIFIED

    subgraph "JSON Output (--output)"
        JSON_OUTPUT[{
            tool_name: str,
            version: str,
            content: str,
            url: str,
            color: int,
            webhook_env: str
        }]
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

## 環境変数とシークレット管理

```mermaid
flowchart TD
    subgraph "GitHub Actions"
        GH_SECRETS[GitHub Secrets<br/>Repository Settings]
        WORKFLOW[Workflow YAML<br/>Environment Config]
    end

    subgraph "Runtime Environment"
        ENV_VARS[Environment Variables<br/>Process Context]
    end

    subgraph "Application"
        CONFIG_READ[Read config.yml]
        WEBHOOK_KEY[webhook_env Key]
        GET_ENV[os.getenv]
        WEBHOOK_URL[Webhook URL]
    end

    GH_SECRETS --> |secrets.XXX| WORKFLOW
    WORKFLOW --> |env:| ENV_VARS

    CONFIG_READ --> WEBHOOK_KEY
    WEBHOOK_KEY --> GET_ENV
    ENV_VARS --> GET_ENV
    GET_ENV --> WEBHOOK_URL

    style GH_SECRETS fill:#28a745,color:#fff
    style ENV_VARS fill:#ffc107,color:#000
    style WEBHOOK_URL fill:#dc3545,color:#fff
```

## 時系列データフロー

```mermaid
gantt
    title Processing Timeline for Multiple Tools
    dateFormat X
    axisFormat %s

    section Tool 1 (Zed)
    Load Config         :0, 1s
    Fetch from GitHub   :1, 3s
    Translate           :4, 5s
    Send to Discord     :9, 2s
    Update Cache        :11, 1s

    section Tool 2 (Dia)
    Wait for Tool 1     :0, 12s
    Fetch from Homebrew :12, 2s
    Translate           :14, 5s
    Send to Discord     :19, 2s
    Update Cache        :21, 1s
```

## データサイズと制限

```mermaid
graph TD
    subgraph "Input Limits"
        ATOM[Atom Feed<br/>~100KB per feed]
        JSON[JSON API<br/>~50KB per response]
    end

    subgraph "Processing"
        PARSE[Parsing<br/>~1-2MB memory]
        TRANS[Translation<br/>~4000 chars input]
    end

    subgraph "Output Limits"
        DISCORD[Discord Embed<br/>4000 chars description]
        CACHE[Cache File<br/>~1-5KB per tool]
    end

    ATOM --> PARSE
    JSON --> PARSE
    PARSE --> TRANS
    TRANS --> DISCORD
    TRANS --> CACHE

    style ATOM fill:#4a90e2,color:#fff
    style TRANS fill:#8e44ad,color:#fff
    style DISCORD fill:#7289da,color:#fff
```
