# AEGIS-7 Signing Specification

## Canonical JSON Format

Each entry's hash is computed over a canonical JSON serialization:

```python
import json

M = {
    "seq": entry["sequence"],
    "ts": entry["timestamp"],
    "type": entry["type"],
    "prev": entry["prev_hash"],
    "data": entry["data"]
}

canonical_json = json.dumps(M, sort_keys=True)
# Default separators: (', ', ': ')
# UTF-8 encoding

entry_hash = hashlib.sha256(canonical_json.encode()).hexdigest()
```

## TPM Signing

The 64-character hex hash is ASCII-encoded (64 bytes) and signed with TPM 2.0:

```bash
tpm2_sign -c 0x81000001 -g sha256 -s rsassa -f plain -o signature.bin hash_as_hex_string.txt
```

Due to `tpm2_sign -g sha256` with file input, the actually-signed digest is:
## Verification

Recover the signed digest using:
```bash
openssl rsautl -verify -pubin -inkey aegis7_pubkey.pem -in signature.bin
```

The last 32 bytes of the output are the recovered SHA-256 digest. Compare:
```python
recovered[-32:] == hashlib.sha256(entry["hash"].encode()).digest()
```

## Chain Integrity

For all i > 0:
Genesis block: `entry[0]["prev_hash"] = "0" * 64`

## Data Binding

The critical property: sensor payload is included in the canonical JSON. To verify data was not tampered:

```python
recompute = hashlib.sha256(json.dumps(M, sort_keys=True).encode()).hexdigest()
assert recompute == entry["hash"]  # If this fails, data was modified
```

---

**Implementation note**: All three nodes (n1, n2, n3) sensor data is included in the `data.nodes` field and is cryptographically bound to the signature. Changing any sensor reading invalidates the hash; fixing the hash without re-signing via the TPM invalidates the signature.

