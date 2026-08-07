#!/usr/bin/env python3
"""AIFC v0.5 pre-crypto full-admission composition."""
from __future__ import annotations

from typing import Any, Mapping

from full_admission_v02 import verify_full_admission_v02
from preregistration_v05 import verify_signature_preimage_preregistration
from resolver_v02 import EvidenceResolverV02


def verify_full_admission_v05(
    manifest: Mapping[str, Any], resolver: EvidenceResolverV02
) -> dict[str, Any]:
    signature_preimage_prereg = verify_signature_preimage_preregistration(manifest, resolver)
    if signature_preimage_prereg is not None:
        return signature_preimage_prereg
    return verify_full_admission_v02(manifest, resolver)
