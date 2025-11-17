# 貢献ガイド

このプロジェクトへの貢献に興味を持っていただきありがとうございます。

## 新しいツールの追加方法

このプロジェクトに新しい開発ツールの監視を追加する手順を説明します。

### 前提条件

新しいツールを追加する前に、以下を確認してください。

- ツールの公式情報源（GitHub Releases、Homebrew Caskなど）を特定済み
- ツール名（例: "Claude Code"）を決定済み
- Discord通知用の色コード（10進数、0-16777215）を決定済み

### 手順

#### 1. config.ymlへのツール追加

`config.yml`の`tools`リストに新しいツールを追加します。

例: Claude Codeの場合

```yaml
tools:
  # 既存のツール...

  - name: "Claude Code"
    enabled: true
    sources:
      - type: "github_releases"
        priority: 1
        atom_url: "https://github.com/anthropics/claude-code/releases.atom"
        owner: "anthropics"
        repo: "claude-code"
      - type: "github_commits"
        priority: 2
        atom_url: "https://github.com/anthropics/claude-code/commits/main.atom"
        owner: "anthropics"
        repo: "claude-code"
    notification:
      webhook_env: "DISCORD_WEBHOOK"
      color: 16744272
```

設定項目の説明

- `name`: ツール名（表示用）
- `enabled`: 監視の有効/無効
- `sources`: 情報源のリスト（優先度順）
  - `type`: `github_releases`, `homebrew_cask`, `github_commits`のいずれか
  - `priority`: 優先度（1が最優先、数字が小さいほど優先）
  - その他、typeに応じた必須パラメータ
- `notification`:
  - `webhook_env`: Webhook URLを格納する環境変数名
  - `color`: Discord埋め込みメッセージの色（10進数）

情報源の種類

- `github_releases`: GitHub Releasesから取得
  - 必須: `atom_url`, `owner`, `repo`
- `homebrew_cask`: Homebrew Cask APIから取得
  - 必須: `api_url`
- `github_commits`: GitHubコミットから取得
  - 必須: `atom_url`, `owner`, `repo`

#### 2. rspressドキュメントの更新

##### 2-1. ナビゲーションへの追加

`rspress/docs/releases/_meta.json`にツールを追加します（アルファベット順）。

```json
[
  "index",
  {
    "type": "dir",
    "name": "claude-code",
    "label": "Claude Code",
    "collapsible": false
  },
  {
    "type": "dir",
    "name": "dia-browser",
    "label": "Dia Browser",
    "collapsible": false
  },
  {
    "type": "dir",
    "name": "zed-editor",
    "label": "Zed Editor",
    "collapsible": false
  }
]
```

slug名のルール

- ツール名をケバブケース（小文字+ハイフン）に変換
- 例: "Claude Code" → "claude-code"

##### 2-2. リリースページのツールリスト更新

`rspress/docs/releases/index.md`の監視中ツールリストに追加します（アルファベット順）。

```markdown
## 監視中のツール

- [Claude Code](./claude-code/index.md) - AnthropicのAIペアプログラミングツール
- [Dia Browser](./dia-browser/index.md) - 高速なWebブラウザ
- [Zed Editor](./zed-editor/index.md) - モダンなコードエディタ
```

##### 2-3. トップページのツールリスト更新

`rspress/docs/index.md`の監視中ツールリストに追加します（アルファベット順）。

```markdown
## 監視中のツール

- [Claude Code](./releases/claude-code/index.md) - AnthropicのAIペアプログラミングツール
- [Dia Browser](./releases/dia-browser/index.md) - 高速なWebブラウザ
- [Zed Editor](./releases/zed-editor/index.md) - モダンなコードエディタ
```

##### 2-4. ツール専用ページの作成

`rspress/docs/releases/{tool-slug}/index.md`を新規作成します。

例: `rspress/docs/releases/claude-code/index.md`

```markdown
# Claude Code リリース情報

Claude Codeは、Anthropicが開発したAIペアプログラミングツールです。

## 最新のリリース

最新のリリース情報は、以下のページで確認できます。

## 情報源

- GitHub Releases（優先度1）
- GitHub Commits（優先度2）

## 公式リンク

- [GitHub リポジトリ](https://github.com/anthropics/claude-code)
- [公式サイト](https://claude.ai/code)
```

#### 3. 動作確認

##### ローカルでのテスト

```bash
# 依存関係のインストール（初回のみ）
uv sync

# 新しいリリースを検出（通知なし）
uv run devtools-notifier --output releases.json --no-notify

# releases.jsonの内容を確認
cat releases.json

# Discord通知のテスト（オプション）
export DISCORD_WEBHOOK="your-webhook-url"
uv run devtools-notifier
```

期待される結果

- 新しいツールのリリース情報が検出される
- `cache/{tool-slug}_version.json`が作成される
- Discord通知が正常に送信される（通知ありの場合）

##### GitHub Actionsでのテスト

1. 変更をコミット・プッシュ
2. GitHubリポジトリの「Actions」タブを開く
3. 「Check Development Tools Releases」ワークフローを選択
4. 「Run workflow」ボタンで手動実行
5. 実行結果を確認

#### 4. プルリクエストの作成

##### 変更ファイルのチェックリスト

以下のファイルが変更されていることを確認してください。

- [ ] `config.yml` - ツール設定を追加
- [ ] `rspress/docs/releases/_meta.json` - ナビゲーションに追加
- [ ] `rspress/docs/releases/index.md` - ツールリストに追加
- [ ] `rspress/docs/index.md` - トップページのツールリストに追加
- [ ] `rspress/docs/releases/{tool-slug}/index.md` - 専用ページを作成
- [ ] `cache/{tool-slug}_version.json` - キャッシュファイル（初回実行後に生成）

### 色コードの選び方

Discord埋め込みメッセージの色は、ツールのブランドカラーに合わせることを推奨します。

色コードの変換

- 16進数（例: #FF9900）から10進数に変換
- オンラインツール: <https://www.rapidtables.com/convert/color/hex-to-rgb.html>
- Pythonでの変換: `int("FF9900", 16)` → `16744272`

既存ツールの色コード例

- Zed Editor: 5814783（ブルー系）
- Dia Browser: 3447003（パープル系）
- Claude Code: 16744272（オレンジ系）
