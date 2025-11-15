#!/usr/bin/env python3
"""Send translated release information to Discord.

This script takes the original release data and translated content,
then sends formatted notifications to Discord webhooks.
"""

import json
import os
import sys
from datetime import UTC, datetime

import httpx


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
                "title": f"🚀 {tool_name} - {version}",
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


def main():
    """Main entry point."""
    if len(sys.argv) != 3:
        print("Usage: send_to_discord.py <releases.json> <translated_json>", file=sys.stderr)
        sys.exit(1)

    releases_file = sys.argv[1]
    translated_json = sys.argv[2]

    # Load releases data
    try:
        with open(releases_file) as f:
            releases = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error loading releases file: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse translated data
    try:
        translated = json.loads(translated_json)
    except json.JSONDecodeError as e:
        print(f"Error parsing translated JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate translated data structure
    if not isinstance(translated, list):
        print("Error: Translated data must be a JSON array", file=sys.stderr)
        sys.exit(1)

    # Create mapping of tool names to translated content
    translated_map = {}
    for item in translated:
        if not isinstance(item, dict):
            print(f"Warning: Skipping non-dict item in translated data: {item}")
            continue
        if "tool_name" not in item or "translated_content" not in item:
            print(f"Warning: Skipping item missing required fields: {item}")
            continue
        translated_map[item["tool_name"]] = item["translated_content"]

    # Send notifications
    success_count = 0
    for release in releases:
        if not isinstance(release, dict):
            print(f"Warning: Skipping non-dict release: {release}")
            continue

        tool_name = release.get("tool_name")
        if not tool_name:
            print(f"Warning: Release missing tool_name: {release}")
            continue

        # Get webhook URL from environment
        webhook_env = release.get("webhook_env", "DISCORD_WEBHOOK")
        webhook_url = os.getenv(webhook_env)

        if not webhook_url:
            print(f"⚠️  Webhook URL not found for {tool_name} ({webhook_env})")
            continue

        # Get translated content or fall back to original
        translated_content = translated_map.get(tool_name, release.get("content", ""))

        # Send to Discord
        if send_to_discord(
            webhook_url=webhook_url,
            tool_name=tool_name,
            version=release.get("version", "unknown"),
            translated_content=translated_content,
            url=release.get("url", ""),
            color=release.get("color", 5814783),
        ):
            success_count += 1

    print(f"\n✅ Successfully sent {success_count}/{len(releases)} notifications")

    # Exit with error if no notifications were sent
    if success_count == 0 and len(releases) > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
