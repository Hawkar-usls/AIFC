#!/usr/bin/env python3
"""Exact implementation boundary for AIFC inherited-gate obligation hash v1.

This module does not change the historical hash domain. It exists so the
implementation source can receive an immutable content identity independent of
the broader SAL resolver/comparator module.
"""
from __future__ import annotations

import hashlib
from typing import Any, Mapping

from canonical import canonical_json_bytes
from schema_runtime import RuntimeSchemaError, validate_protocol_object

INHERITED_GATE_HASH_PROFILE_ID = "AIFC-INHERITED-GATE-OBLIGATION-HASH-V1"
INHERITED_GATE_HASH_DOMAIN = b"AIFC:INHERITED-GATE-OBLIGATION-SET:v1\x00"


class InheritedGateHashError(ValueError):
    pass


def inherited_gate_obligation_hash_v1(material: Mapping[str, Any]) -> str:
    try:
        validate_protocol_object(material, "AIFC/inherited-gate-obligation-set/v1")
    except RuntimeSchemaError as exc:
        raise InheritedGateHashError(
            f"INHERITED_GATE_OBLIGATION_SCHEMA_INVALID:{exc}"
        ) from exc
    return hashlib.sha256(INHERITED_GATE_HASH_DOMAIN + canonical_json_bytes(material)).hexdigest()
