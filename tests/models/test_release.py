"""Tests for release information models."""

import json
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from devtools_release_notifier.models.release import CachedRelease, ReleaseInfo


def test_release_info_github_releases():
    """Test ReleaseInfo with github_releases source."""
    published_time = datetime(2025, 1, 15, 12, 0, 0)
    release = ReleaseInfo(
        version="v0.100.0",
        content="Release notes content",
        url="https://github.com/zed-industries/zed/releases/tag/v0.100.0",
        published=published_time,
        source="github_releases",
        download_url=None,
    )
    assert release.version == "v0.100.0"
    assert release.content == "Release notes content"
    assert release.url == "https://github.com/zed-industries/zed/releases/tag/v0.100.0"
    assert release.published == published_time
    assert release.source == "github_releases"
    assert release.download_url is None


def test_release_info_homebrew_cask():
    """Test ReleaseInfo with homebrew_cask source."""
    published_time = datetime(2025, 1, 15, 12, 0, 0)
    release = ReleaseInfo(
        version="0.158.0",
        content="Homebrew Cask version info",
        url="https://zed.dev",
        published=published_time,
        source="homebrew_cask",
        download_url="https://zed.dev/api/releases/stable/0.158.0/Zed.dmg",
    )
    assert release.version == "0.158.0"
    assert release.source == "homebrew_cask"
    assert release.download_url == "https://zed.dev/api/releases/stable/0.158.0/Zed.dmg"


def test_release_info_github_commits():
    """Test ReleaseInfo with github_commits source."""
    published_time = datetime(2025, 1, 15, 12, 0, 0)
    release = ReleaseInfo(
        version="abc1234",
        content="Commit message",
        url="https://github.com/owner/repo/commit/abc1234",
        published=published_time,
        source="github_commits",
        download_url=None,
    )
    assert release.version == "abc1234"
    assert release.source == "github_commits"


def test_release_info_invalid_source():
    """Test ReleaseInfo with invalid source type."""
    published_time = datetime(2025, 1, 15, 12, 0, 0)
    with pytest.raises(ValidationError) as exc_info:
        ReleaseInfo(
            version="v1.0.0",
            content="Test",
            url="https://example.com",
            published=published_time,
            source="invalid_source",  # type: ignore[arg-type]
            download_url=None,
        )
    assert "source" in str(exc_info.value)


def test_release_info_json_serialization():
    """Test ReleaseInfo datetime JSON serialization."""
    published_time = datetime(2025, 1, 15, 12, 0, 0)
    release = ReleaseInfo(
        version="v1.0.0",
        content="Test content",
        url="https://example.com",
        published=published_time,
        source="github_releases",
        download_url=None,
    )

    # Test model_dump_json
    json_str = release.model_dump_json()
    data = json.loads(json_str)

    assert "published" in data
    assert data["published"] == "2025-01-15T12:00:00"


def test_cached_release_basic():
    """Test CachedRelease with basic data."""
    timestamp = datetime(2025, 1, 15, 12, 0, 0)
    cached = CachedRelease(
        version="v0.100.0",
        timestamp=timestamp,
    )
    assert cached.version == "v0.100.0"
    assert cached.timestamp == timestamp


def test_cached_release_default_timestamp():
    """Test CachedRelease with default timestamp."""
    cached = CachedRelease(version="v1.0.0")
    assert cached.version == "v1.0.0"
    assert isinstance(cached.timestamp, datetime)
    # Verify timestamp is recent (within last minute)
    now = datetime.now(UTC)
    time_diff = (now - cached.timestamp).total_seconds()
    assert 0 <= time_diff < 60


def test_cached_release_json_serialization():
    """Test CachedRelease datetime JSON serialization."""
    timestamp = datetime(2025, 1, 15, 12, 0, 0)
    cached = CachedRelease(
        version="v1.0.0",
        timestamp=timestamp,
    )

    # Test model_dump_json
    json_str = cached.model_dump_json()
    data = json.loads(json_str)

    assert "timestamp" in data
    assert data["timestamp"] == "2025-01-15T12:00:00"


def test_cached_release_missing_version():
    """Test CachedRelease with missing version."""
    with pytest.raises(ValidationError) as exc_info:
        CachedRelease()  # type: ignore[call-arg]
    assert "version" in str(exc_info.value)
