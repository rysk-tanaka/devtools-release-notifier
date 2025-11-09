#!/bin/bash

# docs/ から rspress/docs/ へドキュメントを同期するスクリプト

set -e

# ディレクトリパス
SOURCE_DIR="../docs"
TARGET_DIR="docs"
GITHUB_REPO="https://github.com/rysk/devtools-release-notifier/blob/main"

echo "📚 Syncing documentation from ${SOURCE_DIR} to ${TARGET_DIR}..."

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
