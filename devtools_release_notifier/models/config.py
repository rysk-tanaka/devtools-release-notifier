"""Configuration models."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class GitHubReleasesSourceConfig(BaseModel):
    """GitHub Releases source configuration.

    Attributes:
        type: Source type identifier
        priority: Priority (lower number = higher priority)
        owner: GitHub repository owner
        repo: GitHub repository name
        atom_url: Atom feed URL
    """

    type: Literal["github_releases"] = Field(..., description="Source type")
    priority: int = Field(..., ge=1, description="Priority (lower is higher)")
    owner: str = Field(..., description="GitHub repository owner")
    repo: str = Field(..., description="GitHub repository name")
    atom_url: str = Field(..., description="Atom feed URL")


class HomebrewCaskSourceConfig(BaseModel):
    """Homebrew Cask source configuration.

    Attributes:
        type: Source type identifier
        priority: Priority (lower number = higher priority)
        api_url: Homebrew API URL
        atom_url: Atom feed URL (optional)
    """

    type: Literal["homebrew_cask"] = Field(..., description="Source type")
    priority: int = Field(..., ge=1, description="Priority (lower is higher)")
    api_url: str = Field(..., description="Homebrew API URL")
    atom_url: str | None = Field(None, description="Atom feed URL (optional)")


class GitHubCommitsSourceConfig(BaseModel):
    """GitHub Commits source configuration.

    Attributes:
        type: Source type identifier
        priority: Priority (lower number = higher priority)
        owner: GitHub repository owner
        repo: GitHub repository name
        atom_url: Atom feed URL
    """

    type: Literal["github_commits"] = Field(..., description="Source type")
    priority: int = Field(..., ge=1, description="Priority (lower is higher)")
    owner: str = Field(..., description="GitHub repository owner")
    repo: str = Field(..., description="GitHub repository name")
    atom_url: str = Field(..., description="Atom feed URL")


SourceConfig = GitHubReleasesSourceConfig | HomebrewCaskSourceConfig | GitHubCommitsSourceConfig


class NotificationConfig(BaseModel):
    """Discord notification configuration.

    Attributes:
        webhook_env: Environment variable name for webhook URL
        color: Discord embed color (integer)
    """

    webhook_env: str = Field(
        default="DISCORD_WEBHOOK",
        description="Environment variable name for webhook URL",
    )
    color: int = Field(..., ge=0, le=16777215, description="Discord embed color (0-16777215)")


class ToolConfig(BaseModel):
    """Tool configuration.

    Attributes:
        name: Tool name
        enabled: Whether this tool is enabled
        sources: List of source configurations
        notification: Discord notification configuration
    """

    name: str = Field(..., description="Tool name")
    enabled: bool = Field(default=True, description="Whether this tool is enabled")
    sources: list[SourceConfig] = Field(..., description="Source configurations")
    notification: NotificationConfig = Field(..., description="Notification configuration")

    @field_validator("sources")
    @classmethod
    def validate_sources(cls, v: list[SourceConfig]) -> list[SourceConfig]:
        """Validate that sources list is not empty."""
        if not v:
            raise ValueError("At least one source must be configured")
        return v


class CommonConfig(BaseModel):
    """Common configuration.

    Attributes:
        check_interval_hours: Check interval in hours
        cache_directory: Cache directory path
    """

    check_interval_hours: int = Field(default=6, ge=1, description="Check interval in hours")
    cache_directory: str = Field(default="./cache", description="Cache directory path")


class AppConfig(BaseModel):
    """Application configuration.

    Attributes:
        tools: List of tool configurations
        common: Common configuration
    """

    tools: list[ToolConfig] = Field(..., description="Tool configurations")
    common: CommonConfig = Field(default_factory=CommonConfig, description="Common configuration")

    @field_validator("tools")
    @classmethod
    def validate_tools(cls, v: list[ToolConfig]) -> list[ToolConfig]:
        """Validate that tools list is not empty."""
        if not v:
            raise ValueError("At least one tool must be configured")
        return v
