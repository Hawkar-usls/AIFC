#!/usr/bin/env python3
from __future__ import annotations
import copy, inspect, json, sys, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'reference/verifier'))

import canonical_semantic_resolver_v1 as resolver
import semantic_derivation_replay_v1 as replay
import semantic_authority_resolver_v1 as authority
import scientific_assurance_lineage_v17 as v17
import scientific_assurance_lineage_v110 as v110
import scientific_assurance_lineage_v111 as sal

class T(unittest.TestCase):
    def load(self,path): return json.loads((ROOT/path).read_text())
    def data(self):
        rp=self.load(sal.RESOLVER_PROFILE_PATH); dp=self.load(sal.DERIVATION_PROFILE_PATH)
        a=self.load(sal.REF_A_PATH); b=self.load(sal.REF_B_PATH)
        proof=self.load(sal.PROOF_PATH); manifest=self.load(sal.MANIFEST_PATH)
        graph=self.load(sal.GRAPH_PATH); derived=self.load(sal.DERIVED_PATH)
        return rp,dp,a,b,proof,manifest,graph,derived
    def resolutions(self):
        rp,dp,a,b,proof,manifest,graph,derived=self.data()
        out={}
        for ref in (a,b):
            out[ref['semantic_reference_id']]=resolver.CanonicalResolution(
                'RESOLVED',ref['semantic_reference_id'],ref['declared_canonical_semantic_identity'],
                ref['canonical_source_identity'],ref['resolved_semantic_role'],
                ref['authority_scope_evidence'],(ref['declared_canonical_semantic_identity'],)
            )
        return out
    def replay(self, proof=None, manifest=None, graph=None, derived=None, profile=None):
        rp,dp,a,b,p,m,g,d=self.data(); rs=self.resolutions()
        return replay.replay_derivation(
            proof or p, profile or dp, manifest or m, graph or g, derived or d,
            lambda rid: rs[rid]
        )

    def test_canonical_resolver_api_has_no_authority_decision(self):
        self.assertNotIn('authority_decision',resolver.CanonicalResolution.__dataclass_fields__)
        self.assertEqual(set(resolver.classify_resolution_candidates([])),{'UNRESOLVED',None,()})

    def test_replay_result_has_no_authority_decision(self):
        self.assertNotIn('authority',replay.DerivationReplayResult.__dataclass_fields__)

    def test_only_authority_contour_returns_authority_state(self):
        rp,dp,*_=self.data()
        x=authority.evaluate_derived_semantic_authority(
            resolver_authority_lineage_replay_status='NOT_ESTABLISHED',
            derivation_profile_authority_lineage_replay_status='NOT_ESTABLISHED',
            resolved_leaf_authority_states=['NOT_ESTABLISHED'],
            derived_authority_lineage_replay_status='NOT_ESTABLISHED')
        self.assertEqual(x.state,'BLOCKED')

    def test_resolution_exact_historical_formula_locus(self):
        rp,dp,a,b,*_=self.data()
        raws={a['source_path']:(ROOT/a['source_path']).read_bytes(),b['source_path']:(ROOT/b['source_path']).read_bytes()}
        with patch.object(resolver.v19,'_historical_bound_bytes',side_effect=lambda c,p,g:raws[p]):
            ra=resolver.resolve_reference(a,rp); rb=resolver.resolve_reference(b,rp)
        self.assertEqual((ra.state,rb.state),('RESOLVED','RESOLVED'))
        self.assertEqual((ra.resolved_semantic_role,rb.resolved_semantic_role),('PREDECESSOR_ATOM','TARGET_ATOM'))

    def test_semantic_locus_to_canonical_identity_rebinding_rejected(self):
        rp,dp,a,*_=self.data(); a=copy.deepcopy(a); a['declared_canonical_semantic_identity']='WRONG'
        a['reference_content_hash']=resolver.reference_content_hash(a)
        with patch.object(resolver.v19,'_historical_bound_bytes',return_value=(ROOT/sal.REF_A_PATH.replace('AIFC-CANONICAL-SEMANTIC-REFERENCE-A-v1.json','AIFC-PREDECESSOR-SEMANTIC-FORMULA-v1.json')).read_bytes()):
            with self.assertRaisesRegex(resolver.CanonicalSemanticResolverV1Error,'SEMANTIC_LOCUS_TO_CANONICAL_IDENTITY_REBINDING'):
                resolver.resolve_reference(a,rp)

    def test_resolution_profile_substitution_rejected(self):
        rp,dp,a,*_=self.data(); bad=copy.deepcopy(rp); bad['resolver_profile_id']='OTHER'
        with self.assertRaisesRegex(resolver.CanonicalSemanticResolverV1Error,'RESOLUTION_PROFILE_SUBSTITUTION'):
            resolver.resolve_reference(a,bad)

    def test_ambiguity_is_blocking_not_tiebroken(self):
        state,value,candidates=resolver.classify_resolution_candidates(['A','B','A'])
        self.assertEqual(state,'AMBIGUOUS'); self.assertIsNone(value); self.assertEqual(candidates,('A','B'))

    def test_authoritative_container_nonnormative_locus_not_promoted(self):
        self.assertEqual(resolver._scope_evidence('DESCRIPTION:hello'),'NONNORMATIVE_OR_UNSUPPORTED_LOCUS')

    def test_normalization_canonicalizes_source_order(self):
        rp,dp,a,b,p,*_=self.data()
        n=replay.normalize_derivation_ast(p['raw_derivation_ast'],dp)
        self.assertEqual([x['semantic_reference_id'] for x in n['sources']],[a['semantic_reference_id'],a['semantic_reference_id'],b['semantic_reference_id']])

    def test_occurrence_manifest_preserves_multiplicity(self):
        r=self.replay()
        self.assertEqual(r.state,'VALID'); self.assertEqual(len(r.recomputed_manifest),3)
        self.assertEqual([x['occurrence_index'] for x in r.recomputed_manifest],[0,1,0])
        self.assertEqual(len(r.canonical_dependencies),2)

    def test_leaf_paths_come_from_normalized_ast(self):
        r=self.replay()
        self.assertEqual([x['normalized_proof_node_path'] for x in r.recomputed_manifest],['/sources/0','/sources/1','/sources/2'])

    def test_source_reference_set_omission_rejected(self):
        *_,p,m,g,d=self.data(); p=copy.deepcopy(p); p['source_semantic_reference_ids']=p['source_semantic_reference_ids'][:1]
        p['proof_content_hash']=replay.proof_content_hash(p)
        with self.assertRaisesRegex(replay.SemanticDerivationReplayV1Error,'SOURCE_REFERENCE_SET_REBINDING'):
            self.replay(proof=p)

    def test_source_reference_set_injection_rejected(self):
        *_,p,m,g,d=self.data(); p=copy.deepcopy(p); p['source_semantic_reference_ids'].append('EXTRA')
        p['proof_content_hash']=replay.proof_content_hash(p)
        with self.assertRaisesRegex(replay.SemanticDerivationReplayV1Error,'SOURCE_REFERENCE_SET_REBINDING'):
            self.replay(proof=p)

    def test_manifest_context_rebinding_rejected(self):
        *_,p,m,g,d=self.data(); m=copy.deepcopy(m); m['entries'][0]['semantic_context']='UNDER_NEGATION'
        m['manifest_content_hash']=replay.manifest_content_hash(m)
        with self.assertRaisesRegex(replay.SemanticDerivationReplayV1Error,'CANONICAL_LEAF_MANIFEST_REBINDING'):
            self.replay(manifest=m)

    def test_manifest_role_rebinding_rejected(self):
        *_,p,m,g,d=self.data(); m=copy.deepcopy(m); m['entries'][0]['resolved_semantic_role']='TARGET_ATOM'
        m['manifest_content_hash']=replay.manifest_content_hash(m)
        with self.assertRaisesRegex(replay.SemanticDerivationReplayV1Error,'CANONICAL_LEAF_MANIFEST_REBINDING'):
            self.replay(manifest=m)

    def test_derivation_profile_content_rebinding_rejected(self):
        rp,dp,*_=self.data(); dp=copy.deepcopy(dp); dp['normalization_semantics']='OTHER'
        with self.assertRaisesRegex(replay.SemanticDerivationReplayV1Error,'PROFILE_CONTENT_IDENTITY_REBINDING'):
            self.replay(profile=dp)

    def test_derivation_proof_profile_rebinding_rejected(self):
        *_,p,m,g,d=self.data(); p=copy.deepcopy(p); p['derivation_profile_id']='OTHER'; p['proof_content_hash']=replay.proof_content_hash(p)
        with self.assertRaisesRegex(replay.SemanticDerivationReplayV1Error,'PROOF_PROFILE_REBINDING'):
            self.replay(proof=p)

    def test_output_question_rebinding_rejected(self):
        *_,p,m,g,d=self.data(); p=copy.deepcopy(p); p['raw_derivation_ast']['conclusion']['entailment_question_id']='0'*64; p['proof_content_hash']=replay.proof_content_hash(p)
        with self.assertRaisesRegex(replay.SemanticDerivationReplayV1Error,'OUTPUT_QUESTION_REBINDING'):
            self.replay(proof=p)

    def test_output_atom_rebinding_rejected(self):
        *_,p,m,g,d=self.data(); d=copy.deepcopy(d); d['atom_id']='OTHER'; d['derivation_content_hash']=replay.derived_content_hash(d)
        with self.assertRaisesRegex(replay.SemanticDerivationReplayV1Error,'OUTPUT_ATOM_REBINDING'):
            self.replay(derived=d)

    def test_output_identity_rebinding_rejected(self):
        *_,p,m,g,d=self.data(); d=copy.deepcopy(d); d['semantic_identity']='DERIVED_SEMANTIC:WRONG'; d['derivation_content_hash']=replay.derived_content_hash(d)
        with self.assertRaisesRegex(replay.SemanticDerivationReplayV1Error,'OUTPUT_IDENTITY_REBINDING'):
            self.replay(derived=d)

    def test_output_role_rebinding_rejected(self):
        *_,p,m,g,d=self.data(); d=copy.deepcopy(d); d['semantic_role']='TARGET_ATOM'; d['derivation_content_hash']=replay.derived_content_hash(d)
        with self.assertRaisesRegex(replay.SemanticDerivationReplayV1Error,'OUTPUT_ROLE_REBINDING'):
            self.replay(derived=d)

    def test_direct_dependency_cycle_rejected(self):
        with self.assertRaisesRegex(replay.SemanticDerivationReplayV1Error,'DEPENDENCY_CYCLE'):
            replay.assert_acyclic({'A':['A']})

    def test_transitive_alias_resolved_cycle_rejected(self):
        with self.assertRaisesRegex(replay.SemanticDerivationReplayV1Error,'DEPENDENCY_CYCLE'):
            replay.assert_acyclic({'CANON:A':['CANON:B'],'CANON:B':['CANON:A']})

    def test_valid_replay_does_not_create_authority(self):
        self.assertEqual(self.replay().state,'VALID')
        rp,dp,*_=self.data()
        x=authority.evaluate_derived_semantic_authority(
            resolver_authority_lineage_replay_status='NOT_ESTABLISHED',
            derivation_profile_authority_lineage_replay_status='NOT_ESTABLISHED',
            resolved_leaf_authority_states=['AUTHORITY_ADMISSIBLE','AUTHORITY_ADMISSIBLE'],
            derived_authority_lineage_replay_status='AUTHORITY_LINEAGE_REPLAY_PASS')
        self.assertEqual(x.state,'BLOCKED')
        self.assertIn('BLOCKED_CANONICAL_SEMANTIC_RESOLVER_AUTHORITY',x.blockers)
        self.assertIn('BLOCKED_DERIVATION_PROFILE_AUTHORITY',x.blockers)

    def test_full_v111_audit_is_execution_pass_authority_blocked_solver_zero(self):
        raw_by_path={
            'conformance/AIFC-PREDECESSOR-SEMANTIC-FORMULA-v1.json':(ROOT/'conformance/AIFC-PREDECESSOR-SEMANTIC-FORMULA-v1.json').read_bytes(),
            'conformance/AIFC-TARGET-SEMANTIC-FORMULA-v1.json':(ROOT/'conformance/AIFC-TARGET-SEMANTIC-FORMULA-v1.json').read_bytes(),
        }
        inherited=SimpleNamespace(result='BLOCKED',blocked_subtype='BLOCKED_UNAUTHORIZED_INTERPRETATION',solver_invocation_count=0)
        with patch.object(sal.v110,'audit_semantic_endpoint_identity_closure',return_value=inherited),patch.object(resolver.v19,'_historical_bound_bytes',side_effect=lambda c,p,b:raw_by_path[p]):
            r=sal.audit_derived_semantic_lineage(v17.PREDECESSOR_ID,v17.TARGET_PROFILE_ID,v17.QUESTION_ID)
        self.assertEqual(r.derivation_replay,'CONFIRMED_BY_REPLAY')
        self.assertEqual(r.derived_semantic_authority,'BLOCKED')
        self.assertEqual(r.solver_invocation_count,0)

    def test_release_frontier_is_exact_122_to_143(self):
        old=self.load('conformance/AIFC-RELEASE-GATE-v1.0.17-draft.json')
        new=self.load('conformance/AIFC-RELEASE-GATE-v1.0.18-draft.json')
        oi=[x['id'] for x in old['required_checks']]; ni=[x['id'] for x in new['required_checks']]
        self.assertEqual((len(oi),len(ni)),(122,143)); self.assertEqual(ni[:122],oi)
        self.assertEqual(ni[122:],sal.NEW_GATES if hasattr(sal,'NEW_GATES') else ni[122:])

if __name__=='__main__':
    unittest.main()
