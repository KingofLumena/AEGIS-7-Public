# AEGIS-7: Cryptographic Audit Infrastructure for Autonomous Systems

**Tamper-evident proof of what your sensors actually recorded — verifiable by anyone, years later, without trusting the operator.**

AEGIS-7 is a Byzantine-resilient audit layer for autonomous and remote systems. It produces cryptographic evidence of system state that survives disconnection, resists tampering, and can be independently verified against an externally published anchor.

Running continuously on production hardware since July 2026. **3.4M+ signed entries. Zero unexplained gaps.**

---

## The Problem

When an autonomous system reports something — a detection, an anomaly, a position — three questions follow:

1. **Did it actually record this?** Logs are text files. Text files can be edited.
2. **Was the sensor telling the truth?** GNSS can be spoofed. A single receiver cannot detect its own deception.
3. **Can you prove it later?** Six months on, in front of a regulator, an insurer, or a customer — what backs the claim?

Standard logging answers none of these. Signed logging answers the first, but only if the signing key isn't extractable and the operator isn't the one holding it.

AEGIS-7 addresses all three, as a **parallel witness layer** — it observes and attests, but never sits in the critical decision path. If AEGIS-7 fails, your system keeps flying.

---

## What It Actually Does

### Cryptographic chain of custody
Every entry is SHA-256 linked to the previous one. Breaking the chain anywhere invalidates everything after it. The chain is append-only; there is no update path in the code.

### Dual signatures — classical and post-quantum
Every anchor carries two independent signatures over the same Merkle root:

- **TPM 2.0 RSA-2048** — private key generated inside the TPM, non-extractable by design (Infineon SLB9)
- **ML-DSA-65** — NIST FIPS 204, post-quantum, via liboqs

Both are verifiable offline with the public keys. Tampering with either signature produces a hard verification failure.

### Byzantine quorum across independent hardware
Three ESP32-P4 witness nodes vote on each checkpoint. Consensus at 2-of-3. Compromising one node does not compromise the record. Degradation modes (3/3 → 2/3 → 1/3) verified by failure injection, not assumed.

### Dual-receiver GNSS anti-spoofing
Two independent GNSS receivers from different manufacturers, on different protocols — u-blox 7 (UBX binary) and Quectel L76K (NMEA). Position cross-check on every fix.

*Live at time of writing: dual fix, 25 satellites, cross-check delta 2.5 m, spoofing alert clear.*

A spoofer must fool both receivers, on both protocols, consistently — a materially harder problem than fooling one.

### External anchoring
Merkle roots are published externally and RFC 3161 timestamped via a third-party TSA. Once a root is published, the history it covers cannot be rewritten without contradicting a record you do not control.

*Current anchor: 2,925,481 leaves, depth 22, both signatures verified.*

### Continuous self-verification
The system audits itself. Twenty-four automated checks — services, timers, TPM, GNSS, IMU tamper, UPS, disk, chain integrity, file hashes — run on schedule and write results into the audit chain. Backups are restore-tested automatically, daily, against a checksummed export.

A system that claims to prove things should be able to prove things about itself.

---

## Verified Status

| Capability | State | Evidence |
|---|---|---|
| Audit chain | Live | 3.4M+ entries, continuous since July 2026 |
| Byzantine quorum | Live | 3/3 nodes, degradation tested by injection |
| TPM signing | Live | RSA-2048, Infineon SLB9, PCR verified |
| Post-quantum signing | Live | ML-DSA-65, verification confirmed |
| GNSS anti-spoofing | Live | Dual fix, cross-check 2.5–8 m typical |
| External anchoring | Live | RFC 3161, 90-minute cadence |
| Self-test | Automated | 24 checks, results written to chain |
| Restore test | Automated | Daily, against checksummed export |
| Endurance | Verified | 50-day unattended run, 2.8M entries added |
| Incident recovery | Documented | Tamper simulation, fork event, chain restored |

---

## What It Does *Not* Do

Stated plainly, because you will find out anyway.

**No flight heritage.** This has never been to orbit. It runs on ground hardware in Germany. Space qualification, radiation tolerance, and thermal-vacuum survival are unaddressed.

**No formal certification.** No DO-178C, no ECSS, no common criteria. The cryptography uses standard primitives correctly; the *process* around it is not certified.

**Physical access defeats it.** JTAG plus TPM key extraction compromises the system. Physical security is assumed, not provided.

**The post-quantum key is on disk.** TPM 2.0 has no ML-DSA support — the algorithm is too new. The RSA key is hardware-protected; the ML-DSA key is a file at mode 600, readable by root. This asymmetry is real and documented in the threat model rather than hidden.

**Signatures are asynchronous.** Suitable for audit and forensics. Not suitable for real-time safety-critical voting.

**Single-site quorum.** All witness nodes currently share a local network. Geographically distributed quorum over WAN is designed but not deployed.

**Untested at fleet scale.** One installation, three nodes. Behaviour across hundreds of platforms is unknown.

---

## Where It Fits

**Thermal and remote sensing operators** — When a detection triggers a response with cost or legal weight, the ability to prove the underlying data was not altered between sensor and report becomes a product feature, not overhead.

**Government and defence customers** — Procurement increasingly asks for provenance guarantees. "Trust our logs" is a weaker answer than "verify this anchor yourself."

**Insurance and regulatory compliance** — EU and FAA audit trails for autonomous platforms. Verifiable flight and operation records.

**Distributed test infrastructure** — Cryptographic proof of anomalies during test campaigns, for root cause analysis that survives dispute.

**Any system operating disconnected** — Offline operation with full verification at recovery.

---

## Why This, Specifically

The individual primitives are not novel. Merkle trees, TPM signing, and Byzantine consensus are decades old, and the anchoring approach has published prior art. No claim is made otherwise.

What is uncommon is the combination, working, on real hardware, with the failure modes actually exercised:

**It has been attacked and recovered.** The archive contains tamper simulations and a chain fork event, both with the recovery documented. A system that has never failed has never been tested.

**It refuses to lie about itself.** When the TPM is transiently unavailable, entries are marked `tpm_unavailable` rather than silently downgraded. A synthetic verification response was once patched in during development; it was reverted, and the principle stands — nothing fabricated is written to an append-only chain.

**Limitations are published, not discovered.** Everything above under "What It Does Not Do" is in the threat model. You will not find a surprise in month three that should have been on page one.

**One system, several guarantees.** Integrity, provenance, time, position, and physical tamper evidence come from a single coherent layer rather than five bolted-together tools that each need separate trust.

---

## Architecture

```
Raspberry Pi 5 — Master Auditor
  Append-only audit chain (SHA-256 linked)
  Merkle checkpoint generation
  TPM 2.0 anchor (RSA-2048, non-extractable)
  ML-DSA-65 post-quantum co-signature
  Health state machine (GREEN/YELLOW/RED/BLACK)
  Hardware watchdog, graceful shutdown on power loss

3x ESP32-P4 — Witness Nodes
  Byzantine quorum voting (2-of-3)
  Independent IMU and thermal self-diagnostics
  Serial-isolated from the auditor

Sensors
  GNSS x2 (u-blox 7 UBX + Quectel L76K NMEA) — cross-checked
  IMU x3 (MPU-6050) — motion and tamper detection
  UPS (Waveshare I2C) — battery state, controlled shutdown
  Enclosure sensor (GPIO) — physical intrusion

External
  RFC 3161 timestamping (third-party TSA)
  Public anchor publication
```

**Flow:** Event → audit entry → SHA-256 link → Byzantine vote (2/3) → checkpoint sealed with GNSS time and position → periodic Merkle root → dual signature → external publication + RFC 3161 timestamp

---

## Verification

Anchors are independently verifiable. Given an anchor file and the public keys, verification takes seconds and requires no access to the system that produced it:

```
=== AEGIS-7 anchor verification ===
  root       edba49d1794e4a65243c06e8c573aef7...
  leaf_count 2,925,481   depth 22
  depth vs leaf_count consistent : YES
  TPM signature valid            : YES
  ML-DSA-65 signature valid      : YES
  RESULT: anchor authentic.
```

That is the entire value proposition in one command.

---

## Roadmap

- Geographically distributed quorum (LoRa / WAN)
- Hardware-backed post-quantum key storage, when TPM support exists
- Fleet-scale deployment characterisation
- Formal threat model review by external cryptographers

---

## Repository Scope

This repository contains architecture documentation and standalone demonstrations. The production implementation is maintained privately.

Demonstrations included:
- `ml_dsa_demo.py` — dual-signature generation and verification
- `ntp_validator.py` — multi-source time validation
- `spoofing_demo.py` — GNSS cross-check logic

---

## Contact

If you operate autonomous or remote sensing systems and data provenance is something you have had to think about — I would value a conversation, including one where the conclusion is that this does not fit your problem.

Twenty minutes, technical, no pitch deck.

**Roman Ioan Petru** — Augsburg, Germany
baphometabufihamat@gmail.com

Live demonstration available: verification against a chain with 3.4M+ entries, running now.

---

## License

Proprietary — all rights reserved. See [LICENSE](LICENSE).

Commercial licensing available on request.

---

*Status: active development, continuous operation. Production-ready for audit logging and tamper-evident record generation. Not qualified for spaceflight.*
