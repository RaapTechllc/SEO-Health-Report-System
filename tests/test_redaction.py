"""Tests for the redaction utility module."""


from packages.seo_health_report.scripts.redaction import (
    REDACTION_PATTERNS,
    SENSITIVE_KEYS,
    redact_dict,
    redact_sensitive,
)


class TestRedactSensitive:
    """Tests for redact_sensitive function."""

    # API key patterns
    def test_redacts_api_key_equals(self):
        assert "[REDACTED]" in redact_sensitive("api_key=abc123")

    def test_redacts_api_key_colon(self):
        assert "[REDACTED]" in redact_sensitive("api_key: abc123")

    def test_redacts_apikey_no_underscore(self):
        assert "[REDACTED]" in redact_sensitive("apikey=abc123")

    def test_redacts_api_hyphen_key(self):
        assert "[REDACTED]" in redact_sensitive("api-key=abc123")

    # Token patterns
    def test_redacts_token_equals(self):
        assert "[REDACTED]" in redact_sensitive("token=mytoken123")

    def test_redacts_token_colon(self):
        assert "[REDACTED]" in redact_sensitive("token: mytoken123")

    # Secret patterns
    def test_redacts_secret_equals(self):
        assert "[REDACTED]" in redact_sensitive("secret=supersecret")

    def test_redacts_secret_colon(self):
        assert "[REDACTED]" in redact_sensitive("secret: supersecret")

    # Password patterns
    def test_redacts_password_equals(self):
        assert "[REDACTED]" in redact_sensitive("password=mypassword")

    def test_redacts_password_colon(self):
        assert "[REDACTED]" in redact_sensitive("password: mypassword")

    # Authorization header
    def test_redacts_authorization_bearer(self):
        result = redact_sensitive("Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")
        assert result == "Authorization: Bearer [REDACTED]"

    def test_redacts_authorization_bearer_case_insensitive(self):
        result = redact_sensitive("authorization: bearer abc123")
        assert result == "Authorization: Bearer [REDACTED]"

    # Cookie patterns
    def test_redacts_cookie_header(self):
        result = redact_sensitive("Cookie: session=abc123; user=test")
        assert result == "Cookie: [REDACTED]"

    def test_redacts_set_cookie_header(self):
        result = redact_sensitive("Set-Cookie: session=abc123; HttpOnly")
        assert result == "Set-Cookie: [REDACTED]"

    # Case insensitivity
    def test_redacts_uppercase_api_key(self):
        assert "[REDACTED]" in redact_sensitive("API_KEY=ABC123")

    def test_redacts_mixed_case_token(self):
        assert "[REDACTED]" in redact_sensitive("Token=MyToken123")

    # Edge cases
    def test_empty_string_returns_empty(self):
        assert redact_sensitive("") == ""

    def test_non_string_returns_unchanged(self):
        assert redact_sensitive(123) == 123
        assert redact_sensitive(None) is None
        assert redact_sensitive([1, 2, 3]) == [1, 2, 3]

    def test_no_sensitive_data_unchanged(self):
        text = "This is just a normal message with no secrets"
        assert redact_sensitive(text) == text

    def test_multiple_patterns_in_one_string(self):
        text = "api_key=abc123 and password=secret123"
        result = redact_sensitive(text)
        assert "abc123" not in result
        assert "secret123" not in result
        assert result.count("[REDACTED]") == 2

    def test_quoted_values(self):
        assert "[REDACTED]" in redact_sensitive("api_key='abc123'")
        assert "[REDACTED]" in redact_sensitive('api_key="abc123"')


class TestRedactDict:
    """Tests for redact_dict function."""

    # Sensitive key redaction
    def test_redacts_api_key_key(self):
        data = {"api_key": "secret123"}
        result = redact_dict(data)
        assert result["api_key"] == "[REDACTED]"

    def test_redacts_token_key(self):
        data = {"token": "mytoken"}
        result = redact_dict(data)
        assert result["token"] == "[REDACTED]"

    def test_redacts_secret_key(self):
        data = {"secret": "mysecret"}
        result = redact_dict(data)
        assert result["secret"] == "[REDACTED]"

    def test_redacts_password_key(self):
        data = {"password": "mypassword"}
        result = redact_dict(data)
        assert result["password"] == "[REDACTED]"

    def test_redacts_authorization_key(self):
        data = {"authorization": "Bearer token"}
        result = redact_dict(data)
        assert result["authorization"] == "[REDACTED]"

    def test_redacts_cookie_key(self):
        data = {"cookie": "session=abc"}
        result = redact_dict(data)
        assert result["cookie"] == "[REDACTED]"

    def test_redacts_api_hyphen_key(self):
        data = {"api-key": "secret123"}
        result = redact_dict(data)
        assert result["api-key"] == "[REDACTED]"

    # Case insensitivity for keys
    def test_redacts_uppercase_api_key_key(self):
        data = {"API_KEY": "secret123"}
        result = redact_dict(data)
        assert result["API_KEY"] == "[REDACTED]"

    def test_redacts_mixed_case_token_key(self):
        data = {"Token": "mytoken"}
        result = redact_dict(data)
        assert result["Token"] == "[REDACTED]"

    def test_redacts_key_containing_sensitive_word(self):
        data = {"my_api_key_value": "secret", "user_password_hash": "hash123"}
        result = redact_dict(data)
        assert result["my_api_key_value"] == "[REDACTED]"
        assert result["user_password_hash"] == "[REDACTED]"

    # Non-sensitive keys pass through
    def test_non_sensitive_key_unchanged(self):
        data = {"url": "https://example.com", "name": "test"}
        result = redact_dict(data)
        assert result["url"] == "https://example.com"
        assert result["name"] == "test"

    # Nested dict handling
    def test_nested_dict_redaction(self):
        data = {
            "config": {
                "api_key": "secret123",
                "url": "https://example.com"
            }
        }
        result = redact_dict(data)
        assert result["config"]["api_key"] == "[REDACTED]"
        assert result["config"]["url"] == "https://example.com"

    def test_deeply_nested_dict(self):
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "token": "deep_secret"
                    }
                }
            }
        }
        result = redact_dict(data)
        assert result["level1"]["level2"]["level3"]["token"] == "[REDACTED]"

    # List handling
    def test_list_of_dicts(self):
        data = {
            "users": [
                {"name": "user1", "password": "pass1"},
                {"name": "user2", "password": "pass2"}
            ]
        }
        result = redact_dict(data)
        assert result["users"][0]["name"] == "user1"
        assert result["users"][0]["password"] == "[REDACTED]"
        assert result["users"][1]["name"] == "user2"
        assert result["users"][1]["password"] == "[REDACTED]"

    def test_list_of_strings_with_sensitive_data(self):
        data = {
            "logs": [
                "api_key=abc123",
                "normal log message",
                "token: xyz789"
            ]
        }
        result = redact_dict(data)
        assert "abc123" not in result["logs"][0]
        assert result["logs"][1] == "normal log message"
        assert "xyz789" not in result["logs"][2]

    def test_list_with_mixed_types(self):
        data = {
            "items": [
                {"secret": "hidden"},
                "api_key=visible",
                123,
                None
            ]
        }
        result = redact_dict(data)
        assert result["items"][0]["secret"] == "[REDACTED]"
        assert "visible" not in result["items"][1]
        assert result["items"][2] == 123
        assert result["items"][3] is None

    # Edge cases
    def test_empty_dict(self):
        assert redact_dict({}) == {}

    def test_non_dict_input_returns_unchanged(self):
        assert redact_dict("not a dict") == "not a dict"
        assert redact_dict(123) == 123
        assert redact_dict(None) is None
        assert redact_dict([1, 2, 3]) == [1, 2, 3]

    def test_string_value_with_sensitive_pattern(self):
        data = {
            "message": "Response contained api_key=abc123 in body"
        }
        result = redact_dict(data)
        assert "abc123" not in result["message"]

    def test_numeric_values_unchanged(self):
        data = {"count": 42, "price": 19.99}
        result = redact_dict(data)
        assert result["count"] == 42
        assert result["price"] == 19.99

    def test_boolean_values_unchanged(self):
        data = {"enabled": True, "disabled": False}
        result = redact_dict(data)
        assert result["enabled"] is True
        assert result["disabled"] is False

    def test_none_values_unchanged(self):
        data = {"value": None}
        result = redact_dict(data)
        assert result["value"] is None

    def test_original_dict_not_modified(self):
        data = {"api_key": "secret123"}
        original_value = data["api_key"]
        redact_dict(data)
        assert data["api_key"] == original_value


class TestPatternConstants:
    """Tests for module constants."""

    def test_redaction_patterns_is_list(self):
        assert isinstance(REDACTION_PATTERNS, list)

    def test_redaction_patterns_has_entries(self):
        assert len(REDACTION_PATTERNS) > 0

    def test_sensitive_keys_contains_expected(self):
        expected = {"api_key", "token", "secret", "password", "authorization", "cookie", "api-key"}
        assert expected.issubset(SENSITIVE_KEYS)
