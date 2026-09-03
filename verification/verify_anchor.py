#!/usr/bin/env python3
"""
verify_anchor.py — verifica independent o ancora AEGIS-7.

NU depinde de niciun cod AEGIS-7 si nu are nevoie de acces la dispozitiv.
Singura dependenta: pip install cryptography

Utilizare:
  verify_anchor.py anchor <anchor.json> <tpm_pub.pem>
  verify_anchor.py inclusion <anchor.json> <entry_hash_hex> <proof.json>

Schema (RFC 6962 style, declarata in campul leaf_scheme al ancorei):
  leaf(h)        = SHA256( 0x00 || bytes.fromhex(h) )
  node(l, r)     = SHA256( 0x01 || l || r )
  numar impar de noduri la un nivel -> ultimul e promovat neschimbat
Semnatura: RSASSA-PKCS1-v1_5 / SHA256 peste reprezentarea ASCII hex a merkle_root.
"""
import json, os, sys, hashlib

def leaf(h):    return hashlib.sha256(b'\x00' + bytes.fromhex(h)).digest()
def node(l, r): return hashlib.sha256(b'\x01' + l + r).digest()


def verify_signature(anchor, pem_path):
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.exceptions import InvalidSignature

    with open(pem_path, 'rb') as f:
        pub = serialization.load_pem_public_key(f.read())
    try:
        pub.verify(bytes.fromhex(anchor['signature']),
                   anchor['merkle_root'].encode('ascii'),
                   padding.PKCS1v15(), hashes.SHA256())
        return True
    except InvalidSignature:
        return False


def verify_inclusion(entry_hash_hex, proof, expected_root_hex):
    h = leaf(entry_hash_hex)
    for sibling_hex, sibling_is_right in proof:
        sib = bytes.fromhex(sibling_hex)
        h = node(h, sib) if sibling_is_right else node(sib, h)
    return h.hex() == expected_root_hex


def verify_pq_signature(anchor, pq_pub_path):
    """Verifica ML-DSA-65 daca liboqs-python e disponibil.
    Returneaza: True (valid), False (invalid), None (nu se poate verifica)."""
    pq_sig = anchor.get('pq_signature')
    if not pq_sig:
        return None
    try:
        import oqs
    except ImportError:
        return None
    if not pq_pub_path or not os.path.exists(pq_pub_path):
        return None
    try:
        with open(pq_pub_path, 'rb') as f:
            pub = f.read()
        with oqs.Signature('ML-DSA-65') as s:
            return s.verify(anchor['merkle_root'].encode('ascii'),
                            bytes.fromhex(pq_sig), pub)
    except Exception:
        return False


def cmd_anchor(anchor_path, pem_path, pq_pub_path=None):
    anchor = json.load(open(anchor_path))
    print(f"  root       {anchor['merkle_root']}")
    print(f"  leaf_count {anchor['leaf_count']:,}   depth {anchor['depth']}")
    print(f"  last_seq   {anchor['last_seq']}")
    print(f"  timestamp  {anchor['utc']}")
    print(f"  sig_alg    {anchor['sig_alg']}")

    d = anchor['depth']; n = anchor['leaf_count']
    consistent = (n <= 2 ** d) and (n > 2 ** (d - 1) if d else n == 1)
    print(f"\n  depth vs leaf_count coerent : {'DA' if consistent else 'NU'}")

    ok = verify_signature(anchor, pem_path)
    print(f"  semnatura TPM valida        : {'DA' if ok else 'NU'}")

    pq = verify_pq_signature(anchor, pq_pub_path)
    if anchor.get('pq_signature'):
        if pq is True:
            print(f"  semnatura ML-DSA-65 valida  : DA")
        elif pq is False:
            print(f"  semnatura ML-DSA-65 valida  : NU")
            print("\n  REZULTAT: ANCORA INVALIDA (semnatura post-cuantica)")
            return 1
        else:
            print(f"  semnatura ML-DSA-65         : prezenta, neverificata")
            print("     (necesita liboqs-python + cheia publica ca argument 4)")
    if not (ok and consistent):
        print("\n  REZULTAT: ANCORA INVALIDA")
        return 1
    print("\n  REZULTAT: ancora autentica.")
    print("  Radacina de mai sus a fost semnata de detinatorul cheii private")
    print("  corespunzatoare acestui PEM. Daca radacina a fost publicata extern")
    print("  la momentul indicat, istoria acoperita de ea nu mai poate fi")
    print("  rescrisa fara a contrazice inregistrarea publica.")
    return 0


def cmd_inclusion(anchor_path, entry_hash_hex, proof_path):
    anchor = json.load(open(anchor_path))
    proof = json.load(open(proof_path))
    print(f"  intrare    {entry_hash_hex}")
    print(f"  proof      {len(proof)} noduri ({len(proof) * 32} B)")
    print(f"  root       {anchor['merkle_root']}")
    ok = verify_inclusion(entry_hash_hex, proof, anchor['merkle_root'])
    print(f"\n  REZULTAT: {'intrarea ESTE inclusa in aceasta radacina' if ok else 'INCLUDERE ESUATA'}")
    return 0 if ok else 1


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    mode = sys.argv[1]
    print(f"\n=== AEGIS-7 anchor verification ({mode}) ===\n")
    if mode == 'anchor' and len(sys.argv) in (4, 5):
        pq = sys.argv[4] if len(sys.argv) == 5 else None
        sys.exit(cmd_anchor(sys.argv[2], sys.argv[3], pq))
    elif mode == 'inclusion' and len(sys.argv) == 5:
        sys.exit(cmd_inclusion(sys.argv[2], sys.argv[3], sys.argv[4]))
    print(__doc__); sys.exit(2)
