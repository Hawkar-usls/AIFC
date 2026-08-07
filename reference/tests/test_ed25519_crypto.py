import sys
import unittest
from pathlib import Path

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from ed25519_crypto import backend_identity, verify_ed25519  # noqa: E402


# RFC 8032, section 7.1, TEST 2.
RFC8032_PUBLIC_KEY = bytes.fromhex(
    "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c"
)
RFC8032_MESSAGE = bytes.fromhex("72")
RFC8032_SIGNATURE = bytes.fromhex(
    "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da"
    "085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"
)


class Ed25519CryptoTests(unittest.TestCase):
    def test_openssl_backend_identity_is_recordable(self):
        identity = backend_identity()
        self.assertTrue(identity.version_line.startswith("OpenSSL "))
        self.assertEqual(len(identity.executable_sha256), 64)

    def test_rfc8032_known_answer_signature_verifies(self):
        self.assertTrue(verify_ed25519(RFC8032_PUBLIC_KEY, RFC8032_MESSAGE, RFC8032_SIGNATURE))

    def test_rfc8032_message_bit_flip_is_rejected(self):
        self.assertFalse(verify_ed25519(RFC8032_PUBLIC_KEY, b"s", RFC8032_SIGNATURE))

    def test_rfc8032_signature_bit_flip_is_rejected(self):
        bad = bytearray(RFC8032_SIGNATURE)
        bad[0] ^= 1
        self.assertFalse(verify_ed25519(RFC8032_PUBLIC_KEY, RFC8032_MESSAGE, bytes(bad)))

    def test_wrong_public_key_is_rejected(self):
        bad_key = bytes([RFC8032_PUBLIC_KEY[0] ^ 1]) + RFC8032_PUBLIC_KEY[1:]
        self.assertFalse(verify_ed25519(bad_key, RFC8032_MESSAGE, RFC8032_SIGNATURE))


if __name__ == "__main__":
    unittest.main()
