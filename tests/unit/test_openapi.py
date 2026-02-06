"""
Tests for OpenAPI documentation enhancements.
"""



class TestOpenAPIMetadata:
    """Test OpenAPI metadata and configuration."""

    def test_tags_metadata_exists(self):
        from apps.api.openapi import TAGS_METADATA

        assert TAGS_METADATA is not None
        assert len(TAGS_METADATA) > 0

    def test_tags_have_required_fields(self):
        from apps.api.openapi import TAGS_METADATA

        for tag in TAGS_METADATA:
            assert "name" in tag
            assert "description" in tag

    def test_required_tags_present(self):
        from apps.api.openapi import TAGS_METADATA

        tag_names = [t["name"] for t in TAGS_METADATA]
        required_tags = ["authentication", "audits", "webhooks", "branding", "system"]

        for required in required_tags:
            assert required in tag_names, f"Missing tag: {required}"

    def test_api_description_exists(self):
        from apps.api.openapi import API_DESCRIPTION

        assert API_DESCRIPTION is not None
        assert len(API_DESCRIPTION) > 100

    def test_api_description_contains_sections(self):
        from apps.api.openapi import API_DESCRIPTION

        assert "Authentication" in API_DESCRIPTION
        assert "Rate Limits" in API_DESCRIPTION
        assert "Tiers" in API_DESCRIPTION or "tier" in API_DESCRIPTION.lower()


class TestErrorResponses:
    """Test error response examples."""

    def test_error_responses_exist(self):
        from apps.api.openapi import ERROR_RESPONSES

        assert ERROR_RESPONSES is not None
        assert len(ERROR_RESPONSES) > 0

    def test_common_error_codes_present(self):
        from apps.api.openapi import ERROR_RESPONSES

        required_codes = [400, 401, 404, 422, 500]

        for code in required_codes:
            assert code in ERROR_RESPONSES, f"Missing error code: {code}"

    def test_error_responses_have_description(self):
        from apps.api.openapi import ERROR_RESPONSES

        for code, response in ERROR_RESPONSES.items():
            assert "description" in response, f"Error {code} missing description"


class TestExampleResponses:
    """Test example response constants."""

    def test_audit_example_exists(self):
        from apps.api.openapi import AUDIT_RESPONSE_EXAMPLE

        assert AUDIT_RESPONSE_EXAMPLE is not None
        assert "audit_id" in AUDIT_RESPONSE_EXAMPLE
        assert "status" in AUDIT_RESPONSE_EXAMPLE

    def test_token_example_exists(self):
        from apps.api.openapi import TOKEN_RESPONSE_EXAMPLE

        assert TOKEN_RESPONSE_EXAMPLE is not None
        assert "access_token" in TOKEN_RESPONSE_EXAMPLE
        assert "token_type" in TOKEN_RESPONSE_EXAMPLE

    def test_pricing_example_exists(self):
        from apps.api.openapi import PRICING_EXAMPLE

        assert PRICING_EXAMPLE is not None
        assert "tiers" in PRICING_EXAMPLE


class TestCustomOpenAPI:
    """Test custom OpenAPI schema generation."""

    def test_create_custom_openapi_function_exists(self):
        from apps.api.openapi import create_custom_openapi

        assert create_custom_openapi is not None
        assert callable(create_custom_openapi)

    def test_get_custom_openapi_function(self):
        from apps.api.openapi import get_custom_openapi_function

        assert get_custom_openapi_function is not None
        assert callable(get_custom_openapi_function)

    def test_openapi_schema_has_security(self):
        from fastapi import FastAPI

        from apps.api.openapi import API_DESCRIPTION, TAGS_METADATA, create_custom_openapi

        app = FastAPI(
            title="Test API",
            description=API_DESCRIPTION,
            version="1.0.0",
            openapi_tags=TAGS_METADATA,
        )

        schema = create_custom_openapi(app)

        assert "components" in schema
        assert "securitySchemes" in schema["components"]
        assert "BearerAuth" in schema["components"]["securitySchemes"]

    def test_openapi_schema_has_info(self):
        from fastapi import FastAPI

        from apps.api.openapi import API_DESCRIPTION, TAGS_METADATA, create_custom_openapi

        app = FastAPI(
            title="SEO Health Report API",
            description=API_DESCRIPTION,
            version="2.0.0",
            openapi_tags=TAGS_METADATA,
        )

        # Clear cached schema if present
        app.openapi_schema = None
        schema = create_custom_openapi(app)

        assert "info" in schema
        assert schema["info"]["title"] == "SEO Health Report API"
        assert schema["info"]["version"] == "2.0.0"

    def test_openapi_security_scheme_bearer(self):
        from fastapi import FastAPI

        from apps.api.openapi import TAGS_METADATA, create_custom_openapi

        app = FastAPI(openapi_tags=TAGS_METADATA)
        schema = create_custom_openapi(app)

        bearer_auth = schema["components"]["securitySchemes"]["BearerAuth"]
        assert bearer_auth["type"] == "http"
        assert bearer_auth["scheme"] == "bearer"
        assert bearer_auth["bearerFormat"] == "JWT"


class TestModelExamples:
    """Test that Pydantic models have examples."""

    def test_audit_request_example_exists(self):
        from apps.api.openapi import AUDIT_REQUEST_EXAMPLE

        assert "url" in AUDIT_REQUEST_EXAMPLE
        assert "company_name" in AUDIT_REQUEST_EXAMPLE
        assert "tier" in AUDIT_REQUEST_EXAMPLE

    def test_audit_response_example_exists(self):
        from apps.api.openapi import AUDIT_RESPONSE_EXAMPLE

        assert "audit_id" in AUDIT_RESPONSE_EXAMPLE
        assert "status" in AUDIT_RESPONSE_EXAMPLE

    def test_token_response_example_exists(self):
        from apps.api.openapi import TOKEN_RESPONSE_EXAMPLE

        assert "access_token" in TOKEN_RESPONSE_EXAMPLE
        assert "token_type" in TOKEN_RESPONSE_EXAMPLE


class TestEndpointDocumentation:
    """Test that endpoints have proper documentation."""

    def test_openapi_tags_metadata_complete(self):
        from apps.api.openapi import TAGS_METADATA

        # All tags should have description
        for tag in TAGS_METADATA:
            assert "name" in tag
            assert "description" in tag
            assert len(tag["description"]) > 10

    def test_api_description_comprehensive(self):
        from apps.api.openapi import API_DESCRIPTION

        # Should cover key topics
        assert "Authentication" in API_DESCRIPTION
        assert "Rate Limit" in API_DESCRIPTION
        assert "Webhook" in API_DESCRIPTION
        assert "Bearer" in API_DESCRIPTION

    def test_error_responses_complete(self):
        from apps.api.openapi import ERROR_RESPONSES

        # Should have all common error codes
        assert 400 in ERROR_RESPONSES
        assert 401 in ERROR_RESPONSES
        assert 404 in ERROR_RESPONSES
        assert 422 in ERROR_RESPONSES
        assert 429 in ERROR_RESPONSES
        assert 500 in ERROR_RESPONSES
