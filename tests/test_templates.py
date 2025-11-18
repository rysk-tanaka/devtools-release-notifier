"""Tests for template string utilities."""

from devtools_release_notifier.templates import convert, render_template


def test_convert_with_str_flag():
    """Test conversion with 's' flag."""
    value = 42
    result = convert(value, "s")
    assert result == "42"
    assert isinstance(result, str)


def test_convert_with_repr_flag():
    """Test conversion with 'r' flag."""
    value = "test"
    result = convert(value, "r")
    assert result == "'test'"


def test_convert_with_ascii_flag():
    """Test conversion with 'a' flag."""
    value = "café"
    result = convert(value, "a")
    assert result == "'caf\\xe9'"


def test_convert_with_none_flag():
    """Test conversion with None flag (no conversion)."""
    value = 42
    result = convert(value, None)
    assert result == 42


def test_convert_with_invalid_flag():
    """Test conversion with invalid flag returns original value."""
    value = 42
    result = convert(value, "invalid")
    assert result == 42


def test_basic_variable_expansion():
    """Test basic variable expansion."""
    name = "World"
    result = render_template(t"Hello {name}!")
    assert result == "Hello World!"


def test_multiple_interpolations():
    """Test template with multiple interpolations."""
    tool = "Zed"
    version = "v1.0.0"
    result = render_template(t"🚀 {tool} - {version}")
    assert result == "🚀 Zed - v1.0.0"


def test_conversion_flag_str():
    """Test conversion flag !s."""
    value = 42
    result = render_template(t"{value!s}")
    assert result == "42"


def test_conversion_flag_repr():
    """Test conversion flag !r."""
    value = "test"
    result = render_template(t"{value!r}")
    assert result == "'test'"


def test_conversion_flag_ascii():
    """Test conversion flag !a."""
    value = "café"
    result = render_template(t"{value!a}")
    assert result == "'caf\\xe9'"


def test_format_specification_float():
    """Test format specification for float."""
    value = 3.14159
    result = render_template(t"{value:.2f}")
    assert result == "3.14"


def test_format_specification_padding():
    """Test format specification for padding."""
    value = 42
    result = render_template(t"{value:05d}")
    assert result == "00042"


def test_format_specification_with_conversion():
    """Test format specification combined with conversion."""
    value = 3.14159
    result = render_template(t"{value!s:.4}")
    assert result == "3.14"


def test_empty_template():
    """Test empty template."""
    result = render_template(t"")
    assert result == ""


def test_template_with_no_interpolation():
    """Test template with only static content."""
    result = render_template(t"Hello World!")
    assert result == "Hello World!"


def test_template_with_none_value():
    """Test template with None value."""
    value = None
    result = render_template(t"{value}")
    assert result == "None"


def test_template_with_empty_string():
    """Test template with empty string value."""
    value = ""
    result = render_template(t"{value}")
    assert result == ""


def test_multiline_template():
    """Test multiline template string."""
    tool = "Zed"
    version = "v1.0.0"
    result = render_template(
        t"""Tool: {tool}
Version: {version}"""
    )
    assert result == "Tool: Zed\nVersion: v1.0.0"


def test_template_with_special_characters():
    """Test template with special characters."""
    url = "https://example.com/path?query=value"
    result = render_template(t"URL: {url}")
    assert result == "URL: https://example.com/path?query=value"


def test_template_with_unicode():
    """Test template with unicode characters."""
    emoji = "🚀"
    name = "ツール"
    result = render_template(t"{emoji} {name}")
    assert result == "🚀 ツール"


def test_template_with_datetime_format():
    """Test template with datetime strftime in interpolation."""
    from datetime import UTC, datetime

    timestamp = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    result = render_template(t"{timestamp.strftime('%Y-%m-%d')}")
    assert result == "2025-01-15"


def test_template_with_method_call():
    """Test template with method call in interpolation."""
    text = "hello"
    result = render_template(t"{text.upper()}")
    assert result == "HELLO"


def test_template_with_dict_access():
    """Test template with dictionary access."""
    data = {"key": "value"}
    result = render_template(t"{data.get('key', 'default')}")
    assert result == "value"


def test_template_with_numeric_operations():
    """Test template with numeric operations."""
    x = 10
    y = 5
    result = render_template(t"{x + y}")
    assert result == "15"


def test_complex_markdown_frontmatter():
    """Test complex markdown frontmatter generation (real-world example)."""
    from datetime import UTC, datetime

    tool_name = "Zed Editor"
    version = "v1.0.0"
    timestamp = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    url = "https://github.com/zed-industries/zed/releases/tag/v1.0.0"
    content = "Release notes"

    result = render_template(
        t"""---
title: {tool_name} - {version}
date: {timestamp.strftime("%Y-%m-%d")}
version: {version}
url: {url}
---

# {tool_name} - {version}

リリース日: {timestamp.strftime("%Y年%m月%d日")}

バージョン: {version}

## リリースノート

{content}
"""
    )

    expected = """---
title: Zed Editor - v1.0.0
date: 2025-01-15
version: v1.0.0
url: https://github.com/zed-industries/zed/releases/tag/v1.0.0
---

# Zed Editor - v1.0.0

リリース日: 2025年01月15日

バージョン: v1.0.0

## リリースノート

Release notes
"""
    assert result == expected
