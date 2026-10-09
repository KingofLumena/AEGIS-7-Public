# Verifying an AEGIS-7 anchor

AEGIS-7 periodically computes a Merkle root over its audit chain, signs that
root twice (TPM RSA-2048 and ML-DSA-65), and publishes it in the
[AEGIS-7-Anchors](https://github.com/KingofLumena/AEGIS-7-Anchors) ledger
(`anchors.jsonl`, one anchor per line). This directory contains everything
needed to check those signatures yourself.

You do not need access to the device, and you do not need any AEGIS-7 code
beyond the single script in this directory.

## Keys

The TPM signing key changed on **2026-10-07**. Pick the key by the anchor's
`tpm_key_id` / `tpm_pubkey_sha256` fields, or by `last_seq` using the keyring.

| key_id | Public key | SHA-256 of the PEM file | Signs sequences | Status |
|---|---|---|---|---|
| `v1-slb9670` | `keys/tpm2_pubkey_v1_slb9670.pem` (= the old `aegis7_tpm_pub.pem`) | `384ea46bb9adbf58ec5d972b16583a3819e33f35bf6429771a12b00e0f9eefe4` | 0 – 6092120 | retired: TPM destroyed 2026-10-02, private key lost |
| `v2-slb9672` | `keys/tpm2_pubkey_v2_slb9672.pem` | `d8d6a184cfbf2952ccae688b61f7d70ad32001a9b83ec1ac843dc8f8ced2c454` | 6092121 – open | **active**, first signed entry 6237825 |

Both are RSA-2048, RSASSA-PKCS1-v1_5 / SHA-256, generated inside an Infineon TPM
(SLB9670, then SLB9672 FW 15.x) at persistent handle `0x81000001`; the private
keys cannot be exported. The machine-readable list is `keys/tpm_keyring.json`.

The post-quantum key did **not** change:

| Key | File | SHA-256 |
|---|---|---|
| ML-DSA-65 (FIPS 204) public key, 1952 bytes | `aegis7_mldsa65_pub.bin` | `93d1ca34e7d5040c277b7ef85cfa9a4c91d2038bef26388f38779676cdec3f5c` |

### Rotation of 2026-10-07

On 2026-10-02 the v1 TPM was destroyed during a hardware migration (a GPS HAT
was fitted reversed on the GPIO header that also carried the TPM). Its private
key is gone, so the rotation statement **cannot** be signed by the old key.
What exists instead:

1. `keys/ROTATION_20261007.json`, signed by v2 over its exact bytes:
   ```bash
   openssl dgst -sha256 -verify keys/tpm2_pubkey_v2_slb9672.pem \
       -signature keys/ROTATION_20261007.json.sig keys/ROTATION_20261007.json
   # Verified OK
   ```
   It names the last entry signed by v1 (seq 6092120) and the first entry
   signed by v2 (seq 6237825), with their entry hashes.
2. **Unsigned window**: sequences 6092121 – 6237824 (145,704 entries) were
   written while no TPM was present. They are hash-chained and HMAC'd but carry
   no TPM signature; their cryptographic attestation starts with the first
   anchor signed by v2, not at write time.
3. **Continuity through the unchanged ML-DSA-65 key**: anchors before and after
   the rotation verify against the same `aegis7_mldsa65_pub.bin`. The rotation
   was also published as a commit in AEGIS-7-Anchors on 2026-10-07.

## What you need

```
pip install cryptography          # required — checks the TPM RSA signature
pip install liboqs-python         # optional — checks the ML-DSA-65 signature
```

Without `liboqs-python` the script still runs; it reports the post-quantum
signature as present but unverified.

## Step by step

1. Get an anchor. Any line of `anchors.jsonl` in AEGIS-7-Anchors is one anchor;
   save it as a file:
   ```bash
   git clone https://github.com/KingofLumena/AEGIS-7-Anchors
   tail -1 AEGIS-7-Anchors/anchors.jsonl > anchor.json
   ```
2. Pick the TPM public key: read `tpm_key_id` in the anchor (`v2-slb9672` for
   every anchor since 2026-10-07). If the field is missing, use the keyring row
   whose sequence range contains `last_seq`.
3. Check you hold the right key: `sha256sum <pem>` must equal both the keyring
   value above and the anchor's `tpm_pubkey_sha256` (when present).
4. Run the verifier:
   ```bash
   python3 verify_anchor.py anchor anchor.json \
       keys/tpm2_pubkey_v2_slb9672.pem aegis7_mldsa65_pub.bin
   ```
5. Read the result. Real output for the anchor of 2026-10-09T01:12:42Z:
   ```
     root       41c8846e7718915f8a79de1cff600d9f680c6498dc911420844d272e6d36756e
     leaf_count 5,824,206   depth 23
     last_seq   6334944
     timestamp  2026-10-09T01:12:42Z
     sig_alg    RSA-2048 PKCS1 SHA256 (TPM 0x81000001) over ASCII hex of merkle_root

     depth vs leaf_count coerent : DA
     semnatura TPM valida        : DA
     semnatura ML-DSA-65 valida  : DA

     REZULTAT: ancora autentica.
   ```
   The same anchor checked against the v1 key reports
   `semnatura TPM valida : NU` / `ANCORA INVALIDA`, which is expected: use the
   key named by `tpm_key_id`.

| Line | Meaning |
|---|---|
| `root` | Merkle root over the audit entries covered by this anchor |
| `leaf_count` / `depth` | Number of leaves and resulting tree height |
| `depth vs leaf_count` | The declared depth matches what `leaf_count` requires. A mismatch means the tree shape was misreported. |
| `semnatura TPM valida` | The root was signed by the private key held in the device's TPM (handle `0x81000001`), which cannot be exported. |
| `semnatura ML-DSA-65 valida` | The root was also signed with ML-DSA-65 (FIPS 204), which is not broken by Shor's algorithm. |

`DA` means yes, `NU` means no. The script is in Romanian; the cryptography is not.

## Merkle scheme

RFC 6962 style, stated in each anchor's `leaf_scheme` field:

```
leaf(h)    = SHA256( 0x00 || bytes.fromhex(h) )      # h = the entry's "hash" field (hex)
node(l, r) = SHA256( 0x01 || l || r )
```

- The `0x00` / `0x01` prefixes are domain separation: a leaf can never be
  presented as an internal node (second-preimage protection).
- **Odd node promotion**: when a level has an odd number of nodes, the last one
  is promoted unchanged to the next level. It is *not* duplicated
  (Bitcoin-style duplication gives a different root).
- Leaves are the `hash` field of every in-chain audit entry, in file order.
  `leaf_count` is therefore the number of leaves, not a sequence number; do not
  expect it to equal `last_seq`.
- Both signatures are computed over the **ASCII hex representation** of the
  root (64 lowercase hex characters, encoded as ASCII), not over its 32 raw
  bytes. Signing or verifying the raw digest instead produces a failure.

## Checking that an entry is in the tree

If you hold a specific audit entry and want to prove it sits under a signed
root, you need an inclusion proof from the device:

```bash
python3 verify_anchor.py inclusion <anchor.json> <entry_hash_hex> <proof.json>
```

## What a passing result proves — and what it does not

**It proves** the root was signed by the holders of these private keys. If
that root was published externally at the stated time, the history it covers
cannot be altered afterwards without contradicting the published record.

**It does not prove** the entries were true when written. AEGIS-7 attests to
what the sensors reported and that nobody changed it afterwards. It cannot
attest that a sensor was calibrated, honest, or working.

**It does not cover** entries written after the anchor. Anchoring runs every
90 minutes, or immediately when the health state degrades. Between anchors, an
attacker with root on the device could rewrite recent entries; anything already
anchored is out of reach.

**For sequences 6092121 – 6237824** (the unsigned window above), no TPM
signature existed at write time; they are attested only from the first v2
anchor onward.

## Sample anchors

| File | Date | Key | Why it's here |
|---|---|---|---|
| `anchors/anchor-first-dualsigned.json` | 2026-08-08 | v1 | First anchor carrying both signatures |
| `anchors/anchor-sample.json` | 2026-08-20 | v1 | Mid-series |
| `anchors/anchor-latest.json` | 2026-10-09 | v2 | Most recent at time of publication |

The first two verify with the v1 key, the latest with v2; all three verify
against the same ML-DSA-65 key.
