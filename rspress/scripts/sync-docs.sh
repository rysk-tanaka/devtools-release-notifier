#!/bin/bash

# docs/ から rspress/docs/ へドキュメントを同期するスクリプト

set -e

# ディレクトリパス
SOURCE_DIR="../docs"
TARGET_DIR="docs"

# GitHubリポジトリURLを取得
get_github_repo_url() {
  # 1. 環境変数を優先
  if [ -n "$GITHUB_REPO_URL" ]; then
    echo "$GITHUB_REPO_URL"
    return
  fi

  # 2. git設定から動的取得
  local remote_url
  remote_url=$(git config --get remote.origin.url 2>/dev/null || echo "")

  if [ -z "$remote_url" ]; then
    echo "❌ Error: Cannot determine GitHub repository URL" >&2
    echo "   Set GITHUB_REPO_URL environment variable or ensure git remote is configured" >&2
    exit 1
  fi

  # SSH形式 (git@github.com:user/repo.git or git@github.com-*:user/repo.git) をHTTPS形式に変換
  if [[ "$remote_url" == git@github.com* ]]; then
    # git@github.com-*:user/repo.git → user/repo.git
    # git@github.com:user/repo.git → user/repo.git
    repo_path=$(echo "$remote_url" | sed 's/^git@github\.com[^:]*://' | sed 's/\.git$//')
    remote_url="https://github.com/${repo_path}"
  # HTTPS形式 (.git を削除)
  elif [[ "$remote_url" == https://github.com/* ]]; then
    remote_url=$(echo "$remote_url" | sed 's/\.git$//')
  else
    echo "❌ Error: Unsupported remote URL format: ${remote_url}" >&2
    exit 1
  fi

  echo "${remote_url}/blob/main"
}

GITHUB_REPO=$(get_github_repo_url)

echo "📚 Syncing documentation from ${SOURCE_DIR} to ${TARGET_DIR}..."
echo "🔗 Using repository URL: ${GITHUB_REPO}"

# 事前チェック
if [ ! -d "$SOURCE_DIR" ]; then
  echo "❌ Error: Source directory '${SOURCE_DIR}' does not exist"
  exit 1
fi

if [ ! -d "$TARGET_DIR" ]; then
  echo "❌ Error: Target directory '${TARGET_DIR}' does not exist"
  exit 1
fi

# Markdownファイルの存在確認
md_count=$(find "$SOURCE_DIR" -maxdepth 1 -name "*.md" 2>/dev/null | wc -l)
if [ "$md_count" -eq 0 ]; then
  echo "❌ Error: No Markdown files found in ${SOURCE_DIR}"
  exit 1
fi

# ターゲットディレクトリのMarkdownファイルをクリーンアップ
echo "🧹 Cleaning up existing files..."
rm -f ${TARGET_DIR}/*.md

# Markdownファイルをコピー
echo "📋 Copying Markdown files..."
cp ${SOURCE_DIR}/*.md ${TARGET_DIR}/

# README.md を index.md にリネーム
if [ -f "${TARGET_DIR}/README.md" ]; then
  echo "🔄 Converting README.md to index.md..."
  mv ${TARGET_DIR}/README.md ${TARGET_DIR}/index.md
fi

# リンクを修正（相対パスからGitHub絶対URLへ）
echo "🔗 Fixing links..."
for file in ${TARGET_DIR}/*.md; do
  if [ -f "$file" ]; then
    # macOSとLinux両方で動作するsedコマンド
    # 対応拡張子ごとに置換（.md, .toml, .yml, .yaml, .json）
    if [[ "$OSTYPE" == "darwin"* ]]; then
      # macOS
      sed -i '' "s|\.\./\([A-Za-z0-9_.-]*\.md\)|${GITHUB_REPO}/\1|g" "$file"
      sed -i '' "s|\.\./\([A-Za-z0-9_.-]*\.toml\)|${GITHUB_REPO}/\1|g" "$file"
      sed -i '' "s|\.\./\([A-Za-z0-9_.-]*\.yml\)|${GITHUB_REPO}/\1|g" "$file"
      sed -i '' "s|\.\./\([A-Za-z0-9_.-]*\.yaml\)|${GITHUB_REPO}/\1|g" "$file"
      sed -i '' "s|\.\./\([A-Za-z0-9_.-]*\.json\)|${GITHUB_REPO}/\1|g" "$file"
    else
      # Linux
      sed -i "s|\.\./\([A-Za-z0-9_.-]*\.md\)|${GITHUB_REPO}/\1|g" "$file"
      sed -i "s|\.\./\([A-Za-z0-9_.-]*\.toml\)|${GITHUB_REPO}/\1|g" "$file"
      sed -i "s|\.\./\([A-Za-z0-9_.-]*\.yml\)|${GITHUB_REPO}/\1|g" "$file"
      sed -i "s|\.\./\([A-Za-z0-9_.-]*\.yaml\)|${GITHUB_REPO}/\1|g" "$file"
      sed -i "s|\.\./\([A-Za-z0-9_.-]*\.json\)|${GITHUB_REPO}/\1|g" "$file"
    fi
  fi
done

echo "✅ Documentation sync completed successfully!"
echo ""
echo "📄 Synced files:"
ls -1 ${TARGET_DIR}/*.md
