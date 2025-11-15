"""Tests for send_to_discord script."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import respx

from devtools_release_notifier.scripts.send_to_discord import main, send_to_discord

# Constants
WEBHOOK_URL = "https://discord.com/api/webhooks/123456/abcdef"
VALID_COLOR = 5814783


class TestSendToDiscord:
    """Tests for send_to_discord function."""

    @respx.mock
    def test_send_success(self):
        """Test successful Discord notification."""
        respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

        result = send_to_discord(
            webhook_url=WEBHOOK_URL,
            tool_name="Zed Editor",
            version="v0.100.0",
            translated_content="## 📌 主な変更点\n- Test content",
            url="https://github.com/zed-industries/zed/releases/tag/v0.100.0",
            color=VALID_COLOR,
        )

        assert result is True
        assert len(respx.calls) == 1

    @respx.mock
    def test_send_http_error(self):
        """Test Discord notification with HTTP error."""
        respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(404))

        result = send_to_discord(
            webhook_url=WEBHOOK_URL,
            tool_name="Zed Editor",
            version="v0.100.0",
            translated_content="Test content",
            url="https://github.com/test",
            color=VALID_COLOR,
        )

        assert result is False

    @respx.mock
    def test_send_network_error(self):
        """Test Discord notification with network error."""
        respx.post(WEBHOOK_URL).mock(side_effect=httpx.ConnectError("Connection failed"))

        result = send_to_discord(
            webhook_url=WEBHOOK_URL,
            tool_name="Zed Editor",
            version="v0.100.0",
            translated_content="Test content",
            url="https://github.com/test",
            color=VALID_COLOR,
        )

        assert result is False

    @respx.mock
    def test_send_long_content_truncation(self):
        """Test that long content is truncated to 4000 characters."""
        respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

        long_content = "A" * 5000

        result = send_to_discord(
            webhook_url=WEBHOOK_URL,
            tool_name="Test Tool",
            version="v1.0.0",
            translated_content=long_content,
            url="https://example.com",
            color=VALID_COLOR,
        )

        assert result is True
        assert len(respx.calls) == 1
        request = respx.calls[0].request
        body = json.loads(request.read().decode())
        # Verify content was truncated
        assert len(body["embeds"][0]["description"]) == 4000


class TestMainFunction:
    """Tests for main function."""

    @respx.mock
    def test_main_all_success(self, tmp_path: Path, monkeypatch):
        """Test main function with all notifications successful."""
        # Create releases file
        releases_file = tmp_path / "releases.json"
        releases = [
            {
                "tool_name": "Zed Editor",
                "version": "v0.100.0",
                "content": "Original content",
                "url": "https://github.com/zed-industries/zed/releases/tag/v0.100.0",
                "color": VALID_COLOR,
                "webhook_env": "DISCORD_WEBHOOK",
            }
        ]
        releases_file.write_text(json.dumps(releases))

        # Create translated JSON
        translated_json = json.dumps(
            [{"tool_name": "Zed Editor", "translated_content": "Translated content"}]
        )

        # Set environment variable
        monkeypatch.setenv("DISCORD_WEBHOOK", WEBHOOK_URL)

        # Mock Discord webhook
        respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

        # Run main
        with patch.object(sys, "argv", ["send_to_discord.py", str(releases_file), translated_json]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    @respx.mock
    def test_main_all_failed(self, tmp_path: Path, monkeypatch):
        """Test main function with all notifications failed."""
        releases_file = tmp_path / "releases.json"
        releases = [
            {
                "tool_name": "Zed Editor",
                "version": "v0.100.0",
                "content": "Content",
                "url": "https://github.com/test",
                "color": VALID_COLOR,
                "webhook_env": "DISCORD_WEBHOOK",
            }
        ]
        releases_file.write_text(json.dumps(releases))

        translated_json = json.dumps(
            [{"tool_name": "Zed Editor", "translated_content": "Translated"}]
        )

        monkeypatch.setenv("DISCORD_WEBHOOK", WEBHOOK_URL)

        # Mock failed webhook
        respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(404))

        with patch.object(sys, "argv", ["send_to_discord.py", str(releases_file), translated_json]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Exit code 1 for all failed
            assert exc_info.value.code == 1

    @respx.mock
    def test_main_partial_failure(self, tmp_path: Path, monkeypatch):
        """Test main function with partial failure."""
        webhook_url_1 = "https://discord.com/api/webhooks/123456/success"
        webhook_url_2 = "https://discord.com/api/webhooks/123456/failed"

        releases_file = tmp_path / "releases.json"
        releases = [
            {
                "tool_name": "Tool 1",
                "version": "v1.0.0",
                "content": "Content 1",
                "url": "https://example.com/1",
                "color": VALID_COLOR,
                "webhook_env": "WEBHOOK_1",
            },
            {
                "tool_name": "Tool 2",
                "version": "v2.0.0",
                "content": "Content 2",
                "url": "https://example.com/2",
                "color": VALID_COLOR,
                "webhook_env": "WEBHOOK_2",
            },
        ]
        releases_file.write_text(json.dumps(releases))

        translated_json = json.dumps(
            [
                {"tool_name": "Tool 1", "translated_content": "Translated 1"},
                {"tool_name": "Tool 2", "translated_content": "Translated 2"},
            ]
        )

        monkeypatch.setenv("WEBHOOK_1", webhook_url_1)
        monkeypatch.setenv("WEBHOOK_2", webhook_url_2)

        # Mock one success, one failure
        respx.post(webhook_url_1).mock(return_value=httpx.Response(204))
        respx.post(webhook_url_2).mock(return_value=httpx.Response(500))

        with patch.object(sys, "argv", ["send_to_discord.py", str(releases_file), translated_json]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Exit code 2 for partial failure
            assert exc_info.value.code == 2

    def test_main_webhook_not_set(self, tmp_path: Path):
        """Test main function when webhook URL is not set."""
        releases_file = tmp_path / "releases.json"
        releases = [
            {
                "tool_name": "Zed Editor",
                "version": "v0.100.0",
                "content": "Content",
                "url": "https://github.com/test",
                "color": VALID_COLOR,
                "webhook_env": "MISSING_WEBHOOK",
            }
        ]
        releases_file.write_text(json.dumps(releases))

        translated_json = json.dumps(
            [{"tool_name": "Zed Editor", "translated_content": "Translated"}]
        )

        with patch.object(sys, "argv", ["send_to_discord.py", str(releases_file), translated_json]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Exit code 1 because all (1) notifications failed (skipped counts as not sent)
            assert exc_info.value.code == 1

    def test_main_file_not_found(self):
        """Test main function when releases file is not found."""
        translated_json = json.dumps([])

        with patch.object(
            sys, "argv", ["send_to_discord.py", "/nonexistent/releases.json", translated_json]
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_main_invalid_translated_json(self, tmp_path: Path):
        """Test main function with invalid translated JSON."""
        releases_file = tmp_path / "releases.json"
        releases_file.write_text("[]")

        with patch.object(sys, "argv", ["send_to_discord.py", str(releases_file), "invalid json"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_main_translated_data_not_list(self, tmp_path: Path):
        """Test main function when translated data is not a list."""
        releases_file = tmp_path / "releases.json"
        releases_file.write_text("[]")

        translated_json = json.dumps({"not": "a list"})

        with patch.object(sys, "argv", ["send_to_discord.py", str(releases_file), translated_json]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @respx.mock
    def test_main_fallback_to_original_content(self, tmp_path: Path, monkeypatch):
        """Test main function falls back to original content when translation is missing."""
        releases_file = tmp_path / "releases.json"
        releases = [
            {
                "tool_name": "Zed Editor",
                "version": "v0.100.0",
                "content": "Original content",
                "url": "https://github.com/test",
                "color": VALID_COLOR,
                "webhook_env": "DISCORD_WEBHOOK",
            }
        ]
        releases_file.write_text(json.dumps(releases))

        # Empty translation (no matching tool_name)
        translated_json = json.dumps([])

        monkeypatch.setenv("DISCORD_WEBHOOK", WEBHOOK_URL)
        respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

        with patch.object(sys, "argv", ["send_to_discord.py", str(releases_file), translated_json]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        # Verify original content was sent
        assert len(respx.calls) == 1
        request = respx.calls[0].request
        body = json.loads(request.read().decode())
        assert body["embeds"][0]["description"] == "Original content"
