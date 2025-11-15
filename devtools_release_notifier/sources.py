"""Release information source classes for various platforms."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime

import feedparser
import httpx


class ReleaseSource(ABC):
    """Abstract base class for release information sources."""

    def __init__(self, config: dict):
        """Initialize with configuration.

        Args:
            config: Configuration dictionary for this source
        """
        self.config = config

    @abstractmethod
    def fetch_latest_version(self) -> dict | None:
        """Fetch latest version information.

        Returns:
            Dictionary with version info or None if failed
        """
        pass


class GitHubReleaseSource(ReleaseSource):
    """Fetch release information from GitHub Releases Atom feed."""

    def fetch_latest_version(self) -> dict | None:
        """Fetch latest release from GitHub Releases.

        Returns:
            Dictionary with version, content, url, published, source or None if failed
        """
        atom_url = self.config.get("atom_url")
        if not atom_url:
            print("✗ GitHub Releases: atom_url not configured")
            return None

        try:
            feed = feedparser.parse(atom_url)
            if not feed.entries:
                print("✗ GitHub Releases: No entries found")
                return None

            latest = feed.entries[0]

            # Try to get published time, fallback to updated time or current time
            published_time = None
            if hasattr(latest, "published_parsed") and latest.published_parsed:
                published_time = datetime(*latest.published_parsed[:6], tzinfo=UTC)
            elif hasattr(latest, "updated_parsed") and latest.updated_parsed:
                published_time = datetime(*latest.updated_parsed[:6], tzinfo=UTC)
            else:
                published_time = datetime.now(UTC)

            return {
                "version": latest.title,
                "content": latest.summary,
                "url": latest.link,
                "published": published_time,
                "source": "github_releases",
            }
        except Exception as e:
            print(f"✗ GitHub Releases: Failed to fetch - {e}")
            return None


class HomebrewCaskSource(ReleaseSource):
    """Fetch release information from Homebrew Cask JSON API."""

    def fetch_latest_version(self) -> dict | None:
        """Fetch latest version from Homebrew Cask.

        Returns:
            Dictionary with version, content, url, download_url, published, source
            or None if failed
        """
        api_url = self.config.get("api_url")
        if not api_url:
            print("✗ Homebrew Cask: api_url not configured")
            return None

        try:
            response = httpx.get(api_url, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            version = data.get("version")
            homepage = data.get("homepage")
            download_url = data.get("url")

            if not version:
                print("✗ Homebrew Cask: version not found in response")
                return None

            # Generate installation information
            content = f"Version: {version}\n"
            if download_url:
                content += f"Download: {download_url}\n"
            content += f"Install: `brew install --cask {data.get('token', 'unknown')}`"

            return {
                "version": version,
                "content": content,
                "url": homepage or "",
                "download_url": download_url or "",
                "published": datetime.now(UTC),
                "source": "homebrew_cask",
            }
        except httpx.HTTPError as e:
            print(f"✗ Homebrew Cask: HTTP error - {e}")
            return None
        except Exception as e:
            print(f"✗ Homebrew Cask: Failed to fetch - {e}")
            return None


class GitHubCommitsSource(ReleaseSource):
    """Fetch commit information from GitHub Commits Atom feed."""

    def fetch_latest_version(self) -> dict | None:
        """Fetch latest commit from GitHub.

        Returns:
            Dictionary with version, content, url, published, source or None if failed
        """
        atom_url = self.config.get("atom_url")
        if not atom_url:
            print("✗ GitHub Commits: atom_url not configured")
            return None

        try:
            feed = feedparser.parse(atom_url)
            if not feed.entries:
                print("✗ GitHub Commits: No entries found")
                return None

            latest = feed.entries[0]

            # Try to get published time, fallback to updated time or current time
            published_time = None
            if hasattr(latest, "published_parsed") and latest.published_parsed:
                published_time = datetime(*latest.published_parsed[:6], tzinfo=UTC)
            elif hasattr(latest, "updated_parsed") and latest.updated_parsed:
                published_time = datetime(*latest.updated_parsed[:6], tzinfo=UTC)
            else:
                published_time = datetime.now(UTC)

            return {
                "version": latest.title,
                "content": latest.summary,
                "url": latest.link,
                "published": published_time,
                "source": "github_commits",
            }
        except Exception as e:
            print(f"✗ GitHub Commits: Failed to fetch - {e}")
            return None
