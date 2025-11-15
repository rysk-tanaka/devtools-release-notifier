"""Tests for Discord webhook models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from devtools_release_notifier.models.discord import (
    DiscordEmbed,
    DiscordEmbedFooter,
    DiscordWebhookPayload,
)

# Constants
MIN_COLOR = 0
MAX_COLOR = 16777215
VALID_COLOR = 5814783
CONTENT_MAX_LENGTH = 4000


def test_discord_embed_footer_valid():
    """Test DiscordEmbedFooter with valid data."""
    footer = DiscordEmbedFooter(text="devtools-release-notifier")
    assert footer.text == "devtools-release-notifier"


def test_discord_embed_valid():
    """Test DiscordEmbed with valid data."""
    embed = DiscordEmbed(
        title="Test Title",
        description="Test Description",
        url="https://example.com",
        color=VALID_COLOR,
        timestamp="2025-01-15T12:00:00Z",
        footer=None,
    )
    assert embed.title == "Test Title"
    assert embed.description == "Test Description"
    assert embed.url == "https://example.com"
    assert embed.color == VALID_COLOR
    assert embed.timestamp == "2025-01-15T12:00:00Z"
    assert embed.footer is None


def test_discord_embed_with_footer():
    """Test DiscordEmbed with footer."""
    footer = DiscordEmbedFooter(text="Footer Text")
    embed = DiscordEmbed(
        title="Test Title",
        description="Test Description",
        url="https://example.com",
        color=VALID_COLOR,
        timestamp="2025-01-15T12:00:00Z",
        footer=footer,
    )
    assert embed.footer is not None
    assert embed.footer.text == "Footer Text"


def test_discord_embed_invalid_color_too_high():
    """Test DiscordEmbed with color value too high."""
    with pytest.raises(ValidationError) as exc_info:
        DiscordEmbed(
            title="Test",
            description="Test",
            url="https://example.com",
            color=MAX_COLOR + 1,
            timestamp="2025-01-15T12:00:00Z",
            footer=None,
        )
    assert "color" in str(exc_info.value)


def test_discord_embed_invalid_color_negative():
    """Test DiscordEmbed with negative color value."""
    with pytest.raises(ValidationError) as exc_info:
        DiscordEmbed(
            title="Test",
            description="Test",
            url="https://example.com",
            color=-1,
            timestamp="2025-01-15T12:00:00Z",
            footer=None,
        )
    assert "color" in str(exc_info.value)


def test_discord_webhook_payload_valid():
    """Test DiscordWebhookPayload with valid data."""
    embed = DiscordEmbed(
        title="Test Title",
        description="Test Description",
        url="https://example.com",
        color=VALID_COLOR,
        timestamp="2025-01-15T12:00:00Z",
        footer=None,
    )
    payload = DiscordWebhookPayload(embeds=[embed])
    assert len(payload.embeds) == 1
    assert payload.embeds[0].title == "Test Title"


def test_create_release_notification_basic():
    """Test create_release_notification with basic data."""
    payload = DiscordWebhookPayload.create_release_notification(
        tool_name="Zed Editor",
        version="v0.100.0",
        content="New release with bug fixes",
        url="https://github.com/zed-industries/zed/releases/tag/v0.100.0",
        color=VALID_COLOR,
    )

    assert len(payload.embeds) == 1
    embed = payload.embeds[0]
    assert embed.title == "🚀 Zed Editor - v0.100.0"
    assert embed.description == "New release with bug fixes"
    assert embed.url == "https://github.com/zed-industries/zed/releases/tag/v0.100.0"
    assert embed.color == VALID_COLOR
    assert embed.footer is not None
    assert embed.footer.text == "devtools-release-notifier"


def test_create_release_notification_long_content():
    """Test create_release_notification with content exceeding 4000 chars."""
    long_content = "A" * 5000

    payload = DiscordWebhookPayload.create_release_notification(
        tool_name="Test Tool",
        version="v1.0.0",
        content=long_content,
        url="https://example.com",
        color=VALID_COLOR,
    )

    assert len(payload.embeds) == 1
    embed = payload.embeds[0]
    assert len(embed.description) == CONTENT_MAX_LENGTH
    assert embed.description == "A" * CONTENT_MAX_LENGTH


def test_create_release_notification_timestamp_format():
    """Test create_release_notification generates valid ISO 8601 timestamp."""
    payload = DiscordWebhookPayload.create_release_notification(
        tool_name="Test Tool",
        version="v1.0.0",
        content="Test content",
        url="https://example.com",
        color=VALID_COLOR,
    )

    embed = payload.embeds[0]
    # Verify timestamp can be parsed as ISO 8601
    timestamp = datetime.fromisoformat(embed.timestamp.replace("Z", "+00:00"))
    assert isinstance(timestamp, datetime)
