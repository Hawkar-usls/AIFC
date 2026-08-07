#!/usr/bin/env python3
"""AIFC Verifier A Ed25519 verification backend v0.6.

The protocol semantics and exact signature preimage are established elsewhere.
This module performs one narrow cryptographic operation using the system OpenSSL
Ed25519 implementation captured by the execution-environment evidence.

It does not evaluate historical compromise, freshness, causal validity, or any
scientific claim. Any backend failure is fail-closed.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile


class Ed25519CryptoError(ValueError):
    pass


# RFC 8410 SubjectPublicKeyInfo prefix for id-Ed25519 + BIT STRING length 32.
ED25519_SPKI_PREFIX = bytes.fromhex("302a300506032b6570032100")


@dataclass(frozen=True)
class Ed25519BackendIdentity:
    executable: str
    executable_sha256: str
    version_line: str


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Ed25519CryptoError(code)


def backend_identity() -> Ed25519BackendIdentity:
    executable = shutil.which("openssl")
    _require(executable is not None, "ED25519_BACKEND_OPENSSL_NOT_FOUND")
    path = Path(executable)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise Ed25519CryptoError(f"ED25519_BACKEND_BINARY_UNREADABLE:{exc}") from exc
    try:
        proc = subprocess.run(
            [str(path), "version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise Ed25519CryptoError(f"ED25519_BACKEND_VERSION_FAILED:{exc}") from exc
    _require(proc.returncode == 0, "ED25519_BACKEND_VERSION_NONZERO")
    try:
        version_line = proc.stdout.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError as exc:
        raise Ed25519CryptoError("ED25519_BACKEND_VERSION_NOT_UTF8") from exc
    _require(version_line.startswith("OpenSSL "), "ED25519_BACKEND_NOT_OPENSSL")
    return Ed25519BackendIdentity(
        executable=str(path),
        executable_sha256=hashlib.sha256(raw).hexdigest(),
        version_line=version_line,
    )


def verify_ed25519(public_key: bytes, message: bytes, signature: bytes) -> bool:
    """Verify one direct Ed25519 signature over exact message bytes.

    Returns True only for a cryptographically valid signature. A normal signature
    verification failure returns False. Backend/setup failures raise
    Ed25519CryptoError so callers can fail closed with a distinct evidence code.
    """
    _require(isinstance(public_key, bytes) and len(public_key) == 32, "ED25519_PUBLIC_KEY_LENGTH_INVALID")
    _require(isinstance(message, bytes), "ED25519_MESSAGE_NOT_BYTES")
    _require(isinstance(signature, bytes) and len(signature) == 64, "ED25519_SIGNATURE_LENGTH_INVALID")
    _require(len(message) > 0, "ED25519_EMPTY_MESSAGE_UNSUPPORTED_BY_CURRENT_OPENSSL_BACKEND")

    backend = backend_identity()
    spki = ED25519_SPKI_PREFIX + public_key

    try:
        with tempfile.TemporaryDirectory(prefix="aifc-ed25519-") as td:
            root = Path(td)
            pub_path = root / "public.der"
            msg_path = root / "message.bin"
            sig_path = root / "signature.bin"
            pub_path.write_bytes(spki)
            msg_path.write_bytes(message)
            sig_path.write_bytes(signature)
            proc = subprocess.run(
                [
                    backend.executable,
                    "pkeyutl",
                    "-verify",
                    "-pubin",
                    "-inkey",
                    str(pub_path),
                    "-keyform",
                    "DER",
                    "-rawin",
                    "-in",
                    str(msg_path),
                    "-sigfile",
                    str(sig_path),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=30,
            )
    except (OSError, subprocess.SubprocessError) as exc:
        raise Ed25519CryptoError(f"ED25519_BACKEND_EXECUTION_FAILED:{exc}") from exc

    if proc.returncode == 0:
        return True

    # OpenSSL returns nonzero for signature mismatch. We deliberately do not try to
    # turn backend-specific stderr text into protocol semantics. Any nonzero result
    # is cryptographic rejection; unexpected backend outages remain fail-closed.
    return False
