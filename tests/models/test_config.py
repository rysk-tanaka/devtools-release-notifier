"""Tests for configuration models."""

import pytest
from pydantic import ValidationError

from devtools_release_notifier.models.config import (
    AppConfig,
    CommonConfig,
    GitHubCommitsSourceConfig,
    GitHubReleasesSourceConfig,
    HomebrewCaskSourceConfig,
    NotificationConfig,
    ToolConfig,
)

# Constants
MIN_PRIORITY = 1
DEFAULT_CHECK_INTERVAL_HOURS = 6
DEFAULT_CACHE_DIRECTORY = "./cache"
DEFAULT_WEBHOOK_ENV = "DISCORD_WEBHOOK"
MIN_COLOR = 0
MAX_COLOR = 16777215
VALID_COLOR = 5814783


def test_github_releases_source_config_valid():
    """Test GitHubReleasesSourceConfig with valid data."""
    config = GitHubReleasesSourceConfig(
        type="github_releases",
        priority=1,
        owner="zed-industries",
        repo="zed",
        atom_url="https://github.com/zed-industries/zed/releases.atom",
    )
    assert config.type == "github_releases"
    assert config.priority == 1
    assert config.owner == "zed-industries"
    assert config.repo == "zed"


def test_github_releases_source_config_invalid_priority():
    """Test GitHubReleasesSourceConfig with invalid priority."""
    with pytest.raises(ValidationError) as exc_info:
        GitHubReleasesSourceConfig(
            type="github_releases",
            priority=0,
            owner="zed-industries",
            repo="zed",
            atom_url="https://github.com/zed-industries/zed/releases.atom",
        )
    assert "priority" in str(exc_info.value)


def test_homebrew_cask_source_config_valid():
    """Test HomebrewCaskSourceConfig with valid data."""
    config = HomebrewCaskSourceConfig(
        type="homebrew_cask",
        priority=2,
        api_url="https://formulae.brew.sh/api/cask/zed.json",
        atom_url=None,
    )
    assert config.type == "homebrew_cask"
    assert config.priority == 2
    assert config.atom_url is None


def test_homebrew_cask_source_config_with_atom_url():
    """Test HomebrewCaskSourceConfig with optional atom_url."""
    config = HomebrewCaskSourceConfig(
        type="homebrew_cask",
        priority=1,
        api_url="https://formulae.brew.sh/api/cask/dia.json",
        atom_url="https://github.com/Homebrew/homebrew-cask/commits/master/Casks/d/dia.rb.atom",
    )
    assert (
        config.atom_url
        == "https://github.com/Homebrew/homebrew-cask/commits/master/Casks/d/dia.rb.atom"
    )


def test_github_commits_source_config_valid():
    """Test GitHubCommitsSourceConfig with valid data."""
    config = GitHubCommitsSourceConfig(
        type="github_commits",
        priority=2,
        owner="blahaj-app",
        repo="Dia",
        atom_url="https://github.com/blahaj-app/Dia/commits/main.atom",
    )
    assert config.type == "github_commits"
    assert config.priority == 2


def test_notification_config_valid():
    """Test NotificationConfig with valid data."""
    config = NotificationConfig(
        webhook_env="DISCORD_WEBHOOK_ZED",
        color=VALID_COLOR,
    )
    assert config.webhook_env == "DISCORD_WEBHOOK_ZED"
    assert config.color == VALID_COLOR


def test_notification_config_default_webhook_env():
    """Test NotificationConfig with default webhook_env."""
    config = NotificationConfig(color=VALID_COLOR)
    assert config.webhook_env == DEFAULT_WEBHOOK_ENV


def test_notification_config_invalid_color_too_high():
    """Test NotificationConfig with color value too high."""
    with pytest.raises(ValidationError) as exc_info:
        NotificationConfig(color=MAX_COLOR + 1)
    assert "color" in str(exc_info.value)


def test_notification_config_invalid_color_negative():
    """Test NotificationConfig with negative color value."""
    with pytest.raises(ValidationError) as exc_info:
        NotificationConfig(color=-1)
    assert "color" in str(exc_info.value)


def test_tool_config_valid():
    """Test ToolConfig with valid data."""
    config = ToolConfig(
        name="Zed Editor",
        enabled=True,
        sources=[
            GitHubReleasesSourceConfig(
                type="github_releases",
                priority=1,
                owner="zed-industries",
                repo="zed",
                atom_url="https://github.com/zed-industries/zed/releases.atom",
            )
        ],
        notification=NotificationConfig(color=VALID_COLOR),
    )
    assert config.name == "Zed Editor"
    assert config.enabled is True
    assert len(config.sources) == 1


def test_tool_config_empty_sources():
    """Test ToolConfig with empty sources list."""
    with pytest.raises(ValidationError) as exc_info:
        ToolConfig(
            name="Test Tool",
            sources=[],
            notification=NotificationConfig(color=VALID_COLOR),
        )
    assert "At least one source must be configured" in str(exc_info.value)


def test_common_config_defaults():
    """Test CommonConfig with default values."""
    config = CommonConfig()
    assert config.check_interval_hours == DEFAULT_CHECK_INTERVAL_HOURS
    assert config.cache_directory == DEFAULT_CACHE_DIRECTORY


def test_common_config_custom_values():
    """Test CommonConfig with custom values."""
    config = CommonConfig(
        check_interval_hours=12,
        cache_directory="./custom_cache",
    )
    assert config.check_interval_hours == 12
    assert config.cache_directory == "./custom_cache"


def test_common_config_invalid_interval():
    """Test CommonConfig with invalid check_interval_hours."""
    with pytest.raises(ValidationError) as exc_info:
        CommonConfig(check_interval_hours=0)
    assert "check_interval_hours" in str(exc_info.value)


def test_app_config_valid():
    """Test AppConfig with valid data."""
    config = AppConfig(
        tools=[
            ToolConfig(
                name="Zed Editor",
                sources=[
                    GitHubReleasesSourceConfig(
                        type="github_releases",
                        priority=1,
                        owner="zed-industries",
                        repo="zed",
                        atom_url="https://github.com/zed-industries/zed/releases.atom",
                    )
                ],
                notification=NotificationConfig(color=VALID_COLOR),
            )
        ],
        common=CommonConfig(),
    )
    assert len(config.tools) == 1
    assert config.common.check_interval_hours == DEFAULT_CHECK_INTERVAL_HOURS


def test_app_config_empty_tools():
    """Test AppConfig with empty tools list."""
    with pytest.raises(ValidationError) as exc_info:
        AppConfig(tools=[])
    assert "At least one tool must be configured" in str(exc_info.value)


def test_app_config_default_common():
    """Test AppConfig with default common config."""
    config = AppConfig(
        tools=[
            ToolConfig(
                name="Test Tool",
                sources=[
                    GitHubReleasesSourceConfig(
                        type="github_releases",
                        priority=1,
                        owner="owner",
                        repo="repo",
                        atom_url="https://github.com/owner/repo/releases.atom",
                    )
                ],
                notification=NotificationConfig(color=VALID_COLOR),
            )
        ]
    )
    assert config.common.check_interval_hours == DEFAULT_CHECK_INTERVAL_HOURS
