"""Homebrew Cask source for release information."""

from datetime import UTC, datetime

import httpx

from devtools_release_notifier.sources.base import ReleaseSource
from devtools_release_notifier.templates import render_template


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
            token = data.get("token", "unknown")
            content = render_template(t"Version: {version}\n")
            if download_url:
                content += render_template(t"Download: {download_url}\n")
            content += render_template(t"Install: `brew install --cask {token}`")

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
