# Production Deployment Proposal: NTPC Safety Monitor

This document outlines the proposal, specifications, costing, and rollout plan for moving the AI-based PPE Detection system from Proof of Concept (PoC) to a production-grade plant gate deployment.

---

## 1. Executive Summary

The NTPC PPE Compliance Monitor PoC has demonstrated high precision ($\ge 75\%$) and real-time processing throughput ($\approx 57$ combined FPS) running on local edge hardware. 

To operationalize this at entry gates, we propose a centralized **Local Edge-First Architecture**. This design processes all video feeds locally on-site to minimize bandwidth, latency, and cloud recurring costs, while syncing metadata to a dashboard portal.

---

## 2. Recommended Production Hardware Specification

To support 4 to 8 concurrent high-definition CCTV streams operating 24/7 in an industrial environment, the following hardware is recommended:

### 2.1. Edge AI Workstation (Central Processing Node)
- **Processor**: Intel Xeon Silver or Core i7 (14th Gen)
- **Graphics Card**: NVIDIA RTX 4080 (16 GB VRAM) or NVIDIA RTX A4000 (16 GB VRAM) for enterprise-grade 24/7 reliability and hardware-accelerated tracking.
- **Memory**: 32 GB DDR5 RAM
- **Storage**: 1 TB NVMe SSD (OS + active frame caching) + 2 TB SATA HDD (for database storage and historical screenshots)
- **OS**: Ubuntu LTS 24.04 (highly optimized for CUDA pipelines)

### 2.2. Industrial Camera Nodes (Gate Ingestion)
- **Camera Type**: Fixed Bullet IP CCTV Cameras
- **Resolution**: 1080p (1920x1080) at 15–20 FPS
- **Lens**: Varifocal 2.8–12mm lens (adjustable to focus on the gate walking line from 3–5 meters distance)
- **Protocols**: RTSP / ONVIF compliant
- **Environmental**: IP67 weather-rated, IK10 vandal-proof housing (with sunshields to reduce outdoor lens glare)

### 2.3. Network Infrastructure
- **Switch**: 8-Port Gigabit PoE+ Industrial Network Switch
- **Cabling**: Cat6 Shielded twisted pair (STP) cabling to reduce electromagnetic interference from high-voltage plant hardware.

---

## 3. Production Software Stack & Network Topology

```
                       [ IP Cameras: Gate 1 & Gate 2 ]
                                      │
                                (PoE Cat6)
                                      │
                         [ Industrial PoE+ Switch ]
                                      │
                                  (Gigabit)
                                      │
                  ┌───────────────────┴───────────────────┐
                  ▼                                       ▼
       [ MediaMTX RTSP Server ]               [ PostgreSQL DB (Local) ]
                  │                                       ▲
              (RTSP Feeds)                       (Metadata / Event Log)
                  ▼                                       │
     [ Multi-Camera Inference ] ──────────────────────────┘
                  │
        (Confirmed Violations)
                  ▼
      [ Local Object Storage ] (Save Screenshots)
                  │
             (HTTPS / LAN)
                  ▼
         [ Web Dashboard ] <─── (Supervisor Web Browser)
```

- **Docker Containerization**: Deploy backend and frontend services via Docker Compose for easy scaling and updates.
- **Local Database Mode**: Fall back entirely to a local PostgreSQL instance running inside a Docker container on the workstation, eliminating external internet dependencies.
- **Relay Server**: Maintain MediaMTX for stream management, and run OpenCV capture loops.

---

## 4. Cost Estimation (Estimated Pricing in INR)

Below is an indicative budget for a single-gate deployment supporting 4 active camera channels:

| Component | Description | Qty | Unit Cost (INR) | Total Cost (INR) |
|-----------|-------------|-----|-----------------|------------------|
| **Edge Server** | Xeon workstation + NVIDIA RTX 4080 | 1 | 2,20,000 | 2,20,000 |
| **IP Cameras** | Hikvision/Dahua 2MP PoE Bullet | 4 | 7,500 | 30,000 |
| **Network Switch**| Cisco/D-Link 8-Port Gigabit PoE+ | 1 | 12,000 | 12,000 |
| **Storage HDD** | WD Purple 4TB Surveillance HDD | 1 | 9,500 | 9,500 |
| **Cabling & Inst.**| Cat6 STP cabling + Conduit + Mounting | 1 | 25,000 | 25,000 |
| **Server Cabinet**| 6U Wallmount Server Rack with UPS | 1 | 15,000 | 15,000 |
| **Total Hardware**| | | | **3,11,500** |

---

## 5. Deployment Rollout Timeline

A standard gate deployment is estimated to take **4 weeks**:

```
Wave 1: Site Survey & Cabling (Week 1)
├── Physical camera mounting at Gate 1/2
└── Cabling back to central rack

Wave 2: Hardware Provisioning (Week 2)
├── Server assembly & OS installation
└── Network config, stream routing in MediaMTX

Wave 3: AI Engine Calibration (Week 3)
├── Stream calibration & confidence tuning
└── Shift configuration & test alert runs

Wave 4: Supervisor Training & Handover (Week 4)
├── Dashboard setup on guard room monitor
└── User testing & feedback log
```

---

## 6. Edge-First Architecture Benefits

1. **Zero Recurring Data Costs**: Video is processed entirely on the local network. No video streams or screenshots are continuously uploaded to cloud networks, saving massive ISP bandwidth costs.
2. **Minimal Latency**: Processing frame inference locally achieves sub-80ms latencies, enabling instant alerts.
3. **Data Privacy**: All worker metrics and violation logs are held securely inside the NTPC local server.
4. **Offline Resilience**: The system remains functional even if the main plant network loses external internet connectivity.
