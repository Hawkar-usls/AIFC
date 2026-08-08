#!/usr/bin/env python3
"""SAL v1.11 semantic authority contour candidate.

This is the only v1.11 contour that may return an authority decision. It never
treats authority labels inside successor resolver/derivation profiles as proof.
Authority can open only from separately replayed lineage inputs.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

@dataclass(frozen=True)
class SemanticAuthorityDecision:
    state: str
    blockers: tuple[str, ...]

def evaluate_derived_semantic_authority(
    *,
    resolver_authority_lineage_replay_status: str,
    derivation_profile_authority_lineage_replay_status: str,
    resolved_leaf_authority_states: Sequence[str],
    derived_authority_lineage_replay_status: str,
) -> SemanticAuthorityDecision:
    blockers:list[str]=[]
    if resolver_authority_lineage_replay_status != "AUTHORITY_LINEAGE_REPLAY_PASS":
        blockers.append("BLOCKED_CANONICAL_SEMANTIC_RESOLVER_AUTHORITY")
    if not resolved_leaf_authority_states or any(x != "AUTHORITY_ADMISSIBLE" for x in resolved_leaf_authority_states):
        blockers.append("BLOCKED_DERIVED_SOURCE_AUTHORITY_RESOLUTION")
    if derivation_profile_authority_lineage_replay_status != "AUTHORITY_LINEAGE_REPLAY_PASS":
        blockers.append("BLOCKED_DERIVATION_PROFILE_AUTHORITY")
    if derived_authority_lineage_replay_status != "AUTHORITY_LINEAGE_REPLAY_PASS":
        blockers.append("BLOCKED_DERIVED_AUTHORITY_LINEAGE_REPLAY")
    return SemanticAuthorityDecision("AUTHORITY_ADMISSIBLE" if not blockers else "BLOCKED", tuple(blockers))
