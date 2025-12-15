"""Release information models."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_serializer


class ReleaseInfo(BaseModel):
    """Release information from a source.

    Attributes:
        version: Version string (e.g., "v0.100.0")
        content: Release notes or description
        url: Release page URL
        published: Publication datetime
        source: Source type identifier
        download_url: Direct download URL (optional, mainly for Homebrew)
    """

    version: str = Field(..., description="Version string")
    content: str = Field(..., description="Release notes or description")
    url: str = Field(..., description="Release page URL")
    published: datetime = Field(..., description="Publication datetime")
    source: Literal["github_releases", "homebrew_cask", "github_commits", "changelog"] = Field(
        ..., description="Source type identifier"
    )
    download_url: str | None = Field(None, description="Direct download URL (mainly for Homebrew)")

    @field_serializer("published")
    def serialize_published(self, value: datetime) -> str:
        """Serialize published datetime to ISO format string."""
        return value.isoformat()


class CachedRelease(BaseModel):
    """Cached release information.

    Attributes:
        version: Version string
        timestamp: Cache timestamp
    """

    version: str = Field(..., description="Cached version string")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Cache timestamp"
    )

    @field_serializer("timestamp")
    def serialize_timestamp(self, value: datetime) -> str:
        """Serialize timestamp datetime to ISO format string."""
        return value.isoformat()
