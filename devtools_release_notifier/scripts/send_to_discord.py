#!/usr/bin/env python3
"""Send translated release information to Discord.

This script takes the original release data and translated content,
then sends formatted notifications to Discord webhooks.
It also saves the notification content as Markdown files for rspress documentation.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import httpx
from pydantic import ValidationError

from devtools_release_notifier.models.output import ReleaseOutput, TranslatedRelease
from devtools_release_notifier.templates import render_template


def send_to_discord(
    webhook_url: str,
    tool_name: str,
    version: str,
    translated_content: str,
    url: str,
    color: int,
) -> bool:
    """Send notification to Discord webhook.

    Args:
        webhook_url: Discord webhook URL
        tool_name: Tool name
        version: Version string
        translated_content: Translated release notes
        url: Release URL
        color: Embed color (RGB integer)

    Returns:
        True if successful, False otherwise
    """
    # Truncate content to Discord's limit
    content = translated_content[:4000]

    # Create Discord embed payload
    payload = {
        "embeds": [
            {
                "title": render_template(t"🚀 {tool_name} - {version}"),
                "description": content,
                "url": url,
                "color": color,
                "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "footer": {"text": "devtools-release-notifier"},
            }
        ]
    }

    try:
        response = httpx.post(webhook_url, json=payload, timeout=10.0)
        response.raise_for_status()
        print(f"✓ Sent notification for {tool_name}")
        return True
    except httpx.HTTPError as e:
        print(f"✗ Failed to send notification for {tool_name}: {e}")
        return False


def _escape_yaml_string(value: str) -> str:
    """Escape double quotes in a string for YAML frontmatter.

    Args:
        value: String value that may contain double quotes

    Returns:
        String with double quotes replaced by single quotes
    """
    return value.replace('"', "'")


def _slugify_tool_name(tool_name: str) -> str:
    """Convert tool name to slug format.

    Args:
        tool_name: Tool name (e.g., "Zed Editor")

    Returns:
        Slug format (e.g., "zed-editor")
    """
    return tool_name.lower().replace(" ", "-")


def save_markdown_log(
    markdown_dir: str,
    tool_name: str,
    version: str,
    translated_content: str,
    url: str,
    timestamp: datetime,
) -> bool:
    """Save notification content as Markdown file.

    Args:
        markdown_dir: Base directory for Markdown files (e.g., "rspress/docs/releases")
        tool_name: Tool name
        version: Version string
        translated_content: Translated release notes
        url: Release URL
        timestamp: Notification timestamp

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create tool-specific directory
        tool_slug = _slugify_tool_name(tool_name)
        tool_dir = Path(markdown_dir) / tool_slug
        tool_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename from timestamp (YYYY-MM-DD.md)
        filename = timestamp.strftime("%Y-%m-%d.md")
        file_path = tool_dir / filename

        # Escape version string for YAML frontmatter (may contain double quotes)
        escaped_version = _escape_yaml_string(version)

        # Create frontmatter and content
        frontmatter = render_template(
            t"""---
title: "{tool_name} - {escaped_version}"
date: "{timestamp.strftime("%Y-%m-%d")}"
version: "{escaped_version}"
url: "{url}"
---

# {tool_name} - {version}

リリース日: {timestamp.strftime("%Y年%m月%d日")}

バージョン: {version}

リリースURL: [{url}]({url})

## リリースノート

{translated_content}

---

*このドキュメントは自動生成されました*
"""
        )

        # Write to file
        file_path.write_text(frontmatter, encoding="utf-8")
        print(f"✓ Saved Markdown log for {tool_name}: {file_path}")
        return True

    except (OSError, ValueError) as e:
        print(f"✗ Failed to save Markdown log for {tool_name}: {e}")
        return False


def _extract_title_from_markdown(file_path: Path) -> str | None:
    """Extract title from Markdown frontmatter.

    Args:
        file_path: Path to Markdown file

    Returns:
        Title string or None if not found
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        match = re.search(r'^title:\s*"(.+)"', content, re.MULTILINE)
        if match:
            return match.group(1)
        return None
    except (OSError, ValueError):
        return None


def _get_tool_links(base_dir: Path) -> list[str]:
    """Generate tool filter links dynamically from directory structure.

    Args:
        base_dir: Base directory containing tool subdirectories

    Returns:
        List of Markdown links to tool index pages
    """
    tool_links = []
    for tool_dir in sorted(base_dir.iterdir()):
        if not tool_dir.is_dir() or tool_dir.name.startswith("_") or tool_dir.name == "index.md":
            continue

        # Convert kebab-case to Title Case (e.g., "claude-code" -> "Claude Code")
        display_name = " ".join(word.capitalize() for word in tool_dir.name.split("-"))
        tool_links.append(f"- [{display_name}](./{tool_dir.name}/index.md)")

    return tool_links


def update_releases_index(markdown_dir: str, max_entries: int = 15) -> bool:
    """Update releases/index.md with latest release entries.

    Args:
        markdown_dir: Base directory for Markdown files (e.g., "rspress/docs/releases")
        max_entries: Maximum number of entries to keep (default: 15)

    Returns:
        True if successful, False otherwise
    """
    try:
        base_dir = Path(markdown_dir)
        index_path = base_dir / "index.md"

        # Collect all release Markdown files (YYYY-MM-DD.md)
        release_files: list[tuple[str, Path, str]] = []
        for tool_dir in base_dir.iterdir():
            if not tool_dir.is_dir() or tool_dir.name.startswith("_"):
                continue

            for md_file in tool_dir.glob("20*.md"):
                # Extract date from filename (YYYY-MM-DD.md)
                date_match = re.match(r"(\d{4}-\d{2}-\d{2})\.md", md_file.name)
                if date_match:
                    date_str = date_match.group(1)
                    # Extract title from frontmatter
                    title = _extract_title_from_markdown(md_file)
                    if title:
                        # Remove "Tool Name - " prefix from title
                        title_parts = title.split(" - ", 1)
                        short_title = title_parts[1] if len(title_parts) > 1 else title
                        release_files.append((date_str, md_file, short_title))

        # Sort by date (descending) and limit to max_entries
        release_files.sort(key=lambda x: x[0], reverse=True)
        release_files = release_files[:max_entries]

        # Group by date
        releases_by_date: dict[str, list[tuple[Path, str]]] = defaultdict(list)
        for date_str, file_path, title in release_files:
            releases_by_date[date_str].append((file_path, title))

        # Generate tool filter links dynamically
        tool_links = _get_tool_links(base_dir)

        # Generate index.md content
        content_lines = [
            "# 最新のリリース情報",
            "",
            "全ツールの最新リリース情報を時系列で表示しています。",
            "",
            "## ツール別フィルタ",
            "",
        ]
        content_lines.extend(tool_links)
        content_lines.extend(
            [
                "",
                "## リリース一覧",
                "",
            ]
        )

        # Add release entries grouped by date (already sorted descending)
        for date_str in sorted(releases_by_date.keys(), reverse=True):
            content_lines.append(f"### {date_str}")
            content_lines.append("")

            # Sort entries within the same date alphabetically by title
            entries = sorted(releases_by_date[date_str], key=lambda x: x[1])
            for file_path, title in entries:
                # Generate relative path from index.md
                rel_path = file_path.relative_to(base_dir)
                content_lines.append(f"- [{title}](./{rel_path})")

            content_lines.append("")

        # Write to index.md
        index_path.write_text("\n".join(content_lines), encoding="utf-8")
        print(f"✓ Updated releases index: {index_path}")
        return True

    except (OSError, ValueError) as e:
        print(f"✗ Failed to update releases index: {e}")
        return False


def _load_releases(file_path: str) -> list[ReleaseOutput]:
    """Load and validate releases data from JSON file.

    Args:
        file_path: Path to releases JSON file

    Returns:
        List of ReleaseOutput objects

    Raises:
        SystemExit: If file cannot be loaded or validation fails
    """
    try:
        with open(file_path) as f:
            releases_data = json.load(f)
        if not isinstance(releases_data, list):
            print("Error: Releases data must be a JSON array", file=sys.stderr)
            sys.exit(1)
        return [ReleaseOutput(**item) for item in releases_data]
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error loading releases file: {e}", file=sys.stderr)
        sys.exit(1)
    except ValidationError as e:
        print(f"Error: Invalid releases data format: {e}", file=sys.stderr)
        sys.exit(1)


def _parse_translations(json_str: str) -> list[TranslatedRelease]:
    """Parse and validate translated data from JSON string.

    Args:
        json_str: JSON string containing translated data

    Returns:
        List of TranslatedRelease objects

    Raises:
        SystemExit: If JSON cannot be parsed or validation fails
    """
    try:
        translated_data = json.loads(json_str)
        if not isinstance(translated_data, list):
            print("Error: Translated data must be a JSON array", file=sys.stderr)
            sys.exit(1)
        return [TranslatedRelease(**item) for item in translated_data]
    except json.JSONDecodeError as e:
        print(f"Error parsing translated JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except ValidationError as e:
        print(f"Error: Invalid translated data format: {e}", file=sys.stderr)
        sys.exit(1)


def _send_notifications(
    releases: list[ReleaseOutput], translated_map: dict[str, str], markdown_dir: str | None = None
) -> tuple[int, int, int]:
    """Send Discord notifications for all releases.

    Args:
        releases: List of releases to notify
        translated_map: Mapping of tool names to translated content
        markdown_dir: Base directory for Markdown files (optional)

    Returns:
        Tuple of (success_count, failed_count, skipped_count)
    """
    success_count = 0
    failed_count = 0
    skipped_count = 0
    timestamp = datetime.now(UTC)
    markdown_saved = False

    for release in releases:
        # Get webhook URL from environment
        webhook_url = os.getenv(release.webhook_env)

        if not webhook_url:
            print(f"⚠️  Webhook URL not found for {release.tool_name} ({release.webhook_env})")
            skipped_count += 1
            continue

        # Get translated content or fall back to original
        translated_content = translated_map.get(release.tool_name, release.content)

        # Send to Discord
        if send_to_discord(
            webhook_url=webhook_url,
            tool_name=release.tool_name,
            version=release.version,
            translated_content=translated_content,
            url=release.url,
            color=release.color,
        ):
            success_count += 1

            # Save Markdown log if directory is specified
            if markdown_dir:
                if save_markdown_log(
                    markdown_dir=markdown_dir,
                    tool_name=release.tool_name,
                    version=release.version,
                    translated_content=translated_content,
                    url=release.url,
                    timestamp=timestamp,
                ):
                    markdown_saved = True
        else:
            failed_count += 1

    # Update releases/index.md if any Markdown logs were saved
    if markdown_saved and markdown_dir:
        update_releases_index(markdown_dir)

    return success_count, failed_count, skipped_count


def _print_summary(success_count: int, failed_count: int, skipped_count: int, total: int):
    """Print notification summary.

    Args:
        success_count: Number of successful notifications
        failed_count: Number of failed notifications
        skipped_count: Number of skipped notifications
        total: Total number of releases
    """
    print("\n📊 Notification Summary:")
    print(f"  ✅ Success: {success_count}/{total}")
    if failed_count > 0:
        print(f"  ✗ Failed:  {failed_count}/{total}")
    if skipped_count > 0:
        print(f"  ⏭️  Skipped: {skipped_count}/{total}")


def _exit_with_status(success_count: int, failed_count: int, total: int):
    """Exit with appropriate status code based on notification results.

    Args:
        success_count: Number of successful notifications
        failed_count: Number of failed notifications
        total: Total number of releases

    Raises:
        SystemExit: Always exits with appropriate code
    """
    if success_count == 0 and total > 0:
        # All failed
        print("\n❌ All notifications failed")
        sys.exit(1)
    elif failed_count > 0:
        # Partial failure - exit with warning code
        print(f"\n⚠️  Partial failure: {failed_count} notification(s) failed")
        sys.exit(2)
    else:
        # All successful
        print("\n✅ All notifications sent successfully")
        sys.exit(0)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Send translated release information to Discord and save as Markdown"
    )
    parser.add_argument("releases_file", help="Path to releases.json file")
    parser.add_argument("translated_json", help="JSON string containing translated data")
    parser.add_argument(
        "--markdown-dir",
        default="rspress/docs/releases",
        help="Base directory for Markdown files (default: rspress/docs/releases)",
    )

    args = parser.parse_args()

    # Load and validate data
    releases = _load_releases(args.releases_file)
    translated = _parse_translations(args.translated_json)

    # Create mapping of tool names to translated content
    translated_map = {r.tool_name: r.translated_content for r in translated}

    # Send notifications and save Markdown logs
    success_count, failed_count, skipped_count = _send_notifications(
        releases, translated_map, markdown_dir=args.markdown_dir
    )

    # Print summary and exit
    total_releases = len(releases)
    _print_summary(success_count, failed_count, skipped_count, total_releases)
    _exit_with_status(success_count, failed_count, total_releases)


if __name__ == "__main__":
    main()
