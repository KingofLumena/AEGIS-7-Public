# AEGIS-7: Cryptographic Audit System for Autonomous Missions

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](docs/STATUS.md)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)

**Fast. Verifiable. Self-Healing.**

AEGIS-7 is a Byzantine-resilient cryptographic audit infrastructure for autonomous systems operating in disconnected or high-risk environments. It provides real-time evidence of system state, enabling instant decision-making coupled with post-flight forensics.

Built for scenarios where you can't phone home, can't trust a single node, and need cryptographic proof of what actually happened.

---

## The Problem

Autonomous systems face an impossible trade-off:

- **Speed:** Decisions must happen in milliseconds (no time for cryptography)
- **Trust:** Every log must be tamper-evident (can't skip verification)  
- **Resilience:** Single-node failure shouldn't cascade into mission loss

Existing solutions pick two. **AEGIS-7 does all three.**

---

## How It Works
┌─ Raspberry Pi 5 (Master Auditor)
│  ├─ Real-time checkpoint generation
│  ├─ Health monitoring (temp, disk, battery, quorum)
│  ├─ Tamper detection (GPIO-based enclosure sensor)
│  └─ TPM 2.0 cryptographic anchor (RSA-2048)
│
├─ 3x ESP32-P4 (Witness Nodes)
│  ├─ Byzantine quorum voting
│  ├─ Independent signature generation
│  └─ Self-diagnostics (IMU, temperature)
│
└─ Sensors
├─ GPS (VK-162): Time + Position anchor
├─ IMU (MPU-6050 × 3): Motion + Temperature
└─ UPS (Waveshare I2C): Battery monitoring

**Data Flow:**
System Event → Audit Entry → Hash (SHA-256)
↓
TPM Signs (RSA-2048)
↓
3x ESP32-P4 Nodes Vote (Byzantine consensus)
↓
2/3 Signatures = Checkpoint ACCEPTED
↓
Entry Sealed (timestamp + GPS + proof)
↓
AEGIS-7 Audit Chain (1.15M+ entries, verifiable
---

## Key Features

✅ **Byzantine Fault Tolerance**
- 3-node quorum: tolerates 1 node failure, continues mission
- Tested: 3/3 → 2/3 → 1/3 degradation modes verified
- All checkpoint decisions require 2/3 consensus (cryptographically signed)

✅ **Cryptographic Proof**
- RSA-2048 TPM signing (keys in hardware, not software)
- SHA-256 entry linking (tampering impossible without detection)
- HMAC validation (detects modification attempts)

✅ **Tamper Detection**
- GPIO-based enclosure sensor (reed relay on GPIO17)
- Instant alerts on physical intrusion
- Graceful service shutdown on compromise

✅ **Real-Time Health Monitoring**
- State machine: GREEN/YELLOW/RED/BLACK
- Metrics: temperature, disk usage, battery, quorum status
- <1 second detection latency

✅ **Hardware Watchdog**
- Kernel freeze recovery (15-second auto-reset)
- Service auto-restart (systemd Restart=always)
- Graceful shutdown on battery depletion (<8% UPS)

✅ **GPS Time Anchor**
- Position + UTC timestamp per checkpoint
- Spoofing detection: Byzantine agreement across NTP + GPS + TPM RTC
- Multi-source validation (Week 1 feature)

---

## Architecture Layers

### Layer 1: Decision Engine (AEGIS-8, in development)
- <50ms anomaly detection
- No cryptographic overhead in critical path
- Pre-computed action queues

### Layer 2: Audit Witness (AEGIS-7, production)
- Sub-500ms checkpoint latency
- Async TPM signing (off-cycle)
- Byzantine quorum verification
- Zero impact on decision speed

### Layer 3: Forensic Archive
- Complete audit chain (entries linked via HMAC)
- Post-flight analysis capability
- Legal/regulatory compliance evidence

---

## Proven Capabilities

| Feature | Status | Evidence |
|---------|--------|----------|
| Byzantine Consensus (3/3 → 2/3 → 1/3) | ✅ Tested | Failure injection test suite |
| Quorum Voting | ✅ Tested | Live logs: 1.15M+ checkpoint decisions |
| Tamper Detection | ✅ Implemented | GPIO17 logic + freeze_services() |
| Health States (GREEN/YELLOW/RED/BLACK) | ✅ Coded | State transitions verified live |
| Hardware Watchdog | ✅ Active | RuntimeWatchdogSec=15s |
| Temperature Monitoring | ✅ Live | IMU bug fixed, realistic readings (26-50°C) |
| GPS Anchoring | ✅ Working | 10+ satellites, position locked |
| Graceful Shutdown | ✅ Tested | Battery failsafe <8% UPS |

---

## Use Cases

### Aerospace / Defense
- **Autonomous test vehicles** (Starship-adjacent): Cryptographic proof of anomalies, instant root cause
- **Distributed sensor networks**: Byzantine consensus over noisy links, fault tolerance
- **High-altitude / space missions**: Offline operation, verification at recovery

### Commercial Drones
- **Flight compliance**: Verifiable logs for insurance claims
- **Regulatory audit trail**: EU/FAA autonomous operation proof
- **Incident investigation**: Tamper-evident evidence of what happened

### Remote Robotics
- **Offline operation**: No cloud needed, verification post-recovery
- **Failure analysis**: Exact sequence of events with cryptographic proof
- **Autonomous decision logging**: Who/what/when/where with proof

---

## Performance

| Metric | Value |
|--------|-------|
| Checkpoint latency | ~500ms (TPM async) |
| Quorum decision time | <2.5s (Byzantine consensus) |
| Audit throughput | 46 entries/min (~0.76/sec) |
| Byzantine tolerance | 1/3 node failure |
| Tamper detection | Instant (<100ms) |
| Storage efficiency | ~800KB per 24h |
| Hardware watchdog recovery | 15s |
| Battery failsafe | <8% UPS → graceful shutdown |

---

## Getting Started

### Hardware Requirements
- Raspberry Pi 5 (8GB+)
- 3× ESP32-P4 microcontrollers
- TPM 2.0 module
- GPS module (VK-162)
- IMU (MPU-6050 × 3)
- UPS HAT (Waveshare I2C, optional)

### Quick Start
```bash
# Clone repository
git clone https://github.com/KingofLumena/AEGIS-7-Private.git

# Install dependencies
pip install pyserial cryptography gpiozero smbus2 requests paho-mqtt --break-system-packages

# Start services
sudo systemctl start aegis7_apex cp_monitor aegis7_health

# Verify status
~/aegis7_status.sh
```

---

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)** — System design, data flow, Byzantine quorum logic
- **[Security Model](docs/SECURITY.md)** — Threat model, limitations, cryptographic guarantees
- **[Test Results](docs/TEST_RESULTS.md)** — Failure injection, tamper detection proofs
- **[Roadmap](docs/ROADMAP.md)** — AEGIS-8 fast path, LoRa mesh, quantum resistance

---

## Known Limitations

❌ **GPS spoofing:** Sophisticated GNSS spoofing undetected (requires external time reference)  
❌ **Distributed geography:** All 3 nodes must share local network (no WAN quorum yet)  
❌ **Hardware root access:** JTAG + TPM key extraction = compromise  
❌ **Real-time crypto:** Entry signatures are async (acceptable for audit, not for real-time voting)  
❌ **Quantum resistance:** RSA-2048 not post-quantum (ML-DSA migration planned)

---

## Research & Development

**Week 1: NTP + GPS Spoofing Validator**
- Multi-source time validation (NTP + GPS + TPM RTC)
- Byzantine agreement across time sources
- Spoofing detection and rejection

**Week 2-12: Full System Hardening**
- ML-DSA quantum resistance
- LoRa long-range distributed quorum
- Predictive anomaly detection (AEGIS-8)
- Security audit and optimization

---

## Contributing

This is a solo technical build, but serious engineers welcome.

**If you:**
- Have aerospace/autonomous systems experience
- Can run hardware tests (Pi5 + ESP32-P4)
- Want to build AEGIS-8 or optimize AEGIS-7

**Contact:** [DM on GitHub](https://github.com/KingofLumena) or open an issue.

---

## License

MIT License — See [LICENSE](LICENSE) for details.

---

## Citation

If you use AEGIS-7 in research or production:

```bibtex
@software{aegis7_2026,
  author = {King of Lumena},
  title = {AEGIS-7: Cryptographic Audit System for Autonomous Missions},
  year = {2026},
  url = {https://github.com/KingofLumena/AEGIS-7}
}
```

---

## Status

**Production Ready for:**
- Audit logging in autonomous systems
- Tamper-evident flight record generation
- Byzantine fault-tolerant consensus

**In Development:**
- AEGIS-8 (fast decision engine, <50ms)
- LoRa mesh networking (WAN quorum)
- Quantum-resistant signing (ML-DSA)

---

**Last Updated:** July 2026  
**Current Checkpoint:** seq=1.15M+ | Quorum: 3/3 | Health: GREEN
