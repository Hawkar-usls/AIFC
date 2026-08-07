#!/usr/bin/env python3
"""AIFC Verifier A provisional canonicalization and protocol-hash backend.

This implementation is intentionally stricter than ordinary json.loads/json.dumps:
- UTF-8 only, no BOM;
- duplicate object keys rejected;
- all strings and keys must already be NFC;
- floating-point JSON numbers and NaN/Infinity rejected;
- JSON integers restricted to the interoperable IEEE-754 exact range;
- object keys ordered by UTF-16 code units before compact UTF-8 serialization.

This backend is suitable for Verifier A replay development but does NOT establish
BYTE_IDENTICAL_CANONICALIZATION. A second independent implementation and a frozen
cross-language crucible remain mandatory before AIFC v1.0 FROZEN.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unicodedata
from typing import Any, Mapping

MAX_SAFE_INTEGER = 9007199254740991
MIN_SAFE_INTEGER = -MAX_SAFE_INTEGER

DOMAIN_BY_SCHEMA = {
    "AIFC/hard-witness/v1": "AIFC:HARD_WITNESS:v1",
    "AIFC/candidate-set/v1": "AIFC:CANDIDATE_SET:v1",
    "AIFC/pre-return-certificate/v1": "AIFC:PRE_RETURN_CERTIFICATE:v1",
    "AIFC/trial-ledger-event/v1": "AIFC:TRIAL_LEDGER_EVENT:v1",
    "AIFC/trial-creation-policy/v1": "AIFC:TRIAL_CREATION_POLICY:v1",
    "AIFC/experiment-plan/v1": "AIFC:EXPERIMENT_PLAN:v1",
    "AIFC/candidate-generation-policy/v1": "AIFC:CANDIDATE_GENERATION_POLICY:v1",
    "AIFC/candidate-generation-profile/v1": "AIFC:CANDIDATE_GENERATION_PROFILE:v1",
    "AIFC/target-selector-policy/v1": "AIFC:TARGET_SELECTOR_POLICY:v1",
    "AIFC/target-selector-profile/v1": "AIFC:TARGET_SELECTOR_PROFILE:v1",
    "AIFC/target-derivation-policy/v1": "AIFC:TARGET_DERIVATION_POLICY:v1",
    "AIFC/target-derivation-profile/v1": "AIFC:TARGET_DERIVATION_PROFILE:v1",
    "AIFC/conditioning-view-policy/v1": "AIFC:CONDITIONING_VIEW_POLICY:v1",
    "AIFC/pre-target-conditioning-view/v1": "AIFC:PRE_TARGET_CONDITIONING_VIEW:v1",
    "AIFC/entropy-policy/v1": "AIFC:ENTROPY_POLICY:v1",
    "AIFC/entropy-profile/v1": "AIFC:ENTROPY_PROFILE:v1",
    "AIFC/signature-preimage-policy/v1": "AIFC:SIGNATURE_PREIMAGE_POLICY:v1",
    "AIFC/causal-model/v1": "AIFC:CAUSAL_MODEL:v1",
    "AIFC/statistical-plan/v1": "AIFC:STATISTICAL_PLAN:v1",
    "AIFC/eprocess-state/v1": "AIFC:EPROCESS_STATE:v1",
    "AIFC/witness-registry/v1": "AIFC:WITNESS_REGISTRY:v1",
    "AIFC/witness-receipt/v1": "AIFC:WITNESS_RECEIPT:v1",
    "AIFC/quorum-certificate/v1": "AIFC:QUORUM_CERTIFICATE:v1",
    "AIFC/registry-transition-body/v1": "AIFC:REGISTRY_TRANSITION_BODY:v1",
    "AIFC/registry-transition-receipt/v1": "AIFC:REGISTRY_TRANSITION_RECEIPT:v1",
    "AIFC/registry-transition-quorum/v1": "AIFC:REGISTRY_TRANSITION_QUORUM:v1",
    "AIFC/registry-transition-certificate/v1": "AIFC:REGISTRY_TRANSITION_CERTIFICATE:v1",
    "AIFC/external-freshness-policy/v1": "AIFC:EXTERNAL_FRESHNESS_POLICY:v1",
    "AIFC/publication-policy/v1": "AIFC:PUBLICATION_POLICY:v1",
    "AIFC/publication-manifest/v1": "AIFC:PUBLICATION_MANIFEST:v1",
    "AIFC/target-evidence/v1": "AIFC:TARGET_EVIDENCE:v1",
    "AIFC/evidence-bundle/v1": "AIFC:EVIDENCE_BUNDLE:v1",
    "AIFC/verifier-result/v1": "AIFC:VERIFIER_RESULT:v1",
    "AIFC/release-manifest/v1": "AIFC:RELEASE_MANIFEST:v1",
    "AIFC/evidence-store-index/v1": "AIFC:EVIDENCE_STORE_INDEX:v1",
}


class CanonicalizationError(ValueError):
    pass


def _reject_float(value: str) -> None:
    raise CanonicalizationError(f"floating-point JSON number forbidden: {value}")


def _reject_constant(value: str) -> None:
    raise CanonicalizationError(f"non-finite JSON number forbidden: {value}")


def _parse_int(value: str) -> int:
    n = int(value, 10)
    if n < MIN_SAFE_INTEGER or n > MAX_SAFE_INTEGER:
        raise CanonicalizationError(
            f"JSON integer outside interoperable range [{MIN_SAFE_INTEGER},{MAX_SAFE_INTEGER}]: {value}"
        )
    return n


def _object_pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise CanonicalizationError(f"duplicate JSON object key: {key!r}")
        out[key] = value
    return out


def loads_strict(text: str) -> Any:
    if text.startswith("\ufeff"):
        raise CanonicalizationError("UTF-8 BOM forbidden")
    try:
        obj = json.loads(
            text,
            object_pairs_hook=_object_pairs_no_duplicates,
            parse_int=_parse_int,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except CanonicalizationError:
        raise
    except (json.JSONDecodeError, UnicodeError, ValueError) as exc:
        raise CanonicalizationError(str(exc)) from exc
    validate_value(obj)
    return obj


def load_json_strict(path: str | Path) -> Any:
    raw = Path(path).read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise CanonicalizationError("UTF-8 BOM forbidden")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise CanonicalizationError(f"invalid UTF-8: {exc}") from exc
    return loads_strict(text)


def _validate_string(value: str, where: str) -> None:
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise CanonicalizationError(f"invalid Unicode scalar sequence at {where}: {exc}") from exc
    if unicodedata.normalize("NFC", value) != value:
        raise CanonicalizationError(f"non-NFC string at {where}")


def validate_value(value: Any, where: str = "$") -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if value < MIN_SAFE_INTEGER or value > MAX_SAFE_INTEGER:
            raise CanonicalizationError(f"integer outside interoperable range at {where}: {value}")
        return
    if isinstance(value, float):
        raise CanonicalizationError(f"floating-point value forbidden at {where}")
    if isinstance(value, str):
        _validate_string(value, where)
        return
    if isinstance(value, list):
        for i, item in enumerate(value):
            validate_value(item, f"{where}[{i}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError(f"non-string object key at {where}")
            _validate_string(key, f"{where}.<key>")
            validate_value(item, f"{where}.{key}")
        return
    raise CanonicalizationError(f"unsupported value type at {where}: {type(value).__name__}")


def _utf16_sort_key(value: str) -> bytes:
    return value.encode("utf-16-be", errors="strict")


def _ordered(value: Any) -> Any:
    if isinstance(value, list):
        return [_ordered(v) for v in value]
    if isinstance(value, dict):
        return {key: _ordered(value[key]) for key in sorted(value.keys(), key=_utf16_sort_key)}
    return value


def canonical_json_bytes(value: Any) -> bytes:
    validate_value(value)
    ordered = _ordered(value)
    text = json.dumps(
        ordered,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=False,
    )
    return text.encode("utf-8", errors="strict")


def domain_hash(separator: str, value: Any) -> str:
    if not isinstance(separator, str) or not separator:
        raise CanonicalizationError("domain separator must be a non-empty string")
    try:
        sep = separator.encode("ascii", errors="strict")
    except UnicodeEncodeError as exc:
        raise CanonicalizationError("domain separator must be ASCII") from exc
    return hashlib.sha256(sep + b"\x00" + canonical_json_bytes(value)).hexdigest()


def protocol_hash(value: Mapping[str, Any]) -> str:
    schema = value.get("schema")
    separator = DOMAIN_BY_SCHEMA.get(schema)
    if separator is None:
        raise CanonicalizationError(f"no frozen AIFC domain separator for schema {schema!r}")
    return domain_hash(separator, value)


def raw_evidence_hash(raw: bytes) -> str:
    return hashlib.sha256(b"AIFC:RAW_EVIDENCE:v1\x00" + raw).hexdigest()
