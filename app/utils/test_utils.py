import pytest

from app.utils.utils import parse_json


# Test function for parse_json
@pytest.mark.parametrize(
    "input_json_string, expected_output",
    [
        ("{'key': 'value'}", {"key": "value"}),  # Testing single to double quotes
        ('{"key": "value",}', {"key": "value"}),  # Testing trailing comma removal
        ('{"key1": "value1", "key2": "value2"}', {"key1": "value1", "key2": "value2"}),  # Valid JSON string
        ("{'key1': 'value1', 'key2': 'value2',}", {"key1": "value1", "key2": "value2"}),
        # Trailing comma with single quotes
        ("invalid json", None),  # Invalid JSON input
    ]
)
def test_parse_json(input_json_string, expected_output):
    result = parse_json(input_json_string)
    assert result == expected_output
