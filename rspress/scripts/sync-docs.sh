#!/bin/bash

# docs/ から rspress/docs/ へドキュメントを同期するスクリプト

set -e

# ディレクトリパス
SOURCE_DIR="../docs"
TARGET_DIR="docs"

# GitHubリポジトリURLを動的に取得
get_github_repo_url() {
  local remote_url
  remote_url=$(git config --get remote.origin.url 2>/dev/null || echo "")

  if [ -z "$remote_url" ]; then
    # フォールバック: git設定から取得できない場合
    echo "https://github.com/rysk/devtools-release-notifier/blob/main"
    return
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
    if [[ "$OSTYPE" == "darwin"* ]]; then
      # macOS
      sed -i '' "s|\.\./README\.md|${GITHUB_REPO}/README.md|g" "$file"
      sed -i '' "s|\.\./CLAUDE\.md|${GITHUB_REPO}/CLAUDE.md|g" "$file"
      sed -i '' "s|\.\./pyproject\.toml|${GITHUB_REPO}/pyproject.toml|g" "$file"
      sed -i '' "s|\.\./config\.yml|${GITHUB_REPO}/config.yml|g" "$file"
    else
      # Linux
      sed -i "s|\.\./README\.md|${GITHUB_REPO}/README.md|g" "$file"
      sed -i "s|\.\./CLAUDE\.md|${GITHUB_REPO}/CLAUDE.md|g" "$file"
      sed -i "s|\.\./pyproject\.toml|${GITHUB_REPO}/pyproject.toml|g" "$file"
      sed -i "s|\.\./config\.yml|${GITHUB_REPO}/config.yml|g" "$file"
    fi
  fi
done

echo "✅ Documentation sync completed successfully!"
echo ""
echo "📄 Synced files:"
ls -1 ${TARGET_DIR}/*.md
