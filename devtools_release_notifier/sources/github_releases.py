"""GitHub Releases source for release information."""

import time
from datetime import UTC, datetime

import feedparser

from devtools_release_notifier.sources.base import ReleaseSource


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
                parsed_time: time.struct_time = latest.published_parsed  # type: ignore[assignment]
                published_time = datetime(*parsed_time[:6], tzinfo=UTC)
            elif hasattr(latest, "updated_parsed") and latest.updated_parsed:
                updated_time: time.struct_time = latest.updated_parsed  # type: ignore[assignment]
                published_time = datetime(*updated_time[:6], tzinfo=UTC)
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
