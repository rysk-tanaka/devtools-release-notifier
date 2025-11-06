# データフロー

devtools-release-notifierのデータフロー図です。

## 全体のデータフロー

```mermaid
flowchart TD
    START([Start]) --> LOAD_CONFIG[Load config.yml]
    LOAD_CONFIG --> INIT[Initialize Components<br/>Translator, DiscordNotifier]

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

    COMPARE -->|Yes| TRANSLATE[Translate & Summarize<br/>with Claude API]

    TRANSLATE --> TRANSLATE_SUCCESS{Translation<br/>Success?}
    TRANSLATE_SUCCESS -->|No| FALLBACK[Use Original<br/>Content]
    TRANSLATE_SUCCESS -->|Yes| TRANSLATED[Use Translated<br/>Content]

    FALLBACK --> NOTIFY
    TRANSLATED --> NOTIFY[Send Discord<br/>Notification]

    NOTIFY --> NOTIFY_SUCCESS{Notification<br/>Success?}
    NOTIFY_SUCCESS -->|No| ERR_LOG[Log Error]
    NOTIFY_SUCCESS -->|Yes| SUCCESS_LOG[Log Success]

    ERR_LOG --> UPDATE_CACHE
    SUCCESS_LOG --> UPDATE_CACHE[Update Cache<br/>Save New Version]

    UPDATE_CACHE --> LOOP_END

    LOOP_END --> LOOP_START

    LOOP_START -->|No More Tools| END([End])

    style START fill:#28a745,color:#fff
    style END fill:#dc3545,color:#fff
    style FETCH fill:#4a90e2,color:#fff
    style TRANSLATE fill:#8e44ad,color:#fff
    style NOTIFY fill:#7289da,color:#fff
    style UPDATE_CACHE fill:#f39c12,color:#fff
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

## 翻訳フロー

```mermaid
flowchart TD
    START([Translate Request]) --> CHECK_SERVICE{Translation<br/>Service<br/>Enabled?}

    CHECK_SERVICE -->|No| RETURN_ORIGINAL[Return Original<br/>Content]
    RETURN_ORIGINAL --> END

    CHECK_SERVICE -->|Yes| CHECK_TOKEN{OAuth Token<br/>Available?}

    CHECK_TOKEN -->|No| RETURN_ORIGINAL

    CHECK_TOKEN -->|Yes| BUILD_PROMPT[Build Translation<br/>Prompt]

    BUILD_PROMPT --> REQUEST[HTTP POST to<br/>Claude API]

    REQUEST --> TIMEOUT{Request<br/>Success?}

    TIMEOUT -->|No| LOG_ERROR[Log HTTP Error]
    LOG_ERROR --> RETURN_ORIGINAL

    TIMEOUT -->|Yes| PARSE[Parse JSON<br/>Response]

    PARSE --> EXTRACT[Extract Translated<br/>Content]

    EXTRACT --> RETURN_TRANSLATED[Return Translated<br/>Content]

    RETURN_TRANSLATED --> END([End])

    style START fill:#28a745,color:#fff
    style END fill:#dc3545,color:#fff
    style REQUEST fill:#8e44ad,color:#fff
    style RETURN_TRANSLATED fill:#50c878,color:#fff
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

    subgraph "Translation"
        TRANS_IN[Original Content<br/>English]
        TRANS_OUT[Translated Content<br/>Japanese]

        TRANS_IN --> |Claude API| TRANS_OUT
    end

    UNIFIED --> TRANS_IN

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

    TRANS_OUT --> DISCORD_EMBED

    style UNIFIED fill:#4a90e2,color:#fff
    style TRANS_OUT fill:#8e44ad,color:#fff
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
