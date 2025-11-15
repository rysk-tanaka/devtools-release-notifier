"""Output models for GitHub Actions integration."""

from pydantic import BaseModel, Field


class ReleaseOutput(BaseModel):
    """Release information for GitHub Actions output.

    This model is used when outputting release information
    to a JSON file for processing by GitHub Actions.

    Attributes:
        tool_name: Tool name
        version: Version string
        content: Release content (untranslated)
        url: Release URL
        color: Discord embed color
        webhook_env: Environment variable name for webhook URL
    """

    tool_name: str = Field(..., description="Tool name")
    version: str = Field(..., description="Version string")
    content: str = Field(..., description="Release content")
    url: str = Field(..., description="Release URL")
    color: int = Field(..., ge=0, le=16777215, description="Discord embed color (0-16777215)")
    webhook_env: str = Field(
        default="DISCORD_WEBHOOK",
        description="Environment variable name for webhook URL",
    )


class TranslatedRelease(BaseModel):
    """Translated release information from Claude.

    This model represents the expected output format
    from the Claude translation action.

    Attributes:
        tool_name: Tool name
        translated_content: Translated content in Japanese
    """

    tool_name: str = Field(..., description="Tool name")
    translated_content: str = Field(..., description="Translated content in Japanese")
