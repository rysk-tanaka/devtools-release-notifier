"""Tests for release information sources."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import httpx
import respx

from devtools_release_notifier.sources.changelog import ChangelogSource
from devtools_release_notifier.sources.github_commits import GitHubCommitsSource
from devtools_release_notifier.sources.github_releases import GitHubReleaseSource
from devtools_release_notifier.sources.homebrew_cask import HomebrewCaskSource

# Sample Atom feed with published_parsed
ATOM_FEED_WITH_PUBLISHED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>v0.100.0</title>
    <link href="https://github.com/test/repo/releases/tag/v0.100.0"/>
    <summary>Release notes</summary>
    <published>2025-01-15T12:00:00Z</published>
  </entry>
</feed>
"""

# Sample Atom feed with only updated (no published)
ATOM_FEED_WITH_UPDATED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>v0.100.0</title>
    <link href="https://github.com/test/repo/releases/tag/v0.100.0"/>
    <summary>Release notes</summary>
    <updated>2025-01-15T12:00:00Z</updated>
  </entry>
</feed>
"""

# Empty Atom feed
EMPTY_ATOM_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
</feed>
"""

# Sample Homebrew Cask JSON
HOMEBREW_CASK_JSON = {
    "token": "zed",
    "version": "0.100.0",
    "homepage": "https://zed.dev/",
    "url": "https://zed.dev/api/releases/stable/0.100.0/Zed.dmg",
}

# Sample CHANGELOG for simple pattern (Claude Code format)
CHANGELOG_SIMPLE = """# Changelog

## 2.0.69
- Minor bugfixes

## 2.0.68
- Fixed IME support
- Fixed MCP tools bug
"""

# Sample CHANGELOG for keepachangelog pattern
CHANGELOG_KEEPACHANGELOG = """# Changelog

## [1.0.0] - 2024-01-15
### Added
- Initial release

## [0.9.0] - 2024-01-01
### Changed
- Beta improvements
"""

# Sample CHANGELOG for keepachangelog pattern without date
CHANGELOG_NO_DATE = """# Changelog

## [1.0.0]
- Initial release
"""

# Sample CHANGELOG with custom pattern
CHANGELOG_CUSTOM = """
# Version History

Version 3.2.1
* Bug fixes

Version 3.2.0
* New features
"""


class TestGitHubReleaseSource:
    """Tests for GitHubReleaseSource."""

    @patch("devtools_release_notifier.sources.github_releases.feedparser.parse")
    def test_fetch_success_with_published(self, mock_parse):
        """Test successful fetch with published_parsed."""
        config = {
            "atom_url": "https://github.com/test/repo/releases.atom",
            "owner": "test",
            "repo": "repo",
        }

        # Mock feedparser response
        mock_entry = MagicMock()
        mock_entry.title = "v0.100.0"
        mock_entry.summary = "Release notes"
        mock_entry.link = "https://github.com/test/repo/releases/tag/v0.100.0"
        mock_entry.published_parsed = (2025, 1, 15, 12, 0, 0)

        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry]
        mock_parse.return_value = mock_feed

        source = GitHubReleaseSource(config)
        result = source.fetch_latest_version()

        assert result is not None
        assert result["version"] == "v0.100.0"
        assert result["content"] == "Release notes"
        assert result["url"] == "https://github.com/test/repo/releases/tag/v0.100.0"
        assert isinstance(result["published"], datetime)
        assert result["source"] == "github_releases"

    @patch("devtools_release_notifier.sources.github_releases.feedparser.parse")
    def test_fetch_success_with_updated(self, mock_parse):
        """Test successful fetch with updated_parsed fallback."""
        config = {
            "atom_url": "https://github.com/test/repo/releases.atom",
            "owner": "test",
            "repo": "repo",
        }

        # Mock feedparser response with only updated_parsed
        mock_entry = MagicMock()
        mock_entry.title = "v0.100.0"
        mock_entry.summary = "Release notes"
        mock_entry.link = "https://github.com/test/repo/releases/tag/v0.100.0"
        mock_entry.published_parsed = None
        mock_entry.updated_parsed = (2025, 1, 15, 12, 0, 0)

        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry]
        mock_parse.return_value = mock_feed

        source = GitHubReleaseSource(config)
        result = source.fetch_latest_version()

        assert result is not None
        assert result["version"] == "v0.100.0"
        assert isinstance(result["published"], datetime)
        assert result["source"] == "github_releases"

    @patch("devtools_release_notifier.sources.github_releases.feedparser.parse")
    def test_fetch_empty_feed(self, mock_parse):
        """Test fetch with empty feed."""
        config = {
            "atom_url": "https://github.com/test/repo/releases.atom",
            "owner": "test",
            "repo": "repo",
        }

        # Mock empty feed
        mock_feed = MagicMock()
        mock_feed.entries = []
        mock_parse.return_value = mock_feed

        source = GitHubReleaseSource(config)
        result = source.fetch_latest_version()

        assert result is None

    def test_fetch_missing_atom_url(self):
        """Test fetch with missing atom_url."""
        config = {"owner": "test", "repo": "repo"}

        source = GitHubReleaseSource(config)
        result = source.fetch_latest_version()

        assert result is None


class TestHomebrewCaskSource:
    """Tests for HomebrewCaskSource."""

    @respx.mock
    def test_fetch_success(self):
        """Test successful fetch from Homebrew Cask API."""
        config = {"api_url": "https://formulae.brew.sh/api/cask/zed.json"}

        # Mock the API response
        respx.get("https://formulae.brew.sh/api/cask/zed.json").mock(
            return_value=httpx.Response(200, json=HOMEBREW_CASK_JSON)
        )

        source = HomebrewCaskSource(config)
        result = source.fetch_latest_version()

        assert result is not None
        assert result["version"] == "0.100.0"
        assert "Version: 0.100.0" in result["content"]
        assert "Download: https://zed.dev/api/releases/stable/0.100.0/Zed.dmg" in result["content"]
        assert "Install: `brew install --cask zed`" in result["content"]
        assert result["url"] == "https://zed.dev/"
        assert result["download_url"] == "https://zed.dev/api/releases/stable/0.100.0/Zed.dmg"
        assert isinstance(result["published"], datetime)
        assert result["source"] == "homebrew_cask"

    @respx.mock
    def test_fetch_http_error(self):
        """Test fetch with HTTP error."""
        config = {"api_url": "https://formulae.brew.sh/api/cask/nonexistent.json"}

        # Mock 404 error
        respx.get("https://formulae.brew.sh/api/cask/nonexistent.json").mock(
            return_value=httpx.Response(404)
        )

        source = HomebrewCaskSource(config)
        result = source.fetch_latest_version()

        assert result is None

    @respx.mock
    def test_fetch_missing_version(self):
        """Test fetch with missing version in response."""
        config = {"api_url": "https://formulae.brew.sh/api/cask/invalid.json"}

        # Mock response without version
        respx.get("https://formulae.brew.sh/api/cask/invalid.json").mock(
            return_value=httpx.Response(
                200, json={"token": "invalid", "homepage": "https://example.com"}
            )
        )

        source = HomebrewCaskSource(config)
        result = source.fetch_latest_version()

        assert result is None

    def test_fetch_missing_api_url(self):
        """Test fetch with missing api_url."""
        config = {}

        source = HomebrewCaskSource(config)
        result = source.fetch_latest_version()

        assert result is None


class TestGitHubCommitsSource:
    """Tests for GitHubCommitsSource."""

    @patch("devtools_release_notifier.sources.github_commits.feedparser.parse")
    def test_fetch_success(self, mock_parse):
        """Test successful fetch from GitHub Commits."""
        config = {
            "atom_url": "https://github.com/test/repo/commits/main.atom",
            "owner": "test",
            "repo": "repo",
        }

        # Mock feedparser response
        mock_entry = MagicMock()
        mock_entry.title = "v0.100.0"
        mock_entry.summary = "Release notes"
        mock_entry.link = "https://github.com/test/repo/releases/tag/v0.100.0"
        mock_entry.published_parsed = (2025, 1, 15, 12, 0, 0)

        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry]
        mock_parse.return_value = mock_feed

        source = GitHubCommitsSource(config)
        result = source.fetch_latest_version()

        assert result is not None
        assert result["version"] == "v0.100.0"
        assert result["content"] == "Release notes"
        assert result["url"] == "https://github.com/test/repo/releases/tag/v0.100.0"
        assert isinstance(result["published"], datetime)
        assert result["source"] == "github_commits"

    @patch("devtools_release_notifier.sources.github_commits.feedparser.parse")
    def test_fetch_empty_feed(self, mock_parse):
        """Test fetch with empty feed."""
        config = {
            "atom_url": "https://github.com/test/repo/commits/main.atom",
            "owner": "test",
            "repo": "repo",
        }

        # Mock empty feed
        mock_feed = MagicMock()
        mock_feed.entries = []
        mock_parse.return_value = mock_feed

        source = GitHubCommitsSource(config)
        result = source.fetch_latest_version()

        assert result is None

    def test_fetch_missing_atom_url(self):
        """Test fetch with missing atom_url."""
        config = {"owner": "test", "repo": "repo"}

        source = GitHubCommitsSource(config)
        result = source.fetch_latest_version()

        assert result is None


class TestChangelogSource:
    """Tests for ChangelogSource."""

    @respx.mock
    def test_fetch_simple_pattern(self):
        """Test fetch with simple version pattern."""
        config = {
            "raw_url": "https://example.com/CHANGELOG.md",
            "version_pattern": "simple",
        }
        respx.get(config["raw_url"]).mock(return_value=httpx.Response(200, text=CHANGELOG_SIMPLE))

        source = ChangelogSource(config)
        result = source.fetch_latest_version()

        assert result is not None
        assert result["version"] == "2.0.69"
        assert "Minor bugfixes" in result["content"]
        assert "2.0.68" not in result["content"]
        assert result["source"] == "changelog"

    @respx.mock
    def test_fetch_keepachangelog_pattern(self):
        """Test fetch with keepachangelog pattern."""
        config = {
            "raw_url": "https://example.com/CHANGELOG.md",
            "version_pattern": "keepachangelog",
        }
        respx.get(config["raw_url"]).mock(
            return_value=httpx.Response(200, text=CHANGELOG_KEEPACHANGELOG)
        )

        source = ChangelogSource(config)
        result = source.fetch_latest_version()

        assert result is not None
        assert result["version"] == "1.0.0"
        assert "Initial release" in result["content"]
        assert result["published"].year == 2024
        assert result["published"].month == 1
        assert result["published"].day == 15

    @respx.mock
    def test_fetch_no_date_uses_current_time(self):
        """Test that missing date falls back to current time."""
        config = {
            "raw_url": "https://example.com/CHANGELOG.md",
            "version_pattern": "keepachangelog",
        }
        respx.get(config["raw_url"]).mock(return_value=httpx.Response(200, text=CHANGELOG_NO_DATE))

        source = ChangelogSource(config)
        result = source.fetch_latest_version()

        assert result is not None
        assert result["version"] == "1.0.0"
        assert isinstance(result["published"], datetime)

    @respx.mock
    def test_fetch_custom_pattern(self):
        """Test fetch with custom regex pattern."""
        config = {
            "raw_url": "https://example.com/CHANGELOG.md",
            "version_pattern": r"^Version (\d+\.\d+\.\d+)",
        }
        respx.get(config["raw_url"]).mock(return_value=httpx.Response(200, text=CHANGELOG_CUSTOM))

        source = ChangelogSource(config)
        result = source.fetch_latest_version()

        assert result is not None
        assert result["version"] == "3.2.1"

    @respx.mock
    def test_fetch_with_content_url(self):
        """Test that content_url is used for url field."""
        config = {
            "raw_url": "https://raw.githubusercontent.com/org/repo/main/CHANGELOG.md",
            "content_url": "https://github.com/org/repo/blob/main/CHANGELOG.md",
            "version_pattern": "simple",
        }
        respx.get(config["raw_url"]).mock(return_value=httpx.Response(200, text=CHANGELOG_SIMPLE))

        source = ChangelogSource(config)
        result = source.fetch_latest_version()

        assert result is not None
        assert result["url"] == config["content_url"]

    @respx.mock
    def test_fetch_http_error(self):
        """Test fetch with HTTP error."""
        config = {"raw_url": "https://example.com/CHANGELOG.md"}
        respx.get(config["raw_url"]).mock(return_value=httpx.Response(404))

        source = ChangelogSource(config)
        result = source.fetch_latest_version()

        assert result is None

    def test_fetch_missing_raw_url(self):
        """Test fetch with missing raw_url."""
        config = {}

        source = ChangelogSource(config)
        result = source.fetch_latest_version()

        assert result is None

    @respx.mock
    def test_fetch_invalid_regex(self):
        """Test fetch with invalid custom regex."""
        config = {
            "raw_url": "https://example.com/CHANGELOG.md",
            "version_pattern": "[invalid(regex",
        }
        respx.get(config["raw_url"]).mock(return_value=httpx.Response(200, text=CHANGELOG_SIMPLE))

        source = ChangelogSource(config)
        result = source.fetch_latest_version()

        assert result is None

    @respx.mock
    def test_fetch_no_version_found(self):
        """Test fetch when no version matches."""
        config = {
            "raw_url": "https://example.com/CHANGELOG.md",
            "version_pattern": "simple",
        }
        respx.get(config["raw_url"]).mock(
            return_value=httpx.Response(200, text="# Just a header\n\nNo versions here.")
        )

        source = ChangelogSource(config)
        result = source.fetch_latest_version()

        assert result is None
