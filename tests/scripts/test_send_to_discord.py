"""Tests for send_to_discord script."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx

from devtools_release_notifier.scripts.send_to_discord import (
    _escape_yaml_string,
    _send_notifications,
    _slugify_tool_name,
    main,
    save_markdown_log,
    send_to_discord,
)

# Constants
WEBHOOK_URL = "https://discord.com/api/webhooks/123456/abcdef"
VALID_COLOR = 5814783
LONG_CONTENT_LENGTH = 5000
DISCORD_MAX_DESCRIPTION_LENGTH = 4000


@respx.mock
def test_send_success():
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
def test_send_http_error():
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
def test_send_network_error():
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
def test_send_long_content_truncation():
    """Test that long content is truncated to 4000 characters."""
    respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

    long_content = "A" * LONG_CONTENT_LENGTH

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
    assert len(body["embeds"][0]["description"]) == DISCORD_MAX_DESCRIPTION_LENGTH


@respx.mock
def test_main_all_success(tmp_path: Path, monkeypatch):
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
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "send_to_discord.py",
            str(releases_file),
            translated_json,
            "--markdown-dir",
            str(tmp_path / "markdown"),
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0


@respx.mock
def test_main_all_failed(tmp_path: Path, monkeypatch):
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

    translated_json = json.dumps([{"tool_name": "Zed Editor", "translated_content": "Translated"}])

    monkeypatch.setenv("DISCORD_WEBHOOK", WEBHOOK_URL)

    # Mock failed webhook
    respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(404))

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "send_to_discord.py",
            str(releases_file),
            translated_json,
            "--markdown-dir",
            str(tmp_path / "markdown"),
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    # Exit code 1 for all failed
    assert exc_info.value.code == 1


@respx.mock
def test_main_partial_failure(tmp_path: Path, monkeypatch):
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

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "send_to_discord.py",
            str(releases_file),
            translated_json,
            "--markdown-dir",
            str(tmp_path / "markdown"),
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    # Exit code 2 for partial failure
    assert exc_info.value.code == 2


def test_main_webhook_not_set(tmp_path: Path, monkeypatch):
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

    translated_json = json.dumps([{"tool_name": "Zed Editor", "translated_content": "Translated"}])

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "send_to_discord.py",
            str(releases_file),
            translated_json,
            "--markdown-dir",
            str(tmp_path / "markdown"),
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    # Exit code 1 because all (1) notifications failed (skipped counts as not sent)
    assert exc_info.value.code == 1


def test_main_file_not_found(tmp_path: Path, monkeypatch):
    """Test main function when releases file is not found."""
    translated_json = json.dumps([])

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "send_to_discord.py",
            "/nonexistent/releases.json",
            translated_json,
            "--markdown-dir",
            str(tmp_path / "markdown"),
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_invalid_translated_json(tmp_path: Path, monkeypatch):
    """Test main function with invalid translated JSON."""
    releases_file = tmp_path / "releases.json"
    releases_file.write_text("[]")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "send_to_discord.py",
            str(releases_file),
            "invalid json",
            "--markdown-dir",
            str(tmp_path / "markdown"),
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_translated_data_not_list(tmp_path: Path, monkeypatch):
    """Test main function when translated data is not a list."""
    releases_file = tmp_path / "releases.json"
    releases_file.write_text("[]")

    translated_json = json.dumps({"not": "a list"})

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "send_to_discord.py",
            str(releases_file),
            translated_json,
            "--markdown-dir",
            str(tmp_path / "markdown"),
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


@respx.mock
def test_main_fallback_to_original_content(tmp_path: Path, monkeypatch):
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

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "send_to_discord.py",
            str(releases_file),
            translated_json,
            "--markdown-dir",
            str(tmp_path / "markdown"),
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0

    # Verify original content was sent
    assert len(respx.calls) == 1
    request = respx.calls[0].request
    body = json.loads(request.read().decode())
    assert body["embeds"][0]["description"] == "Original content"


def test_main_invalid_release_data(tmp_path: Path, monkeypatch):
    """Test main function with invalid release data (missing required fields)."""
    releases_file = tmp_path / "releases.json"
    # Missing 'version' field
    releases = [{"tool_name": "Test", "content": "Content", "url": "https://test.com"}]
    releases_file.write_text(json.dumps(releases))

    translated_json = json.dumps([])

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "send_to_discord.py",
            str(releases_file),
            translated_json,
            "--markdown-dir",
            str(tmp_path / "markdown"),
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    # Should exit with error code due to validation failure
    assert exc_info.value.code == 1


def test_main_invalid_translated_data(tmp_path: Path, monkeypatch):
    """Test main function with invalid translated data (missing required fields)."""
    releases_file = tmp_path / "releases.json"
    releases = [
        {
            "tool_name": "Test",
            "version": "v1.0.0",
            "content": "Content",
            "url": "https://test.com",
            "color": VALID_COLOR,
        }
    ]
    releases_file.write_text(json.dumps(releases))

    # Missing 'translated_content' field
    translated_json = json.dumps([{"tool_name": "Test"}])

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "send_to_discord.py",
            str(releases_file),
            translated_json,
            "--markdown-dir",
            str(tmp_path / "markdown"),
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    # Should exit with error code due to validation failure
    assert exc_info.value.code == 1


def test_main_invalid_color_value(tmp_path: Path, monkeypatch):
    """Test main function with invalid color value (out of range)."""
    releases_file = tmp_path / "releases.json"
    # Color must be 0-16777215
    releases = [
        {
            "tool_name": "Test",
            "version": "v1.0.0",
            "content": "Content",
            "url": "https://test.com",
            "color": 99999999,  # Invalid: exceeds max value
        }
    ]
    releases_file.write_text(json.dumps(releases))

    translated_json = json.dumps([])

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "send_to_discord.py",
            str(releases_file),
            translated_json,
            "--markdown-dir",
            str(tmp_path / "markdown"),
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    # Should exit with error code due to validation failure
    assert exc_info.value.code == 1


# Markdown logging tests


def test_slugify_tool_name():
    """Test tool name slugification."""
    assert _slugify_tool_name("Zed Editor") == "zed-editor"
    assert _slugify_tool_name("Dia Browser") == "dia-browser"
    assert _slugify_tool_name("VIM") == "vim"
    assert _slugify_tool_name("Multi Word Tool Name") == "multi-word-tool-name"
    assert _slugify_tool_name("UPPER CASE") == "upper-case"


def test_save_markdown_log_success(tmp_path: Path):
    """Test successful Markdown log saving."""
    markdown_dir = tmp_path / "releases"
    timestamp = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)

    result = save_markdown_log(
        markdown_dir=str(markdown_dir),
        tool_name="Zed Editor",
        version="v0.100.0",
        translated_content="## 📌 主な変更点\n- 変更1\n- 変更2",
        url="https://github.com/zed-industries/zed/releases/tag/v0.100.0",
        timestamp=timestamp,
    )

    assert result is True
    expected_file = markdown_dir / "zed-editor" / "2025-01-15.md"
    assert expected_file.exists()

    content = expected_file.read_text(encoding="utf-8")
    # Verify frontmatter
    assert 'title: "Zed Editor - v0.100.0"' in content
    assert 'date: "2025-01-15"' in content
    assert 'version: "v0.100.0"' in content
    assert 'url: "https://github.com/zed-industries/zed/releases/tag/v0.100.0"' in content
    # Verify Japanese date format
    assert "2025年01月15日" in content
    # Verify content
    assert "## 📌 主な変更点" in content
    assert "- 変更1" in content


def test_save_markdown_log_creates_directory(tmp_path: Path):
    """Test that Markdown log saving creates necessary directories."""
    markdown_dir = tmp_path / "releases"
    timestamp = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)

    # Directory doesn't exist yet
    assert not markdown_dir.exists()

    result = save_markdown_log(
        markdown_dir=str(markdown_dir),
        tool_name="Dia Browser",
        version="v1.0.0",
        translated_content="Test content",
        url="https://test.com",
        timestamp=timestamp,
    )

    assert result is True
    # Verify directories were created
    assert markdown_dir.exists()
    assert (markdown_dir / "dia-browser").exists()
    assert (markdown_dir / "dia-browser" / "2025-01-15.md").exists()


def test_save_markdown_log_overwrites_existing_file(tmp_path: Path):
    """Test that Markdown log saving overwrites existing file on same date."""
    markdown_dir = tmp_path / "releases"
    timestamp = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)

    # Save first version
    save_markdown_log(
        markdown_dir=str(markdown_dir),
        tool_name="Zed Editor",
        version="v0.100.0",
        translated_content="First version",
        url="https://test1.com",
        timestamp=timestamp,
    )

    # Save second version (same date, different time)
    timestamp2 = datetime(2025, 1, 15, 18, 0, 0, tzinfo=UTC)
    result = save_markdown_log(
        markdown_dir=str(markdown_dir),
        tool_name="Zed Editor",
        version="v0.101.0",
        translated_content="Second version",
        url="https://test2.com",
        timestamp=timestamp2,
    )

    assert result is True
    expected_file = markdown_dir / "zed-editor" / "2025-01-15.md"
    content = expected_file.read_text(encoding="utf-8")

    # Should contain second version
    assert "v0.101.0" in content
    assert "Second version" in content
    assert "https://test2.com" in content
    # Should not contain first version
    assert "v0.100.0" not in content
    assert "First version" not in content


def test_save_markdown_log_error_handling(tmp_path: Path):
    """Test Markdown log saving error handling."""
    # Test with invalid path (parent doesn't exist and can't be created)
    invalid_dir = tmp_path / "nonexistent" / "deeply" / "nested"
    # Make parent read-only to prevent creation
    (tmp_path / "nonexistent").mkdir()
    (tmp_path / "nonexistent").chmod(0o444)

    timestamp = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)

    try:
        result = save_markdown_log(
            markdown_dir=str(invalid_dir),
            tool_name="Test Tool",
            version="v1.0.0",
            translated_content="Test",
            url="https://test.com",
            timestamp=timestamp,
        )

        # Should return False on error
        assert result is False
    finally:
        # Cleanup: restore permissions
        (tmp_path / "nonexistent").chmod(0o755)


@respx.mock
def test_send_notifications_with_markdown_dir(tmp_path: Path):
    """Test _send_notifications saves Markdown logs when markdown_dir is specified."""
    from devtools_release_notifier.models.output import ReleaseOutput

    respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

    markdown_dir = tmp_path / "releases"
    releases = [
        ReleaseOutput(
            tool_name="Zed Editor",
            version="v0.100.0",
            content="Original content",
            url="https://github.com/test",
            color=VALID_COLOR,
            webhook_env="TEST_WEBHOOK",
        )
    ]
    translated_map = {"Zed Editor": "## 翻訳された内容"}

    # Mock environment variable
    import os

    original_env = os.environ.copy()
    try:
        os.environ["TEST_WEBHOOK"] = WEBHOOK_URL

        success, failed, skipped = _send_notifications(
            releases, translated_map, markdown_dir=str(markdown_dir)
        )

        assert success == 1
        assert failed == 0
        assert skipped == 0

        # Verify Markdown file was created
        tool_dir = markdown_dir / "zed-editor"
        assert tool_dir.exists()
        md_files = list(tool_dir.glob("*.md"))
        assert len(md_files) == 1
        content = md_files[0].read_text(encoding="utf-8")
        assert "翻訳された内容" in content
    finally:
        os.environ.clear()
        os.environ.update(original_env)


@respx.mock
def test_send_notifications_without_markdown_dir(tmp_path: Path):
    """Test _send_notifications doesn't save Markdown logs when markdown_dir is None."""
    from devtools_release_notifier.models.output import ReleaseOutput

    respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

    markdown_dir = tmp_path / "releases"
    releases = [
        ReleaseOutput(
            tool_name="Zed Editor",
            version="v0.100.0",
            content="Original content",
            url="https://github.com/test",
            color=VALID_COLOR,
            webhook_env="TEST_WEBHOOK",
        )
    ]
    translated_map = {"Zed Editor": "## 翻訳された内容"}

    import os

    original_env = os.environ.copy()
    try:
        os.environ["TEST_WEBHOOK"] = WEBHOOK_URL

        # Call without markdown_dir
        success, failed, skipped = _send_notifications(releases, translated_map, markdown_dir=None)

        assert success == 1
        assert failed == 0
        assert skipped == 0

        # Verify no Markdown files were created
        assert not markdown_dir.exists()
    finally:
        os.environ.clear()
        os.environ.update(original_env)


@respx.mock
def test_send_notifications_no_markdown_on_discord_failure(tmp_path: Path):
    """Test _send_notifications doesn't save Markdown logs when Discord notification fails."""
    from devtools_release_notifier.models.output import ReleaseOutput

    # Mock Discord webhook to fail
    respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(500))

    markdown_dir = tmp_path / "releases"
    releases = [
        ReleaseOutput(
            tool_name="Zed Editor",
            version="v0.100.0",
            content="Original content",
            url="https://github.com/test",
            color=VALID_COLOR,
            webhook_env="TEST_WEBHOOK",
        )
    ]
    translated_map = {"Zed Editor": "## 翻訳された内容"}

    import os

    original_env = os.environ.copy()
    try:
        os.environ["TEST_WEBHOOK"] = WEBHOOK_URL

        success, failed, skipped = _send_notifications(
            releases, translated_map, markdown_dir=str(markdown_dir)
        )

        assert success == 0
        assert failed == 1
        assert skipped == 0

        # Verify no Markdown files were created (Discord failed)
        assert not (markdown_dir / "zed-editor").exists()
    finally:
        os.environ.clear()
        os.environ.update(original_env)


@respx.mock
def test_main_with_markdown_dir_option(tmp_path: Path, monkeypatch):
    """Test main function with --markdown-dir option."""
    respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

    # Create releases file
    releases_file = tmp_path / "releases.json"
    releases = [
        {
            "tool_name": "Zed Editor",
            "version": "v0.100.0",
            "content": "Original content",
            "url": "https://github.com/test",
            "color": VALID_COLOR,
            "webhook_env": "TEST_WEBHOOK",
        }
    ]
    releases_file.write_text(json.dumps(releases))

    translated_json = json.dumps([{"tool_name": "Zed Editor", "translated_content": "## 翻訳"}])

    markdown_dir = tmp_path / "docs" / "releases"

    monkeypatch.setenv("TEST_WEBHOOK", WEBHOOK_URL)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "send_to_discord.py",
            str(releases_file),
            translated_json,
            "--markdown-dir",
            str(markdown_dir),
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    # Should exit successfully
    assert exc_info.value.code == 0

    # Verify Markdown file was created in specified directory
    assert markdown_dir.exists()
    tool_dir = markdown_dir / "zed-editor"
    assert tool_dir.exists()
    md_files = list(tool_dir.glob("*.md"))
    assert len(md_files) == 1
    content = md_files[0].read_text(encoding="utf-8")
    assert "翻訳" in content


def test_escape_yaml_string():
    """Test escaping double quotes in YAML strings."""
    # No quotes - unchanged
    assert _escape_yaml_string("v1.0.0") == "v1.0.0"

    # With double quotes - replaced with single quotes
    assert _escape_yaml_string('Revert "Add feature"') == "Revert 'Add feature'"

    # Multiple double quotes
    assert _escape_yaml_string('"foo" and "bar"') == "'foo' and 'bar'"

    # Empty string
    assert _escape_yaml_string("") == ""


def test_save_markdown_log_with_quotes_in_version(tmp_path: Path):
    """Test that Markdown files with double quotes in version are correctly escaped."""
    markdown_dir = tmp_path / "releases"
    timestamp = datetime(2025, 12, 16, 10, 0, 0, tzinfo=UTC)

    # Version containing double quotes (like Zed nightly releases)
    version_with_quotes = 'nightly: Revert "Add save_file" (#44949)'

    result = save_markdown_log(
        markdown_dir=str(markdown_dir),
        tool_name="Zed Editor",
        version=version_with_quotes,
        translated_content="テスト内容",
        url="https://example.com",
        timestamp=timestamp,
    )

    assert result is True

    # Verify file was created
    md_file = markdown_dir / "zed-editor" / "2025-12-16.md"
    assert md_file.exists()

    # Verify frontmatter has escaped quotes (single quotes instead of double)
    content = md_file.read_text(encoding="utf-8")
    assert "nightly: Revert 'Add save_file' (#44949)" in content
    # Original double quotes should not appear in frontmatter title/version
    assert 'title: "Zed Editor - nightly: Revert "Add' not in content
