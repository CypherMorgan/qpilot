"""Tests for the OpenAPI spec parser."""

from __future__ import annotations

import json

import pytest
import yaml

from app.exceptions import ValidationError
from app.modules.api_test_generation.spec_parser import (
    OpenApiParser,
    ParsedSpec,
)


class TestOpenApiParser:
    """Tests for the OpenAPI spec parser."""

    @pytest.fixture
    def parser(self) -> OpenApiParser:
        return OpenApiParser()

    def test_parse_petstore_yaml(self, parser, petstore_yaml):
        """Should parse a valid petstore.yaml spec correctly."""
        parsed = parser.parse(petstore_yaml, "yaml")

        assert isinstance(parsed, ParsedSpec)
        assert parsed.title == "Pet Store API"
        assert parsed.version == "1.0.0"
        assert parsed.servers == ["https://api.petstore.example.com/v1"]
        assert parsed.endpoint_count == 6

    def test_parse_petstore_json(self, parser, petstore_yaml):
        """Should parse a JSON version of the petstore spec correctly."""
        # Convert YAML to JSON
        raw = yaml.safe_load(petstore_yaml)
        json_str = json.dumps(raw)

        parsed = parser.parse(json_str, "json")
        assert parsed.title == "Pet Store API"
        assert parsed.endpoint_count == 6

    def test_parse_endpoint_structure(self, parser, petstore_yaml):
        """Parsed endpoints should have the correct structure."""
        parsed = parser.parse(petstore_yaml, "yaml")

        # Find the GET /pets endpoint
        pets_get = next(
            (ep for ep in parsed.endpoints if ep.path == "/pets" and ep.method == "get"),
            None,
        )
        assert pets_get is not None
        assert pets_get.summary == "List all pets"
        assert pets_get.operation_id == "listPets"
        assert pets_get.tags == ["pets"]
        assert len(pets_get.parameters) == 2
        assert pets_get.parameters[0].name == "limit"
        assert pets_get.parameters[0].location == "query"
        assert pets_get.parameters[0].schema_type == "integer"

    def test_parse_request_body(self, parser, petstore_yaml):
        """Parsed POST endpoints should have request body info."""
        parsed = parser.parse(petstore_yaml, "yaml")

        pets_post = next(
            (ep for ep in parsed.endpoints if ep.path == "/pets" and ep.method == "post"),
            None,
        )
        assert pets_post is not None
        assert pets_post.request_body is not None
        assert pets_post.request_body.required is True
        assert pets_post.request_body.content_type == "application/json"
        assert pets_post.request_body.schema_ref == "NewPet"

    def test_parse_responses(self, parser, petstore_yaml):
        """Parsed endpoints should have response info."""
        parsed = parser.parse(petstore_yaml, "yaml")

        pets_get = next(
            (ep for ep in parsed.endpoints if ep.path == "/pets/{petId}" and ep.method == "get"),
            None,
        )
        assert pets_get is not None
        assert "200" in pets_get.responses
        assert pets_get.responses["200"].description == "A single pet"
        assert pets_get.responses["200"].schema_ref == "Pet"
        assert "404" in pets_get.responses
        assert pets_get.responses["404"].description == "Pet not found"

    def test_parse_path_parameters(self, parser, petstore_yaml):
        """Path parameters should be correctly extracted."""
        parsed = parser.parse(petstore_yaml, "yaml")

        pet_get = next(
            (ep for ep in parsed.endpoints if ep.path == "/pets/{petId}" and ep.method == "get"),
            None,
        )
        assert pet_get is not None
        assert len(pet_get.parameters) == 1
        param = pet_get.parameters[0]
        assert param.name == "petId"
        assert param.location == "path"
        assert param.required is True
        assert param.schema_type == "integer"

    def test_parse_schemas(self, parser, petstore_yaml):
        """Component schemas should be correctly extracted."""
        parsed = parser.parse(petstore_yaml, "yaml")

        assert len(parsed.schemas) == 3
        schema_names = {s.name for s in parsed.schemas}
        assert schema_names == {"Pet", "NewPet", "User"}

        pet_schema = next(s for s in parsed.schemas if s.name == "Pet")
        assert pet_schema.type == "object"
        assert "id" in pet_schema.required
        assert "name" in pet_schema.required
        assert len(pet_schema.properties) == 3

    def test_parse_security_schemes(self, parser, petstore_yaml):
        """Security schemes should be correctly extracted."""
        parsed = parser.parse(petstore_yaml, "yaml")

        assert len(parsed.security_schemes) == 2
        assert "ApiKeyAuth" in parsed.security_schemes
        assert parsed.security_schemes["ApiKeyAuth"].type == "apiKey"
        assert parsed.security_schemes["ApiKeyAuth"].name == "X-API-Key"
        assert parsed.security_schemes["ApiKeyAuth"].in_ == "header"

        assert "BearerAuth" in parsed.security_schemes
        assert parsed.security_schemes["BearerAuth"].type == "http"
        assert parsed.security_schemes["BearerAuth"].scheme == "bearer"

    def test_parse_invalid_json(self, parser):
        """Invalid JSON should raise ValidationError."""
        with pytest.raises(ValidationError, match="Failed to parse"):
            parser.parse("{invalid json}", "json")

    def test_parse_invalid_yaml(self, parser):
        """Invalid YAML should raise ValidationError."""
        with pytest.raises(ValidationError, match="Failed to parse"):
            parser.parse(": invalid yaml :", "yaml")

    def test_parse_non_dict(self, parser):
        """A non-dict value should raise ValidationError."""
        with pytest.raises(ValidationError, match="OpenAPI spec must be a JSON/YAML object"):
            parser.parse('["not", "an", "object"]', "json")

    def test_parse_missing_openapi_field(self, parser):
        """A spec without 'openapi' or 'swagger' field should raise."""
        with pytest.raises(ValidationError, match="Missing 'openapi' or 'swagger'"):
            parser.parse('{"info": {"title": "Test"}}', "json")

    def test_parse_swagger_v2_rejected(self, parser):
        """OpenAPI 2.0 (Swagger) should be rejected."""
        with pytest.raises(ValidationError, match=r"OpenAPI 2.0"):
            parser.parse('{"swagger": "2.0", "info": {"title": "Test"}, "paths": {}}', "json")

    def test_parse_empty_spec(self, parser):
        """An empty spec with openapi version should parse with no endpoints."""
        result = parser.parse('{"openapi": "3.1.0", "info": {"title": "Empty"}, "paths": {}}', "json")
        assert result.title == "Empty"
        assert result.endpoint_count == 0
        assert result.endpoints == []

    def test_parse_with_type_array(self, parser):
        """A spec with type: [type, 'null'] should handle the array."""
        spec = {
            "openapi": "3.1.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/items": {
                    "get": {
                        "summary": "List items",
                        "parameters": [
                            {
                                "name": "q",
                                "in": "query",
                                "schema": {"type": ["string", "null"]},
                            }
                        ],
                        "responses": {
                            "200": {"description": "OK"}
                        },
                    }
                }
            },
        }
        parsed = parser.parse(json.dumps(spec), "json")
        assert parsed.endpoint_count == 1
        param = parsed.endpoints[0].parameters[0]
        assert param.schema_type == "string"

    def test_parse_with_allof(self, parser):
        """A schema using allOf should be handled."""
        spec = {
            "openapi": "3.1.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {"/test": {"get": {"responses": {"200": {"description": "OK"}}}}},
            "components": {
                "schemas": {
                    "Combined": {
                        "allOf": [
                            {"type": "object", "properties": {"id": {"type": "integer"}}},
                            {"type": "object", "properties": {"name": {"type": "string"}}},
                        ]
                    }
                }
            },
        }
        parsed = parser.parse(json.dumps(spec), "json")
        # Should not crash - allOf schemas are resolved to "object" type
        assert parsed.schemas[0].type == "object"

    def test_parse_deprecated_endpoint(self, parser):
        """Deprecated endpoints should be marked."""
        spec = {
            "openapi": "3.1.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/old": {
                    "get": {
                        "deprecated": True,
                        "responses": {"200": {"description": "OK"}},
                    }
                }
            },
        }
        parsed = parser.parse(json.dumps(spec), "json")
        assert parsed.endpoints[0].deprecated is True
