"""Changelog source for release information."""

import re
from datetime import UTC, datetime

import httpx

from devtools_release_notifier.sources.base import ReleaseSource

VERSION_PATTERNS: dict[str, str] = {
    # Claude Code format: ## 2.0.69
    "simple": r"^## (\d+\.\d+(?:\.\d+)?(?:-[\w.]+)?)",
    # Keep a Changelog format: ## [1.0.0] - 2024-01-15
    "keepachangelog": r"^## \[([^\]]+)\](?: - (\d{4}-\d{2}-\d{2}))?",
}

HTTP_TIMEOUT_SECONDS = 10.0


class ChangelogSource(ReleaseSource):
    """Fetch release information from a CHANGELOG file."""

    def _get_pattern(self) -> re.Pattern:
        """Get compiled regex pattern for version matching.

        Returns:
            Compiled regex pattern
        """
        pattern_config = self.config.get("version_pattern", "keepachangelog")

        if pattern_config in VERSION_PATTERNS:
            pattern_str = VERSION_PATTERNS[pattern_config]
        else:
            pattern_str = pattern_config

        return re.compile(pattern_str, re.MULTILINE)

    def _parse_date(self, date_str: str | None) -> datetime:
        """Parse date string to datetime.

        Args:
            date_str: Date string in YYYY-MM-DD format or None

        Returns:
            Parsed datetime or current UTC time
        """
        if date_str:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=UTC)
            except ValueError:
                pass
        return datetime.now(UTC)

    def _extract_content(self, text: str, start_pos: int, pattern: re.Pattern) -> str:
        """Extract content between current version and next version.

        Args:
            text: Full CHANGELOG text
            start_pos: Position after version header line
            pattern: Compiled version pattern

        Returns:
            Extracted content (trimmed)
        """
        remaining_text = text[start_pos:]
        next_match = pattern.search(remaining_text)

        if next_match:
            content = remaining_text[: next_match.start()]
        else:
            content = remaining_text

        return content.strip()

    def fetch_latest_version(self) -> dict | None:
        """Fetch latest version from CHANGELOG file.

        Returns:
            Dictionary with version, content, url, published, source
            or None if failed
        """
        raw_url = self.config.get("raw_url")
        if not raw_url:
            print("✗ Changelog: raw_url not configured")
            return None

        try:
            response = httpx.get(raw_url, timeout=HTTP_TIMEOUT_SECONDS)
            response.raise_for_status()
            text = response.text

            pattern = self._get_pattern()
            match = pattern.search(text)

            if not match:
                print("✗ Changelog: No version found")
                return None

            version = match.group(1)

            date_str = None
            if match.lastindex and match.lastindex >= 2:
                date_str = match.group(2)

            published = self._parse_date(date_str)

            header_end = text.find("\n", match.end())
            if header_end == -1:
                header_end = match.end()
            else:
                header_end += 1

            content = self._extract_content(text, header_end, pattern)

            url = self.config.get("content_url") or raw_url

            return {
                "version": version,
                "content": content,
                "url": url,
                "published": published,
                "source": "changelog",
            }
        except httpx.HTTPError as e:
            print(f"✗ Changelog: HTTP error - {e}")
            return None
        except re.error as e:
            print(f"✗ Changelog: Invalid regex pattern - {e}")
            return None
