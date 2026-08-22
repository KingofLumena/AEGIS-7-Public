#!/usr/bin/env python3
"""
AEGIS-7 - Dual-signature demonstration (RSA-2048 + ML-DSA-65)

Signs a checkpoint with two independent algorithms over the same payload:
  - RSA-2048 (PKCS#1 v1.5, SHA-256) - classical
  - ML-DSA-65 (NIST FIPS 204)       - post-quantum, via liboqs

Requires: pip install liboqs-python
"""
import json
import sys
from datetime import datetime, timezone

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

try:
    import oqs
except ImportError:
    sys.exit(
        "liboqs-python is not installed.\n\n"
        "This demo performs real ML-DSA-65 signing and will not run without it.\n"
        "Install with:  pip install liboqs-python\n\n"
        "It deliberately does not fall back to a hash-based placeholder - a hash\n"
        "is not a signature."
    )

PQ_ALGORITHM = "ML-DSA-65"


class DualSigner:
    def __init__(self):
        self.rsa_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.pq_signer = oqs.Signature(PQ_ALGORITHM)
        self.pq_public_key = self.pq_signer.generate_keypair()

    def _canonical(self, checkpoint):
        return json.dumps(checkpoint, sort_keys=True).encode()

    def dual_sign(self, checkpoint):
        data = self._canonical(checkpoint)
        return {
            "checkpoint": checkpoint,
            "rsa_signature": self.rsa_key.sign(
                data, padding.PKCS1v15(), hashes.SHA256()
            ).hex(),
            "pq_signature": self.pq_signer.sign(data).hex(),
            "pq_algorithm": PQ_ALGORITHM,
            "signed_at": datetime.now(timezone.utc).isoformat(),
        }

    def verify(self, entry):
        data = self._canonical(entry["checkpoint"])
        try:
            self.rsa_key.public_key().verify(
                bytes.fromhex(entry["rsa_signature"]),
                data,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            rsa_ok = True
        except Exception:
            rsa_ok = False

        with oqs.Signature(PQ_ALGORITHM) as verifier:
            pq_ok = verifier.verify(
                data, bytes.fromhex(entry["pq_signature"]), self.pq_public_key
            )
        return rsa_ok, pq_ok


def main():
    checkpoint = {
        "sequence": 3428863,
        "merkle_root": "edba49d1794e4a65243c06e8c573aef73a8875af7a4d266e7843ae1abd57a3b8",
        "leaf_count": 2925481,
        "quorum": "3/3",
    }

    signer = DualSigner()
    entry = signer.dual_sign(checkpoint)

    print("AEGIS-7 - dual-signed checkpoint")
    print("=" * 60)
    print("  algorithm      %s (NIST FIPS 204)" % PQ_ALGORITHM)
    print("  RSA signature  %d bytes" % (len(entry["rsa_signature"]) // 2))
    print("  PQ signature   %d bytes" % (len(entry["pq_signature"]) // 2))
    print()

    rsa_ok, pq_ok = signer.verify(entry)
    print("  RSA-2048 verification    : %s" % ("PASS" if rsa_ok else "FAIL"))
    print("  ML-DSA-65 verification   : %s" % ("PASS" if pq_ok else "FAIL"))
    print()

    tampered = dict(entry)
    sig = list(entry["pq_signature"])
    sig[0] = "0" if sig[0] != "0" else "1"
    tampered["pq_signature"] = "".join(sig)
    _, pq_tampered_ok = signer.verify(tampered)
    print("  Tampered PQ signature    : %s" % ("PASS" if pq_tampered_ok else "REJECTED"))
    print()

    if rsa_ok and pq_ok and not pq_tampered_ok:
        print("  Both signatures valid; tampering correctly rejected.")
        return 0
    print("  Unexpected result.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
