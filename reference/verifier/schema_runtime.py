#!/usr/bin/env python3
"""AIFC Verifier A runtime JSON Schema admission.

Order enforced by the caller:
    exact stored bytes -> canonicalization -> content hash -> JSON Schema -> semantic replay

Schemas are loaded only from the tested repository tree. Network resolution is not
used. Relative $ref values resolve through each schema's canonical $id and the
local registry populated from schemas/*.schema.json.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource


class RuntimeSchemaError(ValueError):
    pass


@dataclass(frozen=True)
class SchemaCatalog:
    schemas_by_protocol_name: Mapping[str, Mapping[str, Any]]
    registry: Registry


_CATALOG: SchemaCatalog | None = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _schema_files() -> list[Path]:
    return sorted((_repo_root() / "schemas").glob("*.schema.json"))


def _load_catalog() -> SchemaCatalog:
    global _CATALOG
    if _CATALOG is not None:
        return _CATALOG

    by_protocol: dict[str, Mapping[str, Any]] = {}
    resources: list[tuple[str, Resource]] = []
    for path in _schema_files():
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # repository schema corruption is fatal
            raise RuntimeSchemaError(f"SCHEMA_FILE_PARSE_FAILED:{path.name}:{exc}") from exc
        if not isinstance(schema, Mapping):
            raise RuntimeSchemaError(f"SCHEMA_FILE_NOT_OBJECT:{path.name}")
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            raise RuntimeSchemaError(f"META_SCHEMA_REJECTED:{path.name}:{exc.message}") from exc
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            raise RuntimeSchemaError(f"SCHEMA_ID_MISSING:{path.name}")
        protocol_schema = schema.get("properties", {}).get("schema", {}).get("const")
        if isinstance(protocol_schema, str):
            if protocol_schema in by_protocol:
                raise RuntimeSchemaError(f"DUPLICATE_PROTOCOL_SCHEMA:{protocol_schema}")
            by_protocol[protocol_schema] = schema
        resources.append((schema_id, Resource.from_contents(schema)))

    registry = Registry().with_resources(resources)
    _CATALOG = SchemaCatalog(by_protocol, registry)
    return _CATALOG


def validate_protocol_object(value: Mapping[str, Any], expected_schema: str | None = None) -> None:
    catalog = _load_catalog()
    actual_schema = value.get("schema")
    if not isinstance(actual_schema, str):
        raise RuntimeSchemaError("PROTOCOL_SCHEMA_FIELD_MISSING")
    if expected_schema is not None and actual_schema != expected_schema:
        raise RuntimeSchemaError(f"EXPECTED_SCHEMA_MISMATCH:{expected_schema}:{actual_schema}")
    schema = catalog.schemas_by_protocol_name.get(actual_schema)
    if schema is None:
        raise RuntimeSchemaError(f"NO_LOCAL_RUNTIME_SCHEMA:{actual_schema}")

    validator = Draft202012Validator(
        schema,
        registry=catalog.registry,
        format_checker=FormatChecker(),
    )
    errors = sorted(validator.iter_errors(value), key=lambda e: (list(e.absolute_path), e.message))
    if errors:
        first = errors[0]
        path = "$" + "".join(
            f"[{part}]" if isinstance(part, int) else f".{part}" for part in first.absolute_path
        )
        raise RuntimeSchemaError(f"JSON_SCHEMA_REJECTED:{actual_schema}:{path}:{first.message}")


def validate_store_index(index: Mapping[str, Any]) -> None:
    validate_protocol_object(index, "AIFC/evidence-store-index/v1")
