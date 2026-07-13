# AEGIS-7: Cryptographic Audit System for Autonomous Missions

**Byzantine-resilient cryptographic audit infrastructure for autonomous systems operating in disconnected or high-risk environments.**

AEGIS-7 provides tamper-evident evidence of system state using distributed nodes and TPM signing — cryptographic proof of what autonomous systems and test infrastructure actually did, even in disconnected environments.

---

## The Problem

Autonomous systems face a trade-off:

- **Speed:** Decisions must happen in milliseconds
- **Trust:** Every log must be tamper-evident
- **Resilience:** Single-node failure shouldn't cascade into mission loss

AEGIS-7 addresses all three by running cryptographic verification as a parallel witness layer, not in the critical decision path.

---

## Architecture

```
Raspberry Pi 5 (Master Auditor)
  - Real-time checkpoint generation
  - Health monitoring (temp, disk, battery, quorum)
  - Tamper detection (GPIO-based enclosure sensor)
  - TPM 2.0 cryptographic anchor (RSA-2048)

3x ESP32-P4 (Witness Nodes)
  - Byzantine quorum voting (2-of-3)
  - Independent signature generation
  - Self-diagnostics (IMU, temperature)

Sensors
  - GPS (VK-162): Time + Position anchor
  - IMU (MPU-6050 x3): Motion + Temperature
  - UPS (Waveshare I2C): Battery monitoring
```

**Data Flow:** System Event → Audit Entry → SHA-256 Hash → TPM RSA-2048 Signature → 3x ESP32-P4 Byzantine Vote → 2/3 Consensus = Checkpoint Accepted → Entry Sealed with timestamp + GPS + proof

---

## Key Features

**Byzantine Fault Tolerance** — 3-node quorum tolerates 1 node failure and continues. Tested: 3/3 → 2/3 → 1/3 degradation modes verified via failure injection.

**Cryptographic Proof** — RSA-2048 TPM signing (keys in hardware, not software), SHA-256 entry linking, HMAC validation.

**Tamper Detection** — GPIO-based enclosure sensor (reed relay on GPIO17), instant alerts on physical intrusion, graceful service shutdown on compromise.

**Real-Time Health Monitoring** — State machine (GREEN/YELLOW/RED/BLACK) tracking temperature, disk, battery, and quorum status.

**Hardware Watchdog** — Kernel freeze recovery (15s auto-reset), service auto-restart, graceful shutdown on battery depletion.

**GPS Time Anchor** — Position + UTC timestamp per checkpoint, with multi-source spoofing detection (NTP + GPS + TPM RTC Byzantine agreement).

---

## Current Status

| Feature | Status |
|---------|--------|
| Byzantine Consensus (3/3 → 2/3 → 1/3) | Tested via failure injection |
| Quorum Voting | Live (1M+ checkpoint decisions) |
| Tamper Detection | Implemented (GPIO17) |
| Health States | Verified live |
| Hardware Watchdog | Active |
| Temperature Monitoring | Live (26-50°C readings) |
| GPS Anchoring | Working (10+ satellites) |
| Graceful Shutdown | Tested (battery failsafe) |

---

## Use Cases

**Aerospace / Defense** — Autonomous test vehicles: cryptographic proof of anomalies for root cause analysis. Distributed sensor networks with Byzantine consensus over noisy links.

**Commercial Drones** — Verifiable flight logs for insurance and regulatory compliance (EU/FAA audit trails).

**Remote Robotics** — Offline operation with verification at recovery; tamper-evident record of autonomous decisions.

---

## Known Limitations

- **GPS spoofing:** Sophisticated GNSS spoofing requires external time reference (multi-source validation in development)
- **Distributed geography:** All nodes currently share a local network (WAN quorum planned)
- **Hardware root access:** Physical JTAG + TPM key extraction compromises the system
- **Real-time crypto:** Entry signatures are asynchronous — suitable for audit, not real-time safety-critical voting
- **Quantum resistance:** RSA-2048 is not post-quantum (ML-DSA migration planned)

---

## Roadmap

- Multi-source NTP + GPS spoofing validation
- ML-DSA post-quantum signatures
- LoRa long-range distributed quorum
- AEGIS-8: sub-50ms fast-path decision engine (parallel to the cryptographic witness layer)

---

## License

MIT License

---

**Status:** Active development. Production-ready for audit logging and tamper-evident record generation.
```
