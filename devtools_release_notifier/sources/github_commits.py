"""GitHub Commits source for release information."""

from datetime import UTC, datetime

import feedparser

from devtools_release_notifier.sources.base import ReleaseSource


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
