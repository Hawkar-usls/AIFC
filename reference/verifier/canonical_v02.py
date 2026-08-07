#!/usr/bin/env python3
"""AIFC Verifier A v0.2 extended protocol-domain registry.

Temporary compatibility layer while the draft protocol surface is still moving.
It reuses the already-tested canonical byte engine and extends only the schema ->
domain mapping for newly introduced experiment-scoped plan-freeze objects.
"""
from __future__ import annotations

from typing import Any, Mapping

from canonical import (
    CanonicalizationError,
    DOMAIN_BY_SCHEMA as BASE_DOMAINS,
    canonical_json_bytes,
    domain_hash,
    load_json_strict,
    loads_strict,
    raw_evidence_hash,
    validate_value,
)

DOMAIN_BY_SCHEMA_V02 = dict(BASE_DOMAINS)
DOMAIN_BY_SCHEMA_V02.update({
    "AIFC/experiment-plan-receipt/v1": "AIFC:EXPERIMENT_PLAN_RECEIPT:v1",
    "AIFC/experiment-plan-quorum/v1": "AIFC:EXPERIMENT_PLAN_QUORUM:v1",
})


def protocol_hash_v02(value: Mapping[str, Any]) -> str:
    schema = value.get("schema")
    separator = DOMAIN_BY_SCHEMA_V02.get(schema)
    if separator is None:
        raise CanonicalizationError(f"no AIFC v0.2 domain separator for schema {schema!r}")
    return domain_hash(separator, value)
