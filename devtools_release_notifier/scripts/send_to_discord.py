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
from pydantic import ValidationError

from devtools_release_notifier.models.output import ReleaseOutput, TranslatedRelease


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
    releases: list[ReleaseOutput], translated_map: dict[str, str]
) -> tuple[int, int, int]:
    """Send Discord notifications for all releases.

    Args:
        releases: List of releases to notify
        translated_map: Mapping of tool names to translated content

    Returns:
        Tuple of (success_count, failed_count, skipped_count)
    """
    success_count = 0
    failed_count = 0
    skipped_count = 0

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
        else:
            failed_count += 1

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
    if len(sys.argv) != 3:
        print("Usage: send_to_discord.py <releases.json> <translated_json>", file=sys.stderr)
        sys.exit(1)

    releases_file = sys.argv[1]
    translated_json = sys.argv[2]

    # Load and validate data
    releases = _load_releases(releases_file)
    translated = _parse_translations(translated_json)

    # Create mapping of tool names to translated content
    translated_map = {r.tool_name: r.translated_content for r in translated}

    # Send notifications
    success_count, failed_count, skipped_count = _send_notifications(releases, translated_map)

    # Print summary and exit
    total_releases = len(releases)
    _print_summary(success_count, failed_count, skipped_count, total_releases)
    _exit_with_status(success_count, failed_count, total_releases)


if __name__ == "__main__":
    main()
