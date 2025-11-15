"""Discord webhook models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DiscordEmbedFooter(BaseModel):
    """Discord embed footer.

    Attributes:
        text: Footer text
    """

    text: str = Field(..., description="Footer text")


class DiscordEmbed(BaseModel):
    """Discord embed object.

    Attributes:
        title: Embed title
        description: Embed description
        url: Embed URL
        color: Embed color (integer)
        timestamp: ISO 8601 timestamp
        footer: Embed footer
    """

    title: str = Field(..., description="Embed title")
    description: str = Field(..., description="Embed description")
    url: str = Field(..., description="Embed URL")
    color: int = Field(
        ..., ge=0, le=16777215, description="Embed color (0-16777215)"
    )
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    footer: Optional[DiscordEmbedFooter] = Field(None, description="Embed footer")


class DiscordWebhookPayload(BaseModel):
    """Discord webhook payload.

    Attributes:
        embeds: List of embeds
    """

    embeds: list[DiscordEmbed] = Field(..., description="List of embeds")

    @classmethod
    def create_release_notification(
        cls,
        tool_name: str,
        version: str,
        content: str,
        url: str,
        color: int,
    ) -> "DiscordWebhookPayload":
        """Create a release notification payload.

        Args:
            tool_name: Tool name
            version: Version string
            content: Release content
            url: Release URL
            color: Embed color

        Returns:
            Discord webhook payload
        """
        # Limit content to Discord's embed description limit (4096 chars)
        truncated_content = content[:4000] if len(content) > 4000 else content

        embed = DiscordEmbed(
            title=f"🚀 {tool_name} - {version}",
            description=truncated_content,
            url=url,
            color=color,
            timestamp=datetime.utcnow().isoformat(),
            footer=DiscordEmbedFooter(text="devtools-release-notifier"),
        )

        return cls(embeds=[embed])
