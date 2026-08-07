#!/usr/bin/env python3
"""AIFC repository-level draft conformance checks.

This is deliberately NOT the scientific verifier. It checks that the repository
contains the current draft protocol surface and that selected fail-closed
contracts cannot silently drift. Scientific admission remains a separate replay
and release-manifest problem.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_FILES = [
    "schemas/hard-witness.schema.json",
    "schemas/candidate-set.schema.json",
    "schemas/pre-return-certificate.schema.json",
    "schemas/trial-ledger-event.schema.json",
    "schemas/trial-creation-policy.schema.json",
    "schemas/experiment-plan.schema.json",
    "schemas/candidate-generation-policy.schema.json",
    "schemas/candidate-generation-profile.schema.json",
    "schemas/target-selector-policy.schema.json",
    "schemas/target-selector-profile.schema.json",
    "schemas/target-derivation-policy.schema.json",
    "schemas/target-derivation-profile.schema.json",
    "schemas/conditioning-view-policy.schema.json",
    "schemas/pre-target-conditioning-view.schema.json",
    "schemas/entropy-policy.schema.json",
    "schemas/entropy-profile.schema.json",
    "schemas/causal-model.schema.json",
    "schemas/statistical-plan.schema.json",
    "schemas/eprocess-state.schema.json",
    "schemas/witness-registry.schema.json",
    "schemas/witness-receipt.schema.json",
    "schemas/quorum-certificate.schema.json",
    "schemas/registry-transition-body.schema.json",
    "schemas/registry-transition-receipt.schema.json",
    "schemas/registry-transition-quorum.schema.json",
    "schemas/registry-transition-certificate.schema.json",
    "schemas/external-freshness-policy.schema.json",
    "schemas/publication-policy.schema.json",
    "schemas/publication-manifest.schema.json",
    "schemas/target-evidence.schema.json",
    "schemas/evidence-bundle.schema.json",
    "schemas/evidence-store-index.schema.json",
    "schemas/replay-package.schema.json",
    "schemas/verifier-result.schema.json",
    "schemas/release-manifest.schema.json",
]

REQUIRED_FILES = [
    "README.md",
    "CITATION.cff",
    ".zenodo.json",
    "ROADMAP.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "spec/AIFC-SPEC-v1.0-draft.md",
    "spec/STATE_MACHINE.md",
    "spec/CANONICALIZATION.md",
    "spec/WITNESS_LIFECYCLE.md",
    "spec/TIME_AND_ORDERING.md",
    "docs/TRIAL_LEDGER.md",
    "docs/CANDIDATE_PROVENANCE.md",
    "docs/ENTROPY_EVIDENCE.md",
    "docs/TARGET_DERIVATION.md",
    "docs/CAUSAL_MODEL.md",
    "docs/RELEASE_MANIFEST.md",
    "conformance/state-machine-v1.json",
    "conformance/AIFC-RELEASE-GATE-v1.json",
    "conformance/VERIFIER-A-FRONTIER-v0.1.json",
    "conformance/VERIFIER-A-REPLAY-v0.2.json",
    "reference/verifier/canonical.py",
    "reference/verifier/frontier.py",
    "reference/verifier/bindings.py",
    "reference/verifier/resolver.py",
    "reference/verifier/replay.py",
    "reference/verifier/replay_engine.py",
    "reference/verifier/aifc_verify.py",
    "reference/tests/test_frontier.py",
    "reference/tests/test_replay.py",
] + SCHEMA_FILES

EXPECTED_SCHEMA_IDS = {rel: f"https://github.com/Hawkar-usls/AIFC/{rel}" for rel in SCHEMA_FILES}

EXPECTED_RELEASE_GATES = {
    "SPEC_SCHEMA_VALID",
    "STATE_MACHINE_VALID",
    "EXPERIMENT_PLAN_VALID",
    "TRIAL_CREATION_POLICY_VALID",
    "TRIAL_LEDGER_CONTINUITY",
    "LEDGER_GENESIS_SENTINEL_VALID",
    "CANDIDATE_SET_RECOMPUTED",
    "CANDIDATE_GENERATION_PROVENANCE_VALID",
    "POST_CREATED_OPERATOR_CHOICE_EXCLUDED",
    "PRE_TARGET_CONDITIONING_VIEW_VALID",
    "TARGET_SELECTOR_PROFILE_VALID",
    "TARGET_DERIVATION_PROFILE_VALID",
    "TARGET_DERIVATION_BYTE_REPLAY",
    "ENTROPY_POLICY_VALID",
    "ENTROPY_PROFILE_VALID",
    "CANONICAL_RATIONAL_VALID",
    "EVIDENCE_RESOLVER_PASS",
    "CAUSAL_MODEL_VALID",
    "CAUSAL_EVIDENCE_RESOLUTION",
    "WITNESS_LIFECYCLE_VALID",
    "WITNESS_FAILURE_DOMAIN_INDEPENDENCE",
    "REGISTRY_TRANSITION_VALID",
    "STATISTICAL_PLAN_VALID",
    "STATISTICAL_ENGINE_REPLAY",
    "PUBLICATION_MANIFEST_VALID",
    "COMPLETE_TRIAL_PUBLICATION",
    "CITATION_ZENODO_METADATA_SYNC",
    "ALL_HONEST_VECTORS_PASS",
    "ALL_ATTACK_VECTORS_EXPECTED_REJECTION",
    "IMPLEMENTATION_A_PASS",
    "IMPLEMENTATION_B_PASS",
    "BYTE_IDENTICAL_CANONICALIZATION",
    "FAIL_OPEN_ZERO",
    "RELEASE_ASSET_CHOREOGRAPHY_VALID",
    "RELEASE_MANIFEST_PROOF_CARRYING",
    "RELEASE_MANIFEST_EVIDENCE_RESOLUTION",
    "TARGET_SOURCE_CRYPTOGRAPHIC_PROOF",
    "EXTERNAL_BENCH_EVIDENCE_ROOTED_OUTSIDE_GENESIS",
}


def die(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def load_json(rel: str):
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception as exc:
        die(f"cannot parse {rel}: {exc}")


def cff_scalar(text: str, key: str) -> str:
    m = re.search(rf"(?m)^{re.escape(key)}:\s*(?:\"([^\"]*)\"|'([^']*)'|([^\n#]+))\s*$", text)
    if not m:
        die(f"missing CFF scalar {key}")
    return next(x for x in m.groups() if x is not None).strip()


def require_keys(obj: dict, required: tuple[str, ...], label: str) -> None:
    missing = [key for key in required if key not in obj.get("required", [])]
    if missing:
        die(f"{label} missing required bindings: {', '.join(missing)}")


def check_required_files() -> None:
    missing = [p for p in REQUIRED_FILES if not (ROOT / p).is_file()]
    if missing:
        die("missing required files: " + ", ".join(missing))
    print(f"REQUIRED_FILES = PASS ({len(REQUIRED_FILES)}/{len(REQUIRED_FILES)})")


def check_schema_headers() -> None:
    for rel in SCHEMA_FILES:
        obj = load_json(rel)
        if obj.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            die(f"{rel}: wrong JSON Schema dialect")
        if obj.get("$id") != EXPECTED_SCHEMA_IDS[rel]:
            die(f"{rel}: unexpected $id")
        if obj.get("type") != "object" or obj.get("additionalProperties") is not False:
            die(f"{rel}: hash-critical top-level schema must be a closed object")
    print(f"SCHEMA_HEADERS = PASS ({len(SCHEMA_FILES)}/{len(SCHEMA_FILES)})")


def check_hardening_contracts() -> None:
    candidate_set = load_json("schemas/candidate-set.schema.json")
    require_keys(candidate_set, ("hard_witness_hashes", "cardinality"), "candidate set")

    candidate_policy = load_json("schemas/candidate-generation-policy.schema.json")
    props = candidate_policy["properties"]
    if props["operator_choice_after_created_policy"].get("const") != "FORBIDDEN_FOR_STRONGEST_GRADE_V1":
        die("strongest-grade post-CREATED operator choice must remain forbidden")

    candidate_profile = load_json("schemas/candidate-generation-profile.schema.json")
    require_keys(candidate_profile, ("policy_hash", "created_slot_certificate_hash", "candidate_set_cardinality_upper_bound"), "candidate profile")
    selection = candidate_profile["properties"]["selection_freedom"]["properties"]
    if selection["operator_choice_after_created"].get("const") is not False:
        die("candidate profile must fail closed on post-CREATED operator choice")

    plan = load_json("schemas/experiment-plan.schema.json")
    require_keys(plan, (
        "trial_creation_policy_hash",
        "candidate_generation_policy_hash",
        "target_selector_policy_hash",
        "target_derivation_policy_hash",
        "entropy_policy_hash",
        "causal_model_hash",
        "statistical_plan_hash",
        "publication_policy_hash",
        "external_freshness_policy_hash",
        "conditioning_view_policy_hash",
    ), "experiment plan")

    pre = load_json("schemas/pre-return-certificate.schema.json")
    require_keys(pre, (
        "experiment_plan_hash",
        "candidate_generation_profile_hash",
        "target_selector_policy_hash",
        "target_derivation_policy_hash",
    ), "PRE_RETURN")
    if "target_derivation_profile_hash" in pre.get("properties", {}):
        die("PRE_RETURN must bind derivation policy, not a later concrete derivation instance")

    selector = load_json("schemas/target-selector-profile.schema.json")
    require_keys(selector, ("policy_hash", "anchor_hash", "selected_event_id", "selection_transcript_hash"), "target selector")
    if selector["properties"]["alternative_selected_events"].get("maxItems") != 0:
        die("strongest-grade selector must permit exactly one selected event")

    derivation = load_json("schemas/target-derivation-profile.schema.json")
    require_keys(derivation, ("policy_hash", "target_selector_profile_hash", "extraction", "transformation"), "target derivation")
    algorithms = derivation["properties"]["transformation"]["properties"]["algorithm"].get("enum", [])
    if set(algorithms) != {"IDENTITY", "SHA-256"}:
        die("strongest-grade target derivation algorithm set drift")
    if "profile_hash" in derivation.get("properties", {}):
        die("target derivation must not contain self-hash field")

    view = load_json("schemas/pre-target-conditioning-view.schema.json")
    require_keys(view, (
        "ledger_head_hash",
        "target_selector_profile_hash",
        "target_derivation_profile_hash",
        "operator_state_evidence_hashes",
        "source_state_evidence_hashes",
    ), "pre-target conditioning view")
    if "certification_quorum_hash" in view.get("properties", {}):
        die("pre-target conditioning view must not contain its own quorum hash")

    entropy_policy = load_json("schemas/entropy-policy.schema.json")
    require_keys(entropy_policy, (
        "source_id",
        "source_protocol_version",
        "allowed_derivation_methods",
        "required_external_evidence_types",
        "post_target_method_selection_forbidden",
    ), "entropy policy")
    if entropy_policy["properties"]["post_target_method_selection_forbidden"].get("const") is not True:
        die("entropy policy must forbid post-target method selection")

    entropy = load_json("schemas/entropy-profile.schema.json")
    rat = entropy["properties"]["point_probability_upper_bound"]["properties"]
    if rat["numerator_dec"].get("pattern") != r"^(0|[1-9][0-9]*)$":
        die("canonical rational numerator grammar drift")
    if rat["denominator_dec"].get("pattern") != r"^[1-9][0-9]*$":
        die("canonical rational denominator grammar drift")
    require_keys(entropy, ("target_selector_profile_hash", "target_derivation_profile_hash", "conditioning_view_hash"), "entropy profile")

    causal = load_json("schemas/causal-model.schema.json")
    require_keys(causal, ("experiment_id", "edges", "no_edge_claims", "unresolved_assumptions"), "causal model")
    edge_items = causal["properties"]["edges"]["items"]
    if "evidence_hashes" not in edge_items.get("required", []):
        die("causal edge claims must carry evidence hashes")

    statistical = load_json("schemas/statistical-plan.schema.json")
    if statistical["properties"]["target_derivation_rule"].get("const") != "EXACTLY_ONE_ADMITTED_TARGET_DERIVATION_PER_TRIAL":
        die("statistical plan must freeze exactly one target derivation per trial")

    quorum = load_json("schemas/quorum-certificate.schema.json")
    if quorum["properties"]["receipts"].get("items", {}).get("$ref") != "witness-receipt.schema.json":
        die("quorum receipts must $ref witness-receipt schema")

    registry = load_json("schemas/witness-registry.schema.json")
    fault_props = registry["properties"]["fault_model"]["properties"]
    if fault_props["independence_unit"].get("const") != "FAILURE_DOMAIN":
        die("witness independence unit must remain FAILURE_DOMAIN")
    if "transition_certificate_hash" not in registry.get("properties", {}):
        die("witness registry missing transition certificate binding")

    transition = load_json("schemas/registry-transition-certificate.schema.json")
    tprops = transition.get("properties", {})
    if tprops.get("transition_body", {}).get("$ref") != "registry-transition-body.schema.json":
        die("registry transition must bind typed transition body")
    if tprops.get("old_registry_authorization", {}).get("$ref") != "registry-transition-quorum.schema.json":
        die("old registry transition authorization must use experiment-scoped quorum")
    if tprops.get("new_registry_acceptance", {}).get("$ref") != "registry-transition-quorum.schema.json":
        die("new registry transition acceptance must use experiment-scoped quorum")

    target = load_json("schemas/target-evidence.schema.json")
    require_keys(target, (
        "target_selector_profile_hash",
        "target_derivation_profile_hash",
        "conditioning_view_hash",
        "raw_source_object_hash",
    ), "target evidence")

    bundle = load_json("schemas/evidence-bundle.schema.json")
    require_keys(bundle, (
        "experiment_plan_hash",
        "candidate_set_hash",
        "target_selector_profile_hash",
        "target_derivation_profile_hash",
        "conditioning_view_hash",
        "statistical_plan_hash",
    ), "evidence bundle")
    if "publication_manifest_hash" in bundle.get("properties", {}):
        die("per-trial evidence bundle must not point forward to publication manifest")

    publication = load_json("schemas/publication-manifest.schema.json")
    require_keys(publication, ("final_ledger_head_hash", "trial_records", "external_publication_root_hash"), "publication manifest")

    resolver_schema = load_json("schemas/evidence-store-index.schema.json")
    require_keys(resolver_schema, ("store_id", "entries"), "evidence store index")

    replay_package = load_json("schemas/replay-package.schema.json")
    require_keys(replay_package, (
        "experiment_plan_hash",
        "ledger_event_hashes",
        "evidence_bundle_hash",
        "pre_target_conditioning_view_hash",
        "publication_manifest_hash",
    ), "replay package")
    if "evidence_bundle" in replay_package.get("properties", {}):
        die("replay package must be content-addressed, not embed producer evidence objects")

    release_manifest = load_json("schemas/release-manifest.schema.json")
    require_keys(release_manifest, ("source_commit", "gate_results", "delivery_mode"), "release manifest")
    if "repository_commit" in release_manifest.get("properties", {}):
        die("release manifest must use two-stage source_commit choreography")
    if release_manifest["properties"]["delivery_mode"].get("const") != "OUT_OF_TREE_RELEASE_ASSET_BOUND_TO_IMMUTABLE_SOURCE_COMMIT":
        die("release manifest delivery choreography drift")
    if "manifest_hash" in release_manifest.get("properties", {}):
        die("release manifest must not contain self-hash field")

    resolver_source = (ROOT / "reference/verifier/resolver.py").read_text(encoding="utf-8")
    for token in ("DANGLING_EVIDENCE_HASH", "NONCANONICAL_STORED_PROTOCOL_BYTES", "PROTOCOL_OBJECT_HASH_MISMATCH"):
        if token not in resolver_source:
            die(f"evidence resolver missing fail-closed path: {token}")

    replay_sources = (
        (ROOT / "reference/verifier/replay.py").read_text(encoding="utf-8")
        + (ROOT / "reference/verifier/replay_engine.py").read_text(encoding="utf-8")
    )
    for token in (
        "POST_HOC_CONDITIONING_VIEW_SANITIZATION",
        "FAULT_MODEL_REBINDING",
        "SAME_FAILURE_DOMAIN_SYBIL",
        "TARGET_DERIVATION_REPLAY",
        "PUBLICATION_MANIFEST_REPLAY",
    ):
        if token not in replay_sources:
            die(f"replay engine missing frontier failure path: {token}")

    ledger_doc = (ROOT / "docs/TRIAL_LEDGER.md").read_text(encoding="utf-8")
    if "AIFC:EXPERIMENT_GENESIS:v1" not in ledger_doc:
        die("ledger genesis sentinel rule missing")

    print("HARDENING_CONTRACTS = PASS")


def check_state_machine() -> None:
    sm = load_json("conformance/state-machine-v1.json")
    if sm.get("schema") != "AIFC/state-machine/v1":
        die("state machine schema mismatch")
    normal = [tuple(x) for x in sm.get("normal_transitions", [])]
    expected = [
        (None, "CREATED"),
        ("CREATED", "PRE_RETURN_FROZEN"),
        ("PRE_RETURN_FROZEN", "QUORUM_CERTIFIED"),
        ("QUORUM_CERTIFIED", "TARGET_ARMED"),
        ("TARGET_ARMED", "TARGET_OBSERVED"),
        ("TARGET_OBSERVED", "VERIFIED"),
        ("VERIFIED", "TERMINAL"),
    ]
    if normal != expected:
        die("normal state transition chain drift")
    forbidden = sm.get("forbidden", {})
    for key in (
        "silent_trial_deletion",
        "candidate_before_created_certified",
        "target_before_quorum_certified",
        "target_selection_after_observing_target",
        "terminal_to_nonterminal",
        "state_skip_without_terminal_abort",
    ):
        if forbidden.get(key) is not True:
            die(f"state-machine forbidden rule missing: {key}")
    print("STATE_MACHINE = PASS")


def check_release_gate() -> None:
    gate = load_json("conformance/AIFC-RELEASE-GATE-v1.json")
    ids = [x.get("id") for x in gate.get("required_checks", []) if x.get("required") is True]
    if len(ids) != len(set(ids)):
        die("duplicate required release gate id")
    if set(ids) != EXPECTED_RELEASE_GATES:
        missing = sorted(EXPECTED_RELEASE_GATES - set(ids))
        extra = sorted(set(ids) - EXPECTED_RELEASE_GATES)
        die(f"release gate required-check set drift; missing={missing}; extra={extra}")
    if gate.get("status") != "DRAFT_NOT_SATISFIED":
        die("draft repository must not self-assert frozen conformance")
    print(f"FROZEN_RELEASE_GATE = BLOCKED_AS_EXPECTED ({len(ids)} unmet evidence classes declared)")


def check_metadata_sync() -> None:
    z = load_json(".zenodo.json")
    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    cff_title = cff_scalar(cff, "title")
    cff_version = cff_scalar(cff, "version")
    cff_license = cff_scalar(cff, "license")
    if z.get("title") != cff_title:
        die("CITATION.cff and .zenodo.json title mismatch")
    if str(z.get("version")) != cff_version:
        die("CITATION.cff and .zenodo.json version mismatch")
    if z.get("license") != cff_license:
        die("CITATION.cff and .zenodo.json license mismatch")
    creators = z.get("creators") or []
    if not creators or creators[0].get("name") != "Agapov, Alexander":
        die("unexpected Zenodo creator identity")
    print("CITATION_ZENODO_METADATA_SYNC = PASS")


def main() -> int:
    check_required_files()
    check_schema_headers()
    check_hardening_contracts()
    check_state_machine()
    check_release_gate()
    check_metadata_sync()
    print("DRAFT_REPOSITORY_CONFORMANCE = PASS")
    print("AIFC_V1_FROZEN = FALSE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
