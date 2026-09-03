# Verifying an AEGIS-7 anchor

AEGIS-7 periodically computes a Merkle root over its audit chain, signs that
root twice, and publishes it externally. This directory contains everything
needed to check those signatures yourself.

You do not need access to the device, and you do not need any AEGIS-7 code
beyond the single script below.

## What you need

```
pip install cryptography          # required — checks the TPM RSA signature
pip install liboqs-python         # optional — checks the ML-DSA-65 signature
```

Without `liboqs-python` the script still runs; it reports the post-quantum
signature as present but unverified.

## Run it

```bash
cd verification
python3 verify_anchor.py anchor \
    anchors/anchor-latest.json \
    aegis7_tpm_pub.pem \
    aegis7_mldsa65_pub.bin
```

## Reading the output

```
  root       f5050920a3cd3d179e22840eeb90e684cbd40ec5764a19e05906de3b7d9bcc56
  leaf_count 3,777,837   depth 22
  last_seq   4279342
  timestamp  2026-09-03T21:31:12Z
  depth vs leaf_count coerent : DA
  semnatura TPM valida        : DA
  semnatura ML-DSA-65 valida  : DA
  REZULTAT: ancora autentica.
```

| Line | Meaning |
|---|---|
| `root` | Merkle root over every audit entry up to `last_seq` |
| `leaf_count` / `depth` | Number of leaves and resulting tree height |
| `depth vs leaf_count` | The declared depth matches what `leaf_count` requires. A mismatch means the tree shape was misreported. |
| `semnatura TPM valida` | The root was signed by the private key held in the device's TPM (handle `0x81000001`), which cannot be exported. |
| `semnatura ML-DSA-65 valida` | The root was also signed with ML-DSA-65 (FIPS 204), which is not broken by Shor's algorithm. |

`DA` means yes. The script is in Romanian; the cryptography is not.

## What a passing result proves — and what it does not

**It proves** the root was signed by the holder of these two private keys. If
that root was published externally at the stated time, the history it covers
cannot be altered afterwards without contradicting the published record.

**It does not prove** the entries were true when written. AEGIS-7 attests to
what the sensors reported and that nobody changed it afterwards. It cannot
attest that a sensor was calibrated, honest, or working.

**It does not cover** entries written after the anchor. Anchoring runs every
90 minutes, or immediately when the health state degrades. Between anchors, an
attacker with root on the device could rewrite recent entries; anything already
anchored is out of reach.

## Sample anchors

| File | Date | Why it's here |
|---|---|---|
| `anchors/anchor-first-dualsigned.json` | 2026-08-08 | First anchor carrying both signatures |
| `anchors/anchor-sample.json` | — | Mid-series |
| `anchors/anchor-latest.json` | 2026-09-03 | Most recent at time of publication |

The first and last are roughly a month apart and verify against the same keys.

## Checking that an entry is in the tree

If you hold a specific audit entry and want to prove it sits under a signed
root, you need an inclusion proof from the device:

```bash
python3 verify_anchor.py inclusion <anchor.json> <entry_hash_hex> <proof.json>
```

## Merkle scheme

RFC 6962 style, stated in each anchor's `leaf_scheme` field:

```
leaf(h)    = SHA256( 0x00 || bytes.fromhex(h) )
node(l, r) = SHA256( 0x01 || l || r )
```

An odd node at any level is promoted unchanged to the next level.

Both signatures are computed over the **ASCII hex representation** of the root,
not over its raw bytes. Signing the raw digest instead will produce a
verification failure.
