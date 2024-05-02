import pytest

from app.utils.utils import parse_json


@pytest.mark.parametrize(
    "input_json_string, expected_output",
    [
        ("{'key': 'value'}", {"key": "value"}),  # Single to double quotes
        ('{"key": "value",}', {"key": "value"}),  # Trailing comma removal
        ('{"key1": "value1", "key2": "value2"}', {"key1": "value1", "key2": "value2"}),  # Valid JSON
        ("{'key1': 'value1', 'key2': 'value2',}", {"key1": "value1", "key2": "value2"}),  # Trailing comma and single quotes
        ("invalid json", None),  # Invalid JSON
        (
                '```json\n{"action": "search", "user_query": "looking for a fishing rod reel", "embedding_query": "fishing rod reel"}\n```',
                {
                    "action": "search",
                    "user_query": "looking for a fishing rod reel",
                    "embedding_query": "fishing rod reel"
                }
        ),  # JSON string with code block
    ]
)
def test_parse_json(input_json_string, expected_output):
    result = parse_json(input_json_string)
    assert result == expected_output
