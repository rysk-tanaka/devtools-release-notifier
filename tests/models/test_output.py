"""Tests for output models."""

import pytest
from pydantic import ValidationError

from devtools_release_notifier.models.output import ReleaseOutput, TranslatedRelease

# Constants
MIN_COLOR = 0
MAX_COLOR = 16777215
VALID_COLOR = 5814783
DEFAULT_WEBHOOK_ENV = "DISCORD_WEBHOOK"


def test_release_output_valid():
    """Test ReleaseOutput with valid data."""
    output = ReleaseOutput(
        tool_name="Zed Editor",
        version="v0.100.0",
        content="Release notes content",
        url="https://github.com/zed-industries/zed/releases/tag/v0.100.0",
        color=VALID_COLOR,
        webhook_env="DISCORD_WEBHOOK_ZED",
    )
    assert output.tool_name == "Zed Editor"
    assert output.version == "v0.100.0"
    assert output.content == "Release notes content"
    assert output.url == "https://github.com/zed-industries/zed/releases/tag/v0.100.0"
    assert output.color == VALID_COLOR
    assert output.webhook_env == "DISCORD_WEBHOOK_ZED"


def test_release_output_default_webhook_env():
    """Test ReleaseOutput with default webhook_env."""
    output = ReleaseOutput(
        tool_name="Test Tool",
        version="v1.0.0",
        content="Test content",
        url="https://example.com",
        color=VALID_COLOR,
    )
    assert output.webhook_env == DEFAULT_WEBHOOK_ENV


def test_release_output_invalid_color_too_high():
    """Test ReleaseOutput with color value too high."""
    with pytest.raises(ValidationError) as exc_info:
        ReleaseOutput(
            tool_name="Test",
            version="v1.0.0",
            content="Test",
            url="https://example.com",
            color=MAX_COLOR + 1,
        )
    assert "color" in str(exc_info.value)


def test_release_output_invalid_color_negative():
    """Test ReleaseOutput with negative color value."""
    with pytest.raises(ValidationError) as exc_info:
        ReleaseOutput(
            tool_name="Test",
            version="v1.0.0",
            content="Test",
            url="https://example.com",
            color=-1,
        )
    assert "color" in str(exc_info.value)


def test_release_output_missing_required_fields():
    """Test ReleaseOutput with missing required fields."""
    with pytest.raises(ValidationError) as exc_info:
        ReleaseOutput(  # type: ignore[call-arg]
            tool_name="Test Tool",
            version="v1.0.0",
        )
    assert "content" in str(exc_info.value)
    assert "url" in str(exc_info.value)
    assert "color" in str(exc_info.value)


def test_translated_release_valid():
    """Test TranslatedRelease with valid data."""
    translated = TranslatedRelease(
        tool_name="Zed Editor",
        translated_content="## 主な変更点\n- バグ修正\n- 新機能追加",
    )
    assert translated.tool_name == "Zed Editor"
    assert "主な変更点" in translated.translated_content
    assert "バグ修正" in translated.translated_content


def test_translated_release_empty_content():
    """Test TranslatedRelease with empty translated_content."""
    translated = TranslatedRelease(
        tool_name="Test Tool",
        translated_content="",
    )
    assert translated.tool_name == "Test Tool"
    assert translated.translated_content == ""


def test_translated_release_missing_required_fields():
    """Test TranslatedRelease with missing required fields."""
    with pytest.raises(ValidationError) as exc_info:
        TranslatedRelease(tool_name="Test Tool")  # type: ignore[call-arg]
    assert "translated_content" in str(exc_info.value)
