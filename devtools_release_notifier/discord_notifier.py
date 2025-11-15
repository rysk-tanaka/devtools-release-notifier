"""Discord notification handler."""

import httpx

from devtools_release_notifier.models.discord import DiscordWebhookPayload


class DiscordNotifier:
    """Handle Discord webhook notifications."""

    def send(
        self,
        webhook_url: str,
        tool_name: str,
        version: str,
        content: str,
        url: str,
        color: int,
    ) -> bool:
        """Send release notification to Discord.

        Args:
            webhook_url: Discord webhook URL
            tool_name: Tool name
            version: Version string
            content: Release content
            url: Release URL
            color: Embed color

        Returns:
            True if notification was sent successfully, False otherwise
        """
        try:
            payload = DiscordWebhookPayload.create_release_notification(
                tool_name=tool_name,
                version=version,
                content=content,
                url=url,
                color=color,
            )

            response = httpx.post(
                webhook_url,
                json=payload.model_dump(),
                timeout=10.0,
            )
            response.raise_for_status()
            print(f"✓ Discord notification sent for {tool_name}")
            return True
        except httpx.HTTPError as e:
            print(f"✗ Discord notification failed for {tool_name}: {e}")
            return False
        except Exception as e:
            print(f"✗ Discord notification failed for {tool_name}: {e}")
            return False
