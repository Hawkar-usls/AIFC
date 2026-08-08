#!/usr/bin/env python3
"""SAL v1.11u machine derivation of the cross-vertex identity-reference edge universe.

The universe is derived from exact vertex objects under a content-identified extraction
profile. No required-edge list is accepted from the caller or receipt. This module
does not make semantic-authority decisions and does not claim completeness outside
the inherited v1.11h six-vertex scope.
"""
from __future__ import annotations
from typing import Any, Mapping, Sequence
from canonical import domain_hash

PROFILE_DOMAIN = "AIFC:LINEAGE-EDGE-UNIVERSE-DERIVATION-PROFILE:v1"
UNIVERSE_DOMAIN = "AIFC:LINEAGE-EDGE-UNIVERSE:v1"
RECEIPT_DOMAIN = "AIFC:DERIVED-SEMANTIC-LINEAGE-EDGE-UNIVERSE:v1"

class LineageEdgeUniverseV1Error(ValueError):
    pass

def profile_content_hash(obj: Mapping[str, Any]) -> str:
    material = dict(obj)
    material.pop("profile_content_hash", None)
    return domain_hash(PROFILE_DOMAIN, material)

def universe_content_hash(obj: Mapping[str, Any]) -> str:
    material = dict(obj)
    material.pop("universe_content_hash", None)
    return domain_hash(RECEIPT_DOMAIN, material)

def _ptr_escape(key: str) -> str:
    return key.replace("~", "~0").replace("/", "~1")

def _utf16_key(value: str) -> bytes:
    return value.encode("utf-16-be", errors="strict")

def iter_string_scalars(value: Any, path: str = ""):
    if isinstance(value, str):
        yield path or "/", value
        return
    if isinstance(value, list):
        for i, item in enumerate(value):
            yield from iter_string_scalars(item, f"{path}/{i}")
        return
    if isinstance(value, Mapping):
        for key in sorted(value.keys(), key=_utf16_key):
            if not isinstance(key, str):
                raise LineageEdgeUniverseV1Error("EDGE_UNIVERSE_NON_STRING_OBJECT_KEY")
            yield from iter_string_scalars(value[key], f"{path}/{_ptr_escape(key)}")

def _validate_profile(profile: Mapping[str, Any], objects: Mapping[str, Mapping[str, Any]]) -> tuple[str, ...]:
    if profile.get("schema") != "AIFC/lineage-edge-universe-derivation-profile/v1":
        raise LineageEdgeUniverseV1Error("EDGE_UNIVERSE_PROFILE_SCHEMA_REBINDING")
    if profile.get("profile_content_hash") != profile_content_hash(profile):
        raise LineageEdgeUniverseV1Error("EDGE_UNIVERSE_PROFILE_CONTENT_REBINDING")
    if profile.get("scope") != "INHERITED_V1_11H_SIX_VERTEX_CROSS_VERTEX_IDENTITY_REFERENCE_SCOPE_V1":
        raise LineageEdgeUniverseV1Error("EDGE_UNIVERSE_SCOPE_REBINDING")
    if profile.get("reference_extraction_semantics") != "RECURSIVE_STRING_SCALAR_EXACT_MATCH_TO_TARGET_IDENTITY_CHANNELS_V1":
        raise LineageEdgeUniverseV1Error("EDGE_UNIVERSE_EXTRACTION_SEMANTICS_REBINDING")
    if profile.get("path_semantics") != "CANONICAL_JSON_POINTER_OVER_UTF16_SORTED_OBJECT_KEYS_AND_ARRAY_INDICES_V1":
        raise LineageEdgeUniverseV1Error("EDGE_UNIVERSE_PATH_SEMANTICS_REBINDING")
    if profile.get("edge_grouping_semantics") != "COLLAPSE_BY_SOURCE_VERTEX_TARGET_VERTEX_TARGET_IDENTITY_CHANNEL_V1":
        raise LineageEdgeUniverseV1Error("EDGE_UNIVERSE_GROUPING_SEMANTICS_REBINDING")
    if profile.get("self_reference_policy") != "EXCLUDE_SOURCE_EQUALS_TARGET_VERTEX_V1":
        raise LineageEdgeUniverseV1Error("EDGE_UNIVERSE_SELF_REFERENCE_POLICY_REBINDING")
    if profile.get("unmatched_reference_policy") != "OUT_OF_SCOPE_NOT_EVIDENCE_OF_ABSENCE_V1":
        raise LineageEdgeUniverseV1Error("EDGE_UNIVERSE_OUT_OF_SCOPE_POLICY_REBINDING")
    keys = profile.get("vertex_keys")
    if not isinstance(keys, list) or len(keys) != len(set(keys)) or set(keys) != set(objects):
        raise LineageEdgeUniverseV1Error("EDGE_UNIVERSE_VERTEX_SCOPE_REBINDING")
    channels = profile.get("target_identity_channels")
    if not isinstance(channels, Mapping) or set(channels) != set(keys):
        raise LineageEdgeUniverseV1Error("EDGE_UNIVERSE_TARGET_CHANNEL_SCOPE_REBINDING")
    return tuple(str(x) for x in keys)

def derive_edge_universe(
    objects: Mapping[str, Mapping[str, Any]],
    profile: Mapping[str, Any],
) -> tuple[Mapping[str, Any], ...]:
    keys = _validate_profile(profile, objects)
    channels = profile["target_identity_channels"]
    target_by_value: dict[str, list[tuple[str, str]]] = {}
    for target in keys:
        fields = channels[target]
        if not isinstance(fields, list) or not fields or len(fields) != len(set(fields)):
            raise LineageEdgeUniverseV1Error(f"EDGE_UNIVERSE_TARGET_CHANNEL_INVALID:{target}")
        for channel in fields:
            if not isinstance(channel, str) or not channel:
                raise LineageEdgeUniverseV1Error(f"EDGE_UNIVERSE_TARGET_CHANNEL_INVALID:{target}")
            value = objects[target].get(channel)
            if not isinstance(value, str) or not value:
                raise LineageEdgeUniverseV1Error(f"EDGE_UNIVERSE_TARGET_IDENTITY_MISSING:{target}:{channel}")
            target_by_value.setdefault(value, []).append((target, channel))

    grouped: dict[tuple[str, str, str, str], list[str]] = {}
    for source in keys:
        for path, value in iter_string_scalars(objects[source]):
            for target, channel in target_by_value.get(value, ()):
                if source == target:
                    continue
                grouped.setdefault((source, target, channel, value), []).append(path)

    out = []
    for source, target, channel, value in sorted(grouped):
        loci = sorted(set(grouped[(source, target, channel, value)]))
        out.append({
            "edge_key": f"{source}->{target}#{channel}",
            "source_vertex_key": source,
            "target_vertex_key": target,
            "target_identity_channel": channel,
            "matched_identity_value": value,
            "reference_loci": loci,
        })
    return tuple(out)

def edge_universe_hash(edges: Sequence[Mapping[str, Any]]) -> str:
    return domain_hash(UNIVERSE_DOMAIN, list(edges))

def verify_universe_receipt(
    receipt: Mapping[str, Any],
    objects: Mapping[str, Mapping[str, Any]],
    profile: Mapping[str, Any],
) -> tuple[tuple[Mapping[str, Any], ...], str]:
    if receipt.get("schema") != "AIFC/derived-semantic-lineage-edge-universe/v1":
        raise LineageEdgeUniverseV1Error("EDGE_UNIVERSE_RECEIPT_SCHEMA_REBINDING")
    derived = derive_edge_universe(objects, profile)
    if receipt.get("derived_edges") != list(derived):
        raise LineageEdgeUniverseV1Error("LINEAGE_REQUIRED_EDGE_UNIVERSE_OMISSION_OR_INJECTION")
    if receipt.get("derived_edge_count") != len(derived):
        raise LineageEdgeUniverseV1Error("LINEAGE_EDGE_UNIVERSE_COUNT_REBINDING")
    uh = edge_universe_hash(derived)
    if receipt.get("edge_universe_hash") != uh:
        raise LineageEdgeUniverseV1Error("LINEAGE_EDGE_UNIVERSE_HASH_REBINDING")
    if receipt.get("universe_content_hash") != universe_content_hash(receipt):
        raise LineageEdgeUniverseV1Error("LINEAGE_EDGE_UNIVERSE_CONTENT_REBINDING")
    return derived, uh
