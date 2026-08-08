#!/usr/bin/env python3
"""SAL v1.12 lineage vertex reference closure.

Build a recognized repository-object index by enumerating an exact predecessor
Git tree, derive the inherited v1.11h seed from its already-bound receipt, and
recursively resolve classified internal object references to a machine-verified
least fixed point. This module makes no semantic-authority decision and no
claim that the seed or reference semantics exhaust global lineage relevance.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import subprocess
from typing import Any, Mapping, Sequence

from canonical import domain_hash, loads_strict

PROFILE_DOMAIN = "AIFC:REPOSITORY-OBJECT-INDEX-PROFILE:v1"
INDEX_DOMAIN = "AIFC:REPOSITORY-OBJECT-INDEX:v1"
VERTEX_UNIVERSE_DOMAIN = "AIFC:LINEAGE-VERTEX-UNIVERSE:v1"
DISCOVERY_MANIFEST_DOMAIN = "AIFC:VERTEX-DISCOVERY-MANIFEST:v1"
CLOSURE_RECEIPT_DOMAIN = "AIFC:LINEAGE-VERTEX-UNIVERSE-CLOSURE-RECEIPT:v1"

REQUIRED_INTERNAL = "REQUIRED_INTERNAL_OBJECT_REFERENCE"
OPTIONAL_INTERNAL = "OPTIONAL_INTERNAL_OBJECT_REFERENCE"
EXTERNAL_REFERENCE = "EXTERNAL_REFERENCE"
NON_OBJECT_OCCURRENCE = "NON_OBJECT_IDENTITY_OCCURRENCE"

class LineageVertexReferenceClosureV1Error(ValueError):
    pass

@dataclass(frozen=True)
class RepositoryObjectIndex:
    source_commit: str
    source_tree: str
    vertices_by_path: Mapping[str, Mapping[str, Any]]
    objects_by_path: Mapping[str, Mapping[str, Any]]
    identity_index: Mapping[tuple[str, str], tuple[str, ...]]
    index_hash: str

@dataclass(frozen=True)
class VertexClosureResult:
    final_vertex_paths: tuple[str, ...]
    final_vertices: tuple[Mapping[str, Any], ...]
    discovery_manifest: tuple[Mapping[str, Any], ...]
    worklist_transcript: tuple[Mapping[str, Any], ...]
    final_vertex_universe_hash: str
    discovery_manifest_hash: str
    ambiguous_required_references: int
    unresolved_required_references: int
    productive_expansions: int
    question_id: str

def profile_content_hash(profile: Mapping[str, Any]) -> str:
    material = dict(profile)
    material.pop("profile_content_hash", None)
    return domain_hash(PROFILE_DOMAIN, material)

def closure_content_hash(receipt: Mapping[str, Any]) -> str:
    material = dict(receipt)
    material.pop("closure_content_hash", None)
    return domain_hash(CLOSURE_RECEIPT_DOMAIN, material)

def _git(*args: str) -> bytes:
    try:
        return subprocess.check_output(["git", *args], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        raise LineageVertexReferenceClosureV1Error(
            "EXACT_TREE_GIT_COMMAND_FAILED:" + " ".join(args)
        ) from exc

def _exact_tree_sha(source_commit: str) -> str:
    return _git("rev-parse", f"{source_commit}^{{tree}}").decode("ascii").strip()

def _enumerate_exact_tree(source_commit: str, prefix: str) -> tuple[tuple[str, str], ...]:
    raw = _git("ls-tree", "-r", "-z", source_commit, "--", prefix)
    entries: list[tuple[str, str]] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            header, path_raw = record.split(b"\t", 1)
            _mode, kind, blob_sha = header.decode("ascii").split()
            path = path_raw.decode("utf-8", errors="strict")
        except Exception as exc:
            raise LineageVertexReferenceClosureV1Error(
                "EXACT_TREE_ENUMERATION_RECORD_INVALID"
            ) from exc
        if kind == "blob":
            entries.append((path, blob_sha))
    return tuple(sorted(entries))

def verify_profile(profile: Mapping[str, Any]) -> None:
    if profile.get("schema") != "AIFC/repository-object-index-profile/v1":
        raise LineageVertexReferenceClosureV1Error(
            "REPOSITORY_OBJECT_INDEX_PROFILE_SCHEMA_REBINDING"
        )
    if profile.get("profile_content_hash") != profile_content_hash(profile):
        raise LineageVertexReferenceClosureV1Error(
            "REPOSITORY_OBJECT_INDEX_PROFILE_REBINDING"
        )
    if profile.get("index_scope_prefix") != "conformance":
        raise LineageVertexReferenceClosureV1Error(
            "REPOSITORY_OBJECT_INDEX_SCOPE_REBINDING"
        )
    if profile.get("file_suffix") != ".json" or profile.get("strict_json") is not True:
        raise LineageVertexReferenceClosureV1Error(
            "REPOSITORY_OBJECT_INDEX_PARSER_REBINDING"
        )
    if profile.get("profile_authority_status") != "SUCCESSOR_CANDIDATE_NOT_AUTHORITY_ADMISSIBLE":
        raise LineageVertexReferenceClosureV1Error(
            "REPOSITORY_OBJECT_INDEX_PROFILE_AUTHORITY_SELF_ASSERTION"
        )
    if profile.get("global_adequacy") != "NOT_ESTABLISHED":
        raise LineageVertexReferenceClosureV1Error(
            "OBJECT_INDEX_PROFILE_GLOBAL_ADEQUACY_FALSE_PROMOTION"
        )

    records = profile.get("recognized_schemas")
    if not isinstance(records, list) or not records:
        raise LineageVertexReferenceClosureV1Error(
            "REPOSITORY_OBJECT_RECOGNITION_PROFILE_EMPTY"
        )
    schema_ids = [x.get("schema_id") for x in records if isinstance(x, Mapping)]
    if len(schema_ids) != len(records) or len(set(schema_ids)) != len(schema_ids):
        raise LineageVertexReferenceClosureV1Error(
            "REPOSITORY_OBJECT_RECOGNITION_PROFILE_DUPLICATE_SCHEMA"
        )

    rules = profile.get("reference_rules")
    if not isinstance(rules, list) or not rules:
        raise LineageVertexReferenceClosureV1Error(
            "LINEAGE_REFERENCE_CLASSIFICATION_PROFILE_EMPTY"
        )
    seen: set[tuple[str, str]] = set()
    allowed = {REQUIRED_INTERNAL, OPTIONAL_INTERNAL, EXTERNAL_REFERENCE, NON_OBJECT_OCCURRENCE}
    for rule in rules:
        if not isinstance(rule, Mapping):
            raise LineageVertexReferenceClosureV1Error(
                "LINEAGE_REFERENCE_CLASSIFICATION_RULE_INVALID"
            )
        field = rule.get("field_name")
        sources = rule.get("source_schema_ids")
        classification = rule.get("classification")
        if not isinstance(field, str) or not field or not isinstance(sources, list) or not sources:
            raise LineageVertexReferenceClosureV1Error(
                "LINEAGE_REFERENCE_CLASSIFICATION_RULE_INVALID"
            )
        if classification not in allowed:
            raise LineageVertexReferenceClosureV1Error(
                "LINEAGE_REFERENCE_CLASSIFICATION_RULE_INVALID"
            )
        if classification in {REQUIRED_INTERNAL, OPTIONAL_INTERNAL} and not isinstance(
            rule.get("target_identity_channel"), str
        ):
            raise LineageVertexReferenceClosureV1Error(
                "LINEAGE_REFERENCE_CLASSIFICATION_TARGET_CHANNEL_MISSING"
            )
        for source_schema in sources:
            key = (str(source_schema), field)
            if key in seen:
                raise LineageVertexReferenceClosureV1Error(
                    "LINEAGE_REFERENCE_CLASSIFICATION_RULE_OVERLAP"
                )
            seen.add(key)

def _schema_profile(profile: Mapping[str, Any]) -> Mapping[str, Mapping[str, Any]]:
    return {str(x["schema_id"]): x for x in profile["recognized_schemas"]}

def build_repository_object_index(
    source_commit: str,
    expected_tree_sha: str,
    profile: Mapping[str, Any],
) -> RepositoryObjectIndex:
    verify_profile(profile)
    actual_tree = _exact_tree_sha(source_commit)
    if actual_tree != expected_tree_sha:
        raise LineageVertexReferenceClosureV1Error("EXACT_TREE_BINDING_REBINDING")

    entries = _enumerate_exact_tree(source_commit, str(profile["index_scope_prefix"]))
    schema_profile = _schema_profile(profile)
    vertices: dict[str, Mapping[str, Any]] = {}
    objects: dict[str, Mapping[str, Any]] = {}
    identity: dict[tuple[str, str], set[str]] = {}

    for path, blob_sha in entries:
        if not path.endswith(str(profile["file_suffix"])):
            continue
        raw = _git("cat-file", "blob", blob_sha)
        try:
            parsed = loads_strict(raw.decode("utf-8", errors="strict"))
        except Exception:
            continue
        if not isinstance(parsed, Mapping):
            continue
        schema_id = parsed.get("schema")
        descriptor = schema_profile.get(str(schema_id))
        if descriptor is None:
            continue

        id_field = descriptor.get("object_id_field")
        primary_id = None
        if id_field is not None:
            primary_id = parsed.get(str(id_field))
            if not isinstance(primary_id, str) or not primary_id:
                raise LineageVertexReferenceClosureV1Error(
                    "REPOSITORY_OBJECT_INDEX_OBJECT_ID_REBINDING:" + path
                )

        hash_field = descriptor.get("content_hash_field")
        whole_hash = None
        if hash_field is not None:
            whole_hash = parsed.get(str(hash_field))
            domain = descriptor.get("content_hash_domain")
            if not isinstance(whole_hash, str) or len(whole_hash) != 64 or not isinstance(domain, str):
                raise LineageVertexReferenceClosureV1Error(
                    "REPOSITORY_OBJECT_INDEX_CONTENT_IDENTITY_REBINDING:" + path
                )
            material = dict(parsed)
            material.pop(str(hash_field), None)
            if domain_hash(domain, material) != whole_hash:
                raise LineageVertexReferenceClosureV1Error(
                    "REPOSITORY_OBJECT_INDEX_CONTENT_IDENTITY_REBINDING:" + path
                )

        vertex = {
            "repository_path": path,
            "schema_id": str(schema_id),
            "primary_object_id": primary_id,
            "git_blob_sha1": blob_sha,
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "whole_object_content_hash": whole_hash,
        }
        vertices[path] = vertex
        objects[path] = dict(parsed)

        def add(channel: str, value: Any) -> None:
            if isinstance(value, str) and value:
                identity.setdefault((channel, value), set()).add(path)

        add("REPOSITORY_PATH", path)
        channel = descriptor.get("object_id_channel")
        if isinstance(channel, str) and primary_id is not None:
            add(channel, primary_id)

    canonical_vertices = tuple(
        vertices[path] for path in sorted(vertices)
    )
    index_hash = domain_hash(INDEX_DOMAIN, list(canonical_vertices))
    frozen_identity = {
        key: tuple(sorted(paths))
        for key, paths in identity.items()
    }
    return RepositoryObjectIndex(
        source_commit=source_commit,
        source_tree=actual_tree,
        vertices_by_path=vertices,
        objects_by_path=objects,
        identity_index=frozen_identity,
        index_hash=index_hash,
    )

def derive_seed_from_inherited_binding(
    source_binding: Mapping[str, Any],
    index: RepositoryObjectIndex,
) -> tuple[str, ...]:
    declared = source_binding.get("vertices")
    if not isinstance(declared, list) or not declared:
        raise LineageVertexReferenceClosureV1Error(
            "LINEAGE_INHERITED_SEED_BINDING_INVALID"
        )
    seed: list[str] = []
    for inherited in declared:
        if not isinstance(inherited, Mapping):
            raise LineageVertexReferenceClosureV1Error(
                "LINEAGE_INHERITED_SEED_BINDING_INVALID"
            )
        path = inherited.get("source_path")
        if not isinstance(path, str) or path not in index.vertices_by_path:
            raise LineageVertexReferenceClosureV1Error(
                "LINEAGE_REQUIRED_VERTEX_UNIVERSE_OMISSION:" + str(path)
            )
        target = index.vertices_by_path[path]
        if (
            inherited.get("schema_id") != target["schema_id"]
            or inherited.get("object_id") != target["primary_object_id"]
            or inherited.get("git_blob_sha1") != target["git_blob_sha1"]
            or inherited.get("raw_sha256") != target["raw_sha256"]
            or inherited.get("whole_object_content_hash")
            != target["whole_object_content_hash"]
        ):
            raise LineageVertexReferenceClosureV1Error(
                "LINEAGE_VERTEX_CONTENT_IDENTITY_REBINDING:" + path
            )
        seed.append(path)
    if len(seed) != len(set(seed)):
        raise LineageVertexReferenceClosureV1Error(
            "LINEAGE_INHERITED_SEED_DUPLICATE_VERTEX"
        )
    return tuple(seed)

def _pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")

def _reference_rule_map(
    profile: Mapping[str, Any],
) -> Mapping[tuple[str, str], Mapping[str, Any]]:
    out: dict[tuple[str, str], Mapping[str, Any]] = {}
    for rule in profile["reference_rules"]:
        for source_schema in rule["source_schema_ids"]:
            out[(str(source_schema), str(rule["field_name"]))] = rule
    return out

def reference_candidates(
    obj: Mapping[str, Any],
    profile: Mapping[str, Any],
) -> tuple[Mapping[str, Any], ...]:
    source_schema = str(obj.get("schema"))
    rule_map = _reference_rule_map(profile)
    out: list[Mapping[str, Any]] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                key_s = str(key)
                child_path = path + "/" + _pointer_escape(key_s)
                rule = rule_map.get((source_schema, key_s))
                if rule is not None:
                    companion_field = rule.get("companion_hash_field")
                    companion = value.get(str(companion_field)) if companion_field else None
                    if isinstance(item, str):
                        out.append({
                            "source_json_pointer": child_path,
                            "field_name": key_s,
                            "classification": rule["classification"],
                            "matched_identity": item,
                            "target_identity_channel": rule.get("target_identity_channel"),
                            "companion_hash_value": companion,
                        })
                    elif isinstance(item, list):
                        for index, child in enumerate(item):
                            if isinstance(child, str):
                                out.append({
                                    "source_json_pointer": child_path + "/" + str(index),
                                    "field_name": key_s,
                                    "classification": rule["classification"],
                                    "matched_identity": child,
                                    "target_identity_channel": rule.get("target_identity_channel"),
                                    "companion_hash_value": companion,
                                })
                walk(item, child_path)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, path + "/" + str(index))

    walk(obj, "")
    return tuple(out)

def _resolve_required(
    candidate: Mapping[str, Any],
    index: RepositoryObjectIndex,
) -> str:
    channel = candidate.get("target_identity_channel")
    value = candidate.get("matched_identity")
    paths = index.identity_index.get((str(channel), str(value)), ())
    unique = tuple(sorted(set(paths)))
    if len(unique) == 0:
        raise LineageVertexReferenceClosureV1Error(
            "BLOCKED_UNRESOLVED_LINEAGE_VERTEX_REFERENCE:"
            + str(channel)
            + ":"
            + str(value)
        )
    if len(unique) > 1:
        raise LineageVertexReferenceClosureV1Error(
            "BLOCKED_AMBIGUOUS_LINEAGE_VERTEX_REFERENCE:"
            + str(channel)
            + ":"
            + str(value)
        )
    target_path = unique[0]
    companion = candidate.get("companion_hash_value")
    if companion is not None:
        target_hash = index.vertices_by_path[target_path]["whole_object_content_hash"]
        if companion != target_hash:
            raise LineageVertexReferenceClosureV1Error(
                "LINEAGE_VERTEX_REFERENCE_TARGET_REBINDING:" + target_path
            )
    return target_path

def assert_monotone(previous: Sequence[str], current: Sequence[str]) -> None:
    if not set(previous).issubset(set(current)):
        raise LineageVertexReferenceClosureV1Error(
            "LINEAGE_VERTEX_CLOSURE_NONMONOTONE_REMOVAL"
        )

def _canonical_discovery_occurrence(
    source_path: str,
    candidate: Mapping[str, Any],
    target_path: str,
    index: RepositoryObjectIndex,
) -> Mapping[str, Any]:
    source_obj = index.objects_by_path[source_path]
    target = index.vertices_by_path[target_path]
    return {
        "source_vertex_path": source_path,
        "source_schema_id": source_obj["schema"],
        "source_json_pointer": candidate["source_json_pointer"],
        "field_name": candidate["field_name"],
        "classification": candidate["classification"],
        "matched_identity": candidate["matched_identity"],
        "target_identity_channel": candidate["target_identity_channel"],
        "resolved_target_path": target_path,
        "resolved_target_schema_id": target["schema_id"],
        "resolved_target_primary_object_id": target["primary_object_id"],
        "resolved_target_git_blob_sha1": target["git_blob_sha1"],
        "resolved_target_raw_sha256": target["raw_sha256"],
        "resolved_target_whole_object_content_hash": target[
            "whole_object_content_hash"
        ],
        "companion_hash_value": candidate.get("companion_hash_value"),
    }

def _full_fixed_point_replay(
    final_paths: Sequence[str],
    index: RepositoryObjectIndex,
    profile: Mapping[str, Any],
) -> tuple[Mapping[str, Any], ...]:
    final_set = set(final_paths)
    manifest: list[Mapping[str, Any]] = []
    for source_path in sorted(final_set):
        obj = index.objects_by_path[source_path]
        for candidate in reference_candidates(obj, profile):
            classification = candidate["classification"]
            if classification == REQUIRED_INTERNAL:
                target_path = _resolve_required(candidate, index)
                if target_path not in final_set:
                    raise LineageVertexReferenceClosureV1Error(
                        "LINEAGE_VERTEX_FIXED_POINT_FALSE_TERMINATION:"
                        + source_path
                        + "->"
                        + target_path
                    )
                manifest.append(
                    _canonical_discovery_occurrence(
                        source_path, candidate, target_path, index
                    )
                )
            elif classification == OPTIONAL_INTERNAL:
                paths = index.identity_index.get(
                    (
                        str(candidate.get("target_identity_channel")),
                        str(candidate.get("matched_identity")),
                    ),
                    (),
                )
                if len(set(paths)) == 1:
                    target_path = tuple(set(paths))[0]
                    if target_path not in final_set:
                        raise LineageVertexReferenceClosureV1Error(
                            "LINEAGE_VERTEX_FIXED_POINT_FALSE_TERMINATION:"
                            + source_path
                            + "->"
                            + target_path
                        )
                    manifest.append(
                        _canonical_discovery_occurrence(
                            source_path, candidate, target_path, index
                        )
                    )
            elif classification in {EXTERNAL_REFERENCE, NON_OBJECT_OCCURRENCE}:
                continue
    return tuple(
        sorted(
            manifest,
            key=lambda item: (
                str(item["source_vertex_path"]),
                str(item["source_json_pointer"]),
                str(item["target_identity_channel"]),
                str(item["matched_identity"]),
                str(item["resolved_target_path"]),
            ),
        )
    )

def _question_id_from_seed(
    seed_paths: Sequence[str], index: RepositoryObjectIndex
) -> str:
    values = []
    for path in seed_paths:
        obj = index.objects_by_path[path]
        if obj.get("schema") == "AIFC/entailment-question/v1":
            values.append(obj.get("question_id"))
    if len(values) != 1 or not isinstance(values[0], str):
        raise LineageVertexReferenceClosureV1Error(
            "LINEAGE_VERTEX_QUESTION_SEED_INVALID"
        )
    return values[0]

def verify_question_context(
    final_paths: Sequence[str],
    index: RepositoryObjectIndex,
    question_id: str,
) -> None:
    for path in final_paths:
        obj = index.objects_by_path[path]
        if "entailment_question_id" in obj and obj.get("entailment_question_id") != question_id:
            raise LineageVertexReferenceClosureV1Error(
                "LINEAGE_VERTEX_QUESTION_CONTEXT_REBINDING:" + path
            )

def compute_reference_closure(
    seed_paths: Sequence[str],
    index: RepositoryObjectIndex,
    profile: Mapping[str, Any],
    *,
    strategy: str,
) -> VertexClosureResult:
    verify_profile(profile)
    if strategy not in {"BFS", "DFS"}:
        raise LineageVertexReferenceClosureV1Error(
            "LINEAGE_VERTEX_DISCOVERY_STRATEGY_INVALID"
        )
    if not set(seed_paths).issubset(set(index.vertices_by_path)):
        raise LineageVertexReferenceClosureV1Error(
            "LINEAGE_REQUIRED_VERTEX_UNIVERSE_OMISSION:SEED"
        )

    discovered: set[str] = set(seed_paths)
    worklist: list[str] = list(seed_paths)
    processed: set[str] = set()
    transcript: list[Mapping[str, Any]] = []
    productive_expansions = 0

    while worklist:
        source_path = worklist.pop(0 if strategy == "BFS" else -1)
        if source_path in processed:
            continue
        processed.add(source_path)
        before = tuple(sorted(discovered))
        added: list[str] = []

        obj = index.objects_by_path[source_path]
        for candidate in reference_candidates(obj, profile):
            classification = candidate["classification"]
            if classification == REQUIRED_INTERNAL:
                target_path = _resolve_required(candidate, index)
            elif classification == OPTIONAL_INTERNAL:
                paths = index.identity_index.get(
                    (
                        str(candidate.get("target_identity_channel")),
                        str(candidate.get("matched_identity")),
                    ),
                    (),
                )
                unique = tuple(sorted(set(paths)))
                if len(unique) == 0:
                    continue
                if len(unique) > 1:
                    raise LineageVertexReferenceClosureV1Error(
                        "BLOCKED_AMBIGUOUS_LINEAGE_VERTEX_REFERENCE:"
                        + str(candidate.get("matched_identity"))
                    )
                target_path = unique[0]
            elif classification in {EXTERNAL_REFERENCE, NON_OBJECT_OCCURRENCE}:
                continue
            else:
                raise LineageVertexReferenceClosureV1Error(
                    "UNRESOLVED_INTERNAL_REFERENCE_TO_EXTERNAL_RECLASSIFICATION"
                )

            if target_path not in discovered:
                discovered.add(target_path)
                worklist.append(target_path)
                added.append(target_path)
                productive_expansions += 1

        after = tuple(sorted(discovered))
        assert_monotone(before, after)
        transcript.append({
            "processed_source_path": source_path,
            "added_vertex_paths": sorted(added),
            "vertex_count_after": len(after),
        })

    final_paths = tuple(sorted(discovered))
    manifest = _full_fixed_point_replay(final_paths, index, profile)
    question_id = _question_id_from_seed(seed_paths, index)
    verify_question_context(final_paths, index, question_id)

    final_vertices = tuple(index.vertices_by_path[path] for path in final_paths)
    vertex_hash = domain_hash(VERTEX_UNIVERSE_DOMAIN, list(final_vertices))
    manifest_hash = domain_hash(DISCOVERY_MANIFEST_DOMAIN, list(manifest))
    return VertexClosureResult(
        final_vertex_paths=final_paths,
        final_vertices=final_vertices,
        discovery_manifest=manifest,
        worklist_transcript=tuple(transcript),
        final_vertex_universe_hash=vertex_hash,
        discovery_manifest_hash=manifest_hash,
        ambiguous_required_references=0,
        unresolved_required_references=0,
        productive_expansions=productive_expansions,
        question_id=question_id,
    )

def compute_order_independent_reference_closure(
    seed_paths: Sequence[str],
    index: RepositoryObjectIndex,
    profile: Mapping[str, Any],
) -> VertexClosureResult:
    bfs = compute_reference_closure(seed_paths, index, profile, strategy="BFS")
    dfs = compute_reference_closure(seed_paths, index, profile, strategy="DFS")
    if (
        bfs.final_vertex_paths != dfs.final_vertex_paths
        or bfs.final_vertex_universe_hash != dfs.final_vertex_universe_hash
        or bfs.discovery_manifest_hash != dfs.discovery_manifest_hash
        or bfs.discovery_manifest != dfs.discovery_manifest
    ):
        raise LineageVertexReferenceClosureV1Error(
            "LINEAGE_VERTEX_DISCOVERY_ORDER_DEPENDENCE"
        )
    return bfs

def verify_closure_receipt(
    receipt: Mapping[str, Any],
    profile: Mapping[str, Any],
    source_binding: Mapping[str, Any],
    *,
    source_commit: str,
    expected_tree_sha: str,
) -> tuple[RepositoryObjectIndex, VertexClosureResult]:
    if receipt.get("schema") != "AIFC/lineage-vertex-universe-closure/v1":
        raise LineageVertexReferenceClosureV1Error(
            "LINEAGE_VERTEX_UNIVERSE_CLOSURE_SCHEMA_REBINDING"
        )
    index = build_repository_object_index(source_commit, expected_tree_sha, profile)
    seed = derive_seed_from_inherited_binding(source_binding, index)
    result = compute_order_independent_reference_closure(seed, index, profile)

    if receipt.get("source_main_commit") != source_commit:
        raise LineageVertexReferenceClosureV1Error(
            "LINEAGE_VERTEX_UNIVERSE_SOURCE_COMMIT_REBINDING"
        )
    if receipt.get("source_tree_sha") != expected_tree_sha:
        raise LineageVertexReferenceClosureV1Error(
            "EXACT_TREE_BINDING_REBINDING"
        )
    if receipt.get("seed_derivation") != "FROM_INHERITED_V1_11H_BINDING_VERTICES":
        raise LineageVertexReferenceClosureV1Error(
            "SUCCESSOR_DEFINED_REQUIRED_VERTEX_LIST"
        )
    if receipt.get("seed_vertex_count") != len(seed):
        raise LineageVertexReferenceClosureV1Error(
            "LINEAGE_VERTEX_SEED_COUNT_REBINDING"
        )
    if receipt.get("final_vertex_count") != len(result.final_vertex_paths):
        raise LineageVertexReferenceClosureV1Error(
            "LINEAGE_VERTEX_FINAL_COUNT_REBINDING"
        )
    if receipt.get("final_vertex_paths") != list(result.final_vertex_paths):
        raise LineageVertexReferenceClosureV1Error(
            "LINEAGE_REQUIRED_VERTEX_UNIVERSE_OMISSION"
        )
    if receipt.get("final_vertex_universe_hash") != result.final_vertex_universe_hash:
        raise LineageVertexReferenceClosureV1Error(
            "LINEAGE_VERTEX_UNIVERSE_HASH_REBINDING"
        )
    if receipt.get("vertex_discovery_manifest_hash") != result.discovery_manifest_hash:
        raise LineageVertexReferenceClosureV1Error(
            "LINEAGE_VERTEX_DISCOVERY_OCCURRENCE_REBINDING"
        )
    if receipt.get("vertex_discovery_occurrence_count") != len(result.discovery_manifest):
        raise LineageVertexReferenceClosureV1Error(
            "LINEAGE_VERTEX_DISCOVERY_OCCURRENCE_OMISSION"
        )
    required_literals = {
        "closure_monotonicity": "CONFIRMED",
        "fixed_point_status": "MACHINE_VERIFIED_BY_FINAL_REPLAY",
        "order_independence": "CONFIRMED_IN_TESTED_SCOPE",
        "reference_closure_status": "ESTABLISHED_IN_TESTED_SCOPE_FROM_INHERITED_SEED",
        "global_lineage_seed_completeness": "NOT_ESTABLISHED",
        "object_index_profile_global_adequacy": "NOT_ESTABLISHED",
        "global_repository_object_universe_completeness": "NOT_ESTABLISHED",
        "semantic_relation_universe_completeness": "NOT_ESTABLISHED",
        "derived_semantic_authority": "BLOCKED",
    }
    for field, expected in required_literals.items():
        if receipt.get(field) != expected:
            raise LineageVertexReferenceClosureV1Error(
                "LINEAGE_VERTEX_CLOSURE_FALSE_PROMOTION:" + field
            )
    if receipt.get("ambiguous_required_references") != 0:
        raise LineageVertexReferenceClosureV1Error(
            "BLOCKED_AMBIGUOUS_LINEAGE_VERTEX_REFERENCE"
        )
    if receipt.get("unresolved_required_references") != 0:
        raise LineageVertexReferenceClosureV1Error(
            "BLOCKED_UNRESOLVED_LINEAGE_VERTEX_REFERENCE"
        )
    if receipt.get("solver_invocation_count") != 0:
        raise LineageVertexReferenceClosureV1Error(
            "LINEAGE_VERTEX_CLOSURE_SOLVER_FALSE_PROMOTION"
        )
    if receipt.get("closure_content_hash") != closure_content_hash(receipt):
        raise LineageVertexReferenceClosureV1Error(
            "LINEAGE_VERTEX_CLOSURE_CONTENT_REBINDING"
        )
    return index, result
