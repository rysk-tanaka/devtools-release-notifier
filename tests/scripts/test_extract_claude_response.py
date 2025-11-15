"""Tests for extract_claude_response script."""

import json
from pathlib import Path

import pytest

from devtools_release_notifier.scripts.extract_claude_response import (
    extract_claude_response,
    extract_json_from_text,
)


def test_extract_from_markdown_code_block_with_json_tag():
    """Test extracting JSON from markdown code block with 'json' tag."""
    text = """Here is the result:
```json
[
  {
    "tool_name": "Zed Editor",
    "translated_content": "Test content"
  }
]
```
"""
    result = extract_json_from_text(text)
    assert result is not None
    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["tool_name"] == "Zed Editor"


def test_extract_from_markdown_code_block_without_language_tag():
    """Test extracting JSON from markdown code block without language tag."""
    text = """Here is the result:
```
[
  {
    "tool_name": "Dia Browser",
    "translated_content": "Test content 2"
  }
]
```
"""
    result = extract_json_from_text(text)
    assert result is not None
    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["tool_name"] == "Dia Browser"


def test_extract_from_raw_json():
    """Test extracting raw JSON without markdown."""
    text = '[{"tool_name": "Test", "translated_content": "Content"}]'
    result = extract_json_from_text(text)
    assert result is not None
    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) == 1


def test_extract_multiple_json_returns_last():
    """Test that when multiple JSON blocks exist, the last one is returned."""
    text = """First block:
```json
[{"tool_name": "First", "translated_content": "First content"}]
```

Second block:
```json
[{"tool_name": "Second", "translated_content": "Second content"}]
```
"""
    result = extract_json_from_text(text)
    assert result is not None
    data = json.loads(result)
    assert data[0]["tool_name"] == "Second"


def test_no_json_found():
    """Test that None is returned when no JSON is found."""
    text = "This is just plain text with no JSON."
    result = extract_json_from_text(text)
    assert result is None


def test_invalid_json_skipped():
    """Test that invalid JSON is skipped and search continues."""
    text = """Invalid JSON:
```json
[{invalid json}]
```

Valid JSON:
```json
[{"tool_name": "Valid", "translated_content": "Valid content"}]
```
"""
    result = extract_json_from_text(text)
    assert result is not None
    data = json.loads(result)
    assert data[0]["tool_name"] == "Valid"


def test_extract_from_array_format_result_type(tmp_path: Path):
    """Test extracting from array format with type='result'."""
    execution_file = tmp_path / "execution.json"
    data = [
        {"type": "system", "subtype": "init"},
        {
            "type": "result",
            "result": '```json\n[{"tool_name": "Zed Editor", "translated_content": "Test"}]\n```',
        },
    ]
    execution_file.write_text(json.dumps(data))

    result = extract_claude_response(str(execution_file))
    parsed = json.loads(result)
    assert parsed[0]["tool_name"] == "Zed Editor"


def test_extract_from_array_format_assistant_type(tmp_path: Path):
    """Test extracting from array format with type='assistant'."""
    execution_file = tmp_path / "execution.json"
    data = [
        {"type": "system", "subtype": "init"},
        {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": '```json\n[{"tool_name": "Dia Browser", "translated_content": "Test"}]\n```',
                    }
                ]
            },
        },
    ]
    execution_file.write_text(json.dumps(data))

    result = extract_claude_response(str(execution_file))
    parsed = json.loads(result)
    assert parsed[0]["tool_name"] == "Dia Browser"


def test_extract_from_array_format_assistant_string_content(tmp_path: Path):
    """Test extracting from array format with string content."""
    execution_file = tmp_path / "execution.json"
    data = [
        {
            "type": "assistant",
            "message": {
                "content": '```json\n[{"tool_name": "Test Tool", "translated_content": "Test"}]\n```'
            },
        },
    ]
    execution_file.write_text(json.dumps(data))

    result = extract_claude_response(str(execution_file))
    parsed = json.loads(result)
    assert parsed[0]["tool_name"] == "Test Tool"


def test_extract_from_dict_format_direct_field(tmp_path: Path):
    """Test extracting from dict format with direct 'response' field."""
    execution_file = tmp_path / "execution.json"
    data = {
        "response": '```json\n[{"tool_name": "Direct Field", "translated_content": "Test"}]\n```'
    }
    execution_file.write_text(json.dumps(data))

    result = extract_claude_response(str(execution_file))
    parsed = json.loads(result)
    assert parsed[0]["tool_name"] == "Direct Field"


def test_extract_from_dict_format_messages_array(tmp_path: Path):
    """Test extracting from dict format with messages array."""
    execution_file = tmp_path / "execution.json"
    data = {
        "messages": [
            {"role": "user", "content": "Translate this"},
            {
                "role": "assistant",
                "content": '```json\n[{"tool_name": "Messages Array", "translated_content": "Test"}]\n```',
            },
        ]
    }
    execution_file.write_text(json.dumps(data))

    result = extract_claude_response(str(execution_file))
    parsed = json.loads(result)
    assert parsed[0]["tool_name"] == "Messages Array"


def test_extract_from_dict_format_conversation(tmp_path: Path):
    """Test extracting from dict format with conversation field."""
    execution_file = tmp_path / "execution.json"
    data = {
        "conversation": [
            {
                "content": '```json\n[{"tool_name": "Conversation", "translated_content": "Test"}]\n```'
            }
        ]
    }
    execution_file.write_text(json.dumps(data))

    result = extract_claude_response(str(execution_file))
    parsed = json.loads(result)
    assert parsed[0]["tool_name"] == "Conversation"


def test_file_not_found():
    """Test error when file does not exist."""
    with pytest.raises(ValueError, match="Execution file not found"):
        extract_claude_response("/nonexistent/file.json")


def test_invalid_json_file(tmp_path: Path):
    """Test error when file is not valid JSON."""
    execution_file = tmp_path / "invalid.json"
    execution_file.write_text("This is not JSON")

    with pytest.raises(ValueError, match="Failed to parse execution file as JSON"):
        extract_claude_response(str(execution_file))


def test_no_json_found_in_file(tmp_path: Path):
    """Test error when no JSON translation is found."""
    execution_file = tmp_path / "no_translation.json"
    data = {"response": "This is just plain text with no JSON array"}
    execution_file.write_text(json.dumps(data))

    with pytest.raises(ValueError, match="Could not find translated JSON"):
        extract_claude_response(str(execution_file))


def test_invalid_translated_release_missing_fields(tmp_path: Path):
    """Test that JSON with missing required fields is rejected."""
    execution_file = tmp_path / "invalid_fields.json"
    # Missing 'translated_content' field
    data = [{"type": "result", "result": '[{"tool_name": "Test Tool"}]'}]
    execution_file.write_text(json.dumps(data))

    with pytest.raises(ValueError, match="Could not find translated JSON"):
        extract_claude_response(str(execution_file))


def test_invalid_translated_release_wrong_type(tmp_path: Path):
    """Test that JSON with wrong field types is rejected."""
    execution_file = tmp_path / "wrong_type.json"
    # tool_name should be string, not number
    data = [{"type": "result", "result": '[{"tool_name": 123, "translated_content": "Test"}]'}]
    execution_file.write_text(json.dumps(data))

    with pytest.raises(ValueError, match="Could not find translated JSON"):
        extract_claude_response(str(execution_file))


def test_valid_translated_release_with_extra_fields(tmp_path: Path):
    """Test that JSON with extra fields is accepted (Pydantic allows extra fields by default)."""
    execution_file = tmp_path / "extra_fields.json"
    data = [
        {
            "type": "result",
            "result": '[{"tool_name": "Test", "translated_content": "Content", "extra": "ignored"}]',
        }
    ]
    execution_file.write_text(json.dumps(data))

    # This should succeed - Pydantic ignores extra fields by default
    result = extract_claude_response(str(execution_file))
    parsed = json.loads(result)
    assert parsed[0]["tool_name"] == "Test"
