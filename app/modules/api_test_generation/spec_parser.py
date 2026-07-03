"""OpenAPI specification parser.

Extracts structured endpoint information from OpenAPI 3.x specs
(JSON or YAML).  The extracted format is compact enough to fit in
an AI prompt while retaining all semantically relevant information.

Design decisions:
- We parse programmatically (not AI-assisted) for reliability and
  token efficiency.
- ``$ref`` references are resolved to inline schemas.
- Only the fields relevant to test generation are preserved.
- The output is a ``ParsedSpec`` dataclass that the service uses
  to render prompts and generate conftest.py.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import yaml

from app.exceptions import ValidationError

# ── Extracted data types ──────────────────────────────────────────


@dataclass
class ExtractedParameter:
    """A path, query, header, or cookie parameter."""

    name: str
    location: str  # path, query, header, cookie
    required: bool = False
    schema_type: str = "string"
    description: str | None = None
    example: str | None = None


@dataclass
class ExtractedProperty:
    """A property within a schema."""

    name: str
    type: str = "string"
    required: bool = False
    description: str | None = None
    example: str | None = None


@dataclass
class ExtractedSchema:
    """A named schema (from components/schemas)."""

    name: str
    type: str = "object"
    description: str | None = None
    properties: list[ExtractedProperty] = field(default_factory=list)
    required: list[str] = field(default_factory=list)


@dataclass
class ExtractedResponse:
    """An HTTP response definition."""

    status_code: str  # "200", "404", or "default"
    description: str | None = None
    content_type: str | None = "application/json"
    schema_ref: str | None = None  # $ref to component schema


@dataclass
class ExtractedRequestBody:
    """A request body definition."""

    required: bool = False
    content_type: str = "application/json"
    schema_ref: str | None = None  # $ref to component schema
    description: str | None = None


@dataclass
class ExtractedEndpoint:
    """A single API endpoint with its parameters and responses."""

    path: str
    method: str  # get, post, put, delete, patch, options, head
    summary: str | None = None
    description: str | None = None
    operation_id: str | None = None
    tags: list[str] = field(default_factory=list)
    parameters: list[ExtractedParameter] = field(default_factory=list)
    request_body: ExtractedRequestBody | None = None
    responses: dict[str, ExtractedResponse] = field(default_factory=dict)
    security: list[dict[str, list[str]]] | None = None
    deprecated: bool = False


@dataclass
class SecurityScheme:
    """A security scheme definition."""

    type: str  # apiKey, http, oauth2, openIdConnect
    scheme: str | None = None  # For http: bearer, basic, digest
    name: str | None = None  # For apiKey: header/query param name
    in_: str | None = None  # For apiKey: header, query, cookie


@dataclass
class ParsedSpec:
    """Complete parsed representation of an OpenAPI spec.

    This is the compact, structured input that the AI uses to
    generate test code.  Typically 5-15% of the raw YAML size.
    """

    title: str = ""
    version: str = ""
    description: str | None = None
    servers: list[str] = field(default_factory=list)
    endpoints: list[ExtractedEndpoint] = field(default_factory=list)
    schemas: list[ExtractedSchema] = field(default_factory=list)
    security_schemes: dict[str, SecurityScheme] = field(default_factory=dict)
    endpoint_count: int = 0


# ── Parser ────────────────────────────────────────────────────────


class OpenApiParser:
    """Parses OpenAPI 3.x JSON/YAML specs into structured data."""

    def parse(self, spec_content: str, spec_format: str = "yaml") -> ParsedSpec:
        """Parse an OpenAPI spec string into a ``ParsedSpec``.

        Args:
            spec_content: Raw spec content (JSON or YAML string).
            spec_format: ``"json"`` or ``"yaml"``.

        Returns:
            A structured ``ParsedSpec`` with extracted endpoints and schemas.

        Raises:
            ValidationError: If the spec cannot be parsed or is invalid.
        """
        try:
            if spec_format == "json":
                raw: dict[str, Any] = json.loads(spec_content)
            else:
                raw = yaml.safe_load(spec_content)
        except (json.JSONDecodeError, yaml.YAMLError) as exc:
            raise ValidationError(
                f"Failed to parse OpenAPI spec: {exc}",
                detail={"format": spec_format, "error": str(exc)},
            ) from exc

        if not isinstance(raw, dict):
            raise ValidationError(
                "OpenAPI spec must be a JSON/YAML object",
                detail={"actual_type": type(raw).__name__},
            )

        # Validate OpenAPI version
        openapi_version = raw.get("openapi", raw.get("swagger", ""))
        if not openapi_version:
            raise ValidationError(
                "Missing 'openapi' or 'swagger' field — not a valid OpenAPI spec",
            )
        if str(openapi_version).startswith("2."):
            raise ValidationError(
                "OpenAPI 2.0 (Swagger) is not supported. Please use OpenAPI 3.0 or 3.1.",
                detail={"version": openapi_version},
            )

        info = raw.get("info", {})
        title = info.get("title", "Untitled API")
        version = info.get("version", "0.0.0")
        description = info.get("description")

        servers_raw = raw.get("servers", [])
        servers = []
        for s in servers_raw:
            url = s.get("url", "")
            if url:
                servers.append(url)

        # Parse components for schemas and security schemes
        components = raw.get("components", {})
        schemas = self._parse_schemas(components.get("schemas", {}))
        security_schemes = self._parse_security_schemes(components.get("securitySchemes", {}))

        # Parse endpoints
        paths = raw.get("paths", {})
        endpoints: list[ExtractedEndpoint] = []
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            for method in ("get", "post", "put", "delete", "patch", "options", "head"):
                operation = path_item.get(method)
                if not isinstance(operation, dict):
                    continue
                endpoint = self._parse_endpoint(path, method, operation)
                endpoints.append(endpoint)

        return ParsedSpec(
            title=title,
            version=version,
            description=description,
            servers=servers,
            endpoints=endpoints,
            schemas=schemas,
            security_schemes=security_schemes,
            endpoint_count=len(endpoints),
        )

    # ── Internal parsers ──────────────────────────────────────────

    def _parse_endpoint(
        self,
        path: str,
        method: str,
        operation: dict[str, Any],
    ) -> ExtractedEndpoint:
        """Parse a single endpoint operation."""
        parameters: list[ExtractedParameter] = []
        for param in operation.get("parameters", []):
            if isinstance(param, dict):
                parameters.append(self._parse_parameter(param))

        # Request body
        request_body = None
        rb_raw = operation.get("requestBody")
        if isinstance(rb_raw, dict):
            request_body = self._parse_request_body(rb_raw)

        # Responses
        responses: dict[str, ExtractedResponse] = {}
        for status_code, resp_raw in operation.get("responses", {}).items():
            if isinstance(resp_raw, dict):
                responses[str(status_code)] = self._parse_response(status_code, resp_raw)

        # Security
        security_raw = operation.get("security")

        return ExtractedEndpoint(
            path=path,
            method=method.lower(),
            summary=operation.get("summary"),
            description=operation.get("description"),
            operation_id=operation.get("operationId"),
            tags=operation.get("tags", []),
            parameters=parameters,
            request_body=request_body,
            responses=responses,
            security=security_raw if security_raw else None,
            deprecated=operation.get("deprecated", False),
        )

    def _parse_parameter(self, param: dict[str, Any]) -> ExtractedParameter:
        """Parse a single parameter definition."""
        schema = param.get("schema", {})
        if not isinstance(schema, dict):
            schema = {"type": "string"}

        schema_type = self._resolve_type(schema)
        example = self._get_example(schema)

        return ExtractedParameter(
            name=param.get("name", "unknown"),
            location=param.get("in", "query"),
            required=param.get("required", False),
            schema_type=schema_type,
            description=param.get("description"),
            example=str(example) if example is not None else None,
        )

    def _parse_request_body(self, rb: dict[str, Any]) -> ExtractedRequestBody:
        """Parse a request body definition."""
        content = rb.get("content", {})
        content_type = "application/json"
        schema_ref = None

        # Prefer application/json
        json_content = content.get("application/json", {})
        if isinstance(json_content, dict):
            schema_ref = self._resolve_ref(json_content.get("schema", {}))
        elif content:
            # Fall back to first available content type
            first_key = next(iter(content))
            content_type = first_key
            first_content = content[first_key]
            if isinstance(first_content, dict):
                schema_ref = self._resolve_ref(first_content.get("schema", {}))

        return ExtractedRequestBody(
            required=rb.get("required", False),
            content_type=content_type,
            schema_ref=schema_ref,
            description=rb.get("description"),
        )

    def _parse_response(self, status_code: str, resp: dict[str, Any]) -> ExtractedResponse:
        """Parse a response definition."""
        content = resp.get("content", {})
        schema_ref = None
        content_type = None

        if content:
            for ct, ct_def in content.items():
                if isinstance(ct_def, dict):
                    schema_ref = self._resolve_ref(ct_def.get("schema", {}))
                    content_type = ct
                    break

        return ExtractedResponse(
            status_code=status_code,
            description=resp.get("description"),
            content_type=content_type,
            schema_ref=schema_ref,
        )

    def _parse_schemas(self, schemas_raw: dict[str, Any]) -> list[ExtractedSchema]:
        """Parse component schemas."""
        schemas: list[ExtractedSchema] = []
        for name, schema_raw in schemas_raw.items():
            if not isinstance(schema_raw, dict):
                continue
            properties: list[ExtractedProperty] = []
            required_list = schema_raw.get("required", [])
            props_raw = schema_raw.get("properties", {})
            if isinstance(props_raw, dict):
                for prop_name, prop_raw in props_raw.items():
                    if isinstance(prop_raw, dict):
                        prop_type = self._resolve_type(prop_raw)
                        example = self._get_example(prop_raw)
                        properties.append(
                            ExtractedProperty(
                                name=prop_name,
                                type=prop_type,
                                required=prop_name in required_list if isinstance(required_list, list) else False,
                                description=prop_raw.get("description"),
                                example=str(example) if example is not None else None,
                            ),
                        )

            schemas.append(
                ExtractedSchema(
                    name=name,
                    type=schema_raw.get("type", "object"),
                    description=schema_raw.get("description"),
                    properties=properties,
                    required=required_list if isinstance(required_list, list) else [],
                ),
            )
        return schemas

    def _parse_security_schemes(
        self,
        schemes_raw: dict[str, Any],
    ) -> dict[str, SecurityScheme]:
        """Parse security scheme definitions."""
        schemes: dict[str, SecurityScheme] = {}
        for name, scheme_raw in schemes_raw.items():
            if not isinstance(scheme_raw, dict):
                continue
            schemes[name] = SecurityScheme(
                type=scheme_raw.get("type", ""),
                scheme=scheme_raw.get("scheme"),
                name=scheme_raw.get("name"),
                in_=scheme_raw.get("in"),
            )
        return schemes

    # ── Helpers ───────────────────────────────────────────────────

    def _resolve_ref(self, obj: dict[str, Any]) -> str | None:
        """Resolve a ``$ref`` to a component name, or return ``None``."""
        ref = obj.get("$ref") if isinstance(obj, dict) else None
        if ref and isinstance(ref, str):
            # Extract the schema name from "#/components/schemas/Pet"
            parts = ref.split("/")
            if len(parts) >= 2:
                return str(parts[-1])
            return str(ref) if ref else None
        return None

    def _resolve_type(self, schema: dict[str, Any]) -> str:
        """Resolve the type of a schema node."""
        if "$ref" in schema:
            ref_name = self._resolve_ref(schema)
            return f"ref:{ref_name}" if ref_name else "object"

        # Handle type arrays: {"type": ["string", "null"]}
        schema_type = schema.get("type", "string")
        if isinstance(schema_type, list):
            # Filter out "null" for the primary type
            non_null = [t for t in schema_type if t != "null"]
            return non_null[0] if non_null else "string"

        if schema_type == "array" and "items" in schema:
            items = schema.get("items", {})
            if isinstance(items, dict):
                item_type = self._resolve_type(items)
                return f"array<{item_type}>"

        # Handle allOf/oneOf/anyOf
        for combinator in ("allOf", "oneOf", "anyOf"):
            if combinator in schema:
                sub_schemas = schema[combinator]
                if isinstance(sub_schemas, list) and sub_schemas:
                    first = sub_schemas[0]
                    if isinstance(first, dict):
                        return self._resolve_type(first)
                return "object"

        if isinstance(schema_type, str):
            return schema_type

        return "string"

    def _get_example(self, schema: dict[str, Any]) -> Any:
        """Extract an example value from a schema if present."""
        if "example" in schema:
            return schema["example"]
        if "default" in schema:
            return schema["default"]
        return None
