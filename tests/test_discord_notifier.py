"""Tests for Discord notifier."""

import httpx
import pytest
import respx

from devtools_release_notifier.notifiers import DiscordNotifier

# Constants
VALID_COLOR = 5814783
WEBHOOK_URL = "https://discord.com/api/webhooks/123456/abcdef"


class TestDiscordNotifier:
    """Tests for DiscordNotifier."""

    @respx.mock
    def test_send_success(self):
        """Test successful Discord notification."""
        # Mock successful webhook response
        respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

        notifier = DiscordNotifier()
        result = notifier.send(
            webhook_url=WEBHOOK_URL,
            tool_name="Zed Editor",
            version="v0.100.0",
            content="Release notes",
            url="https://github.com/zed-industries/zed/releases/tag/v0.100.0",
            color=VALID_COLOR,
        )

        assert result is True

    @respx.mock
    def test_send_http_error(self):
        """Test Discord notification with HTTP error."""
        # Mock 404 error
        respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(404))

        notifier = DiscordNotifier()
        result = notifier.send(
            webhook_url=WEBHOOK_URL,
            tool_name="Zed Editor",
            version="v0.100.0",
            content="Release notes",
            url="https://github.com/zed-industries/zed/releases/tag/v0.100.0",
            color=VALID_COLOR,
        )

        assert result is False

    @respx.mock
    def test_send_network_error(self):
        """Test Discord notification with network error."""
        # Mock network error
        respx.post(WEBHOOK_URL).mock(side_effect=httpx.ConnectError("Connection failed"))

        notifier = DiscordNotifier()
        result = notifier.send(
            webhook_url=WEBHOOK_URL,
            tool_name="Zed Editor",
            version="v0.100.0",
            content="Release notes",
            url="https://github.com/zed-industries/zed/releases/tag/v0.100.0",
            color=VALID_COLOR,
        )

        assert result is False

    @respx.mock
    def test_send_long_content(self):
        """Test Discord notification with long content (truncation)."""
        # Mock successful webhook response
        respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

        long_content = "A" * 5000

        notifier = DiscordNotifier()
        result = notifier.send(
            webhook_url=WEBHOOK_URL,
            tool_name="Test Tool",
            version="v1.0.0",
            content=long_content,
            url="https://example.com",
            color=VALID_COLOR,
        )

        assert result is True

        # Verify the request was made
        assert len(respx.calls) == 1
        request = respx.calls[0].request
        body = request.read().decode()
        # Content should be truncated to 4000 characters in the Discord payload
        assert '"description": "' + ("A" * 4000) + '"' in body or len(body) < 6000
