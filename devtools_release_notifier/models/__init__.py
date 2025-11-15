"""Pydantic models for devtools-release-notifier."""

from devtools_release_notifier.models.config import (
    AppConfig,
    CommonConfig,
    GitHubCommitsSourceConfig,
    GitHubReleasesSourceConfig,
    HomebrewCaskSourceConfig,
    NotificationConfig,
    SourceConfig,
    ToolConfig,
)
from devtools_release_notifier.models.discord import (
    DiscordEmbed,
    DiscordEmbedFooter,
    DiscordWebhookPayload,
)
from devtools_release_notifier.models.output import ReleaseOutput, TranslatedRelease
from devtools_release_notifier.models.release import CachedRelease, ReleaseInfo

__all__ = [
    # Config models
    "AppConfig",
    "CommonConfig",
    "GitHubCommitsSourceConfig",
    "GitHubReleasesSourceConfig",
    "HomebrewCaskSourceConfig",
    "NotificationConfig",
    "SourceConfig",
    "ToolConfig",
    # Discord models
    "DiscordEmbed",
    "DiscordEmbedFooter",
    "DiscordWebhookPayload",
    # Output models
    "ReleaseOutput",
    "TranslatedRelease",
    # Release models
    "CachedRelease",
    "ReleaseInfo",
]
