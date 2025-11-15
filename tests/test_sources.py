"""Tests for release information sources."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import httpx
import respx

from devtools_release_notifier.sources import (
    GitHubCommitsSource,
    GitHubReleaseSource,
    HomebrewCaskSource,
)

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
