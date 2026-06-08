# DLMS/COSEM for the GridTokenX Platform: A Deep Technical Reference and Integration Blueprint

## TL;DR
- **DLMS/COSEM (IEC 62056) is the correct meter-side protocol for GridTokenX in Thailand** — it is what PEA, MEA and EGAT actually deploy (Itron OpenWay Riva, EDMI, Trilliant/Samart, Landis+Gyr/Iskraemeco), it natively models bidirectional prosumer energy via standard OBIS codes (import 1.0.1.8.0.255, export 1.0.2.8.0.255) and 15-minute load profiles, and Security Suite 1 (AES-128-GCM + ECDSA-P256) provides the cryptographic root of trust. But DLMS's PKI assumes a single utility owner, not a blockchain settlement layer — so DLMS signatures alone cannot anchor on-chain attestations without a re-signing/attestation bridge.
- **The integration should be a dedicated `dlms-gateway` microservice** sitting at the edge (or regional concentrator), upstream of the existing aggregator-bridge and chain-bridge. It terminates DLMS associations, normalizes COSEM objects to a canonical schema (preserving OBIS code, scaler/unit, timestamp, status, system-title and invocation counter), batches 15-minute intervals into a Merkle commitment, re-signs with an edge secure element (ATECC608/SE050), and crosschecks against Switchboard TEE attestation before the chain-bridge's policy engine authorizes a Solana transaction.
- **Recommended posture: Security Suite 1 minimum (Suite 2 where meters support P-384), HLS-5 (GMAC) or HLS-7 (ECDSA) authentication, per-interval signature + windowed Merkle batch + TEE crosscheck for attestation, and an append-only tamper-evident APDU audit log.** Treat manufacturer-specific OBIS codes and association limits as the main field-integration risks; Koh Tao itself is a former isolated 6 MW diesel microgrid now fed by a 33 kV submarine cable, so islanded-grid logic must remain a first-class design constraint.

---

## Key Findings

1. **DLMS is the data-exchange application protocol; COSEM is the object/data model.** DLMS/COSEM is governed by the DLMS User Association (DLMS UA), which maintains a Type-D liaison with IEC TC13 WG14 and publishes the Blue Book (COSEM object model + OBIS), Green Book (architecture/protocols), Yellow Book (conformance) and White Book (glossary). As of 2025-2026 the current editions are Blue Book Ed. 14/15 and Green Book Ed. 10, recently extended to low-power wireless (Wi-SUN, LoRaWAN, NB-IoT).

2. **The COSEM model is object-oriented and media-agnostic.** Physical devices contain one or more logical devices, each exposing instances of standardized interface classes (ICs), addressed by 6-byte OBIS codes (logical-name referencing) or 16-bit short names. Client/server: the meter is the server, the head-end/concentrator/gateway is the client.

3. **For a solar prosumer, the workhorse objects are well-defined**: Register/Extended Register (class 3/4) for cumulative import/export energy, Profile Generic (class 7) for time-series load profiles, Clock (class 8), Data (class 1), and Disconnect Control (class 70). A 15-minute load profile is 96 entries/day per captured column.

4. **Security Suite 1 is the practical target**: AES-128-GCM authenticated encryption, ECDSA/ECDH on P-256, SHA-256, and AES-128 key wrap (RFC 3394). Suite 2 raises this to AES-256-GCM, P-384 and SHA-384. The known weaknesses are in legacy HLS variants (HLS-3 MD5, HLS-4 SHA-1), GCM nonce/invocation-counter handling, and downgrade to LLS plaintext passwords.

5. **DLMS's trust model is utility-centric.** System-titles, master/authentication/encryption keys, and invocation counters assume a utility-managed PKI and head-end. A blockchain settlement layer is a *different trust domain*; bridging requires re-attestation at the edge plus an independent crosscheck (the dual-verification pattern already in GridTokenX architecture).

6. **Thailand is committed to DLMS-based AMI.** Per Itron's June 19, 2018 announcement, PEA — with consortium partner ALT Telecom Public Company Limited — selected Itron's OpenWay Riva solution including **116,000 OpenWay Riva smart meters** in the City of Pattaya, with Itron Enterprise Edition (IEE) as the MDM and PEA Assistant Governor Pongsakorn Yuthagovit as AMI project manager; Smart Energy International notes the national rollout must scale to "around 1 million meters per year." PEA has installed 300,000+ smart meters and proposes a further one-million-meter national plan; EDMI delivers 15-minute interval data in rural Thailand; Trilliant/Samart and Landis+Gyr/Iskraemeco are also present. Thailand's P2P trading is confined to the ERC Sandbox (single-buyer market), and rooftop solar is compensated under a **net billing** scheme, not full net metering.

---

## Details

### PART A — PROTOCOL-LEVEL DEEP DIVE

#### A1. Architecture fundamentals and standardization

DLMS/COSEM is the dominant global smart-metering standard. The DLMS UA reports a large installed base of certified meter types across 150+ member manufacturers, though I could not confirm a precise current certification count from an authoritative DLMS UA source (treat any specific total as unverified). The standard descends from IEC 61334-4-41 (distribution line carrier) and is published internationally as the IEC 62056 suite, in ANSI as C12.IEC 62056, and in CENELEC as EN 62056.

- **Distinction**: *DLMS* (Device Language Message Specification) is the application-layer messaging protocol (the xDLMS services and ACSE). *COSEM* (Companion Specification for Energy Metering) is the object model — the interface classes and OBIS naming. The Blue Book specifies COSEM + OBIS; the Green Book specifies the DLMS application layer, lower layers and communication profiles.
- **The four books** (current as of 2025-2026): Blue Book (COSEM Identification System and Interface Classes, Ed. 14/15), Green Book (Architecture and Protocols, Ed. 10), Yellow Book (Conformance testing), White Book (glossary). The June 2025 Blue Book Ed. 17 excerpts and the Green Book Ed. 10 reflect the low-power-wireless extensions. Note: the long-standing reference editions widely cited in implementations are Blue Book Ed. 12.x (mapped to IEC 62056-6-2 Ed. 3) and Green Book Ed. 8.3.
- **Three-layer COSEM model**: physical device → one or more logical devices (each separately addressable; the Management Logical Device is reserved at upper HDLC address 1) → interface-class instances (objects). The SAP assignment object (0.0.41.0.0.255, class 17) enumerates logical devices.
- **Application Associations (AA)**: established via ACSE (AARQ/AARE exchange) after the lower-layer connection. The AA negotiates LN vs SN referencing, the xDLMS context (conformance block, max PDU size), and authentication. There are Public (no/low security, read-only discovery), Management, and Pre-established associations.

#### A2. COSEM Interface Classes (selected, with class_id)

| Class | ID (version) | Purpose | Key attributes/methods |
|---|---|---|---|
| Data | 1 (0) | Single value, config/identification | value (attr 2) |
| Register | 3 (0) | Measurement + scaler_unit | value (2), scaler_unit (3); method reset |
| Extended Register | 4 (0) | Register + capture time/status | value(2), scaler_unit(3), status(4), capture_time(5) |
| Demand Register | 5 (0) | Current/last average, demand | current_avg(2), last_avg(3), period(8) |
| Register Activation | 6 (0) | Register sets | — |
| Profile Generic | 7 (1) | Time-series buffer (load profile) | buffer(2), capture_objects(3), capture_period(4), sort_method(5), sort_object(6), entries_in_use(7), profile_entries(8); methods reset, capture |
| Clock | 8 (0) | Time/date | time(2), time_zone(3), status(4), dst attrs; methods adjust, shift |
| Script Table | 9 (0) | Action scripts | — |
| Schedule | 10 (0) | Time-driven actions | — |
| Special Days Table | 11 (0) | Holiday calendar | — |
| Activity Calendar | 20 (0) | TOU tariff calendar | calendar/day/week profiles; method activate |
| Association SN/LN | 12 / 15 | Object list, access rights, auth | object_list(2); method reply_to_HLS_authentication (LN method 1) |
| SAP Assignment | 17 (0) | Logical device list | SAP_assignment_list(2) |
| Register Monitor | 21 (0) | Threshold monitoring | — |
| Single Action Schedule | 22 (0) | — | — |
| Disconnect Control | 70 (0) | Remote breaker/relay | output_state(2), control_state(3), control_mode(4); methods remote_disconnect, remote_reconnect |
| Limiter | 71 (0) | Load limiting | monitored_value, thresholds |
| Security Setup | 64 (0/1) | Security suite, keys, titles | security_policy, security_suite, client/server system_title; methods key_transfer, key_agreement |
| Push Setup | 40 | Push object list, destination | push_object_list, send_destination_and_method |
| Image Transfer | 18 | Firmware upgrade | — |
| TCP-UDP / IPv4 / IPv6 setup | 41 / 42 / 48 | IP stack config | — |

**Solar/prosumer use**: bidirectional metering uses two Register objects (import A+ at 1.0.1.8.0.255, export A− at 1.0.2.8.0.255) and TOU tariff registers (E-group 1–4). A Profile Generic captures Clock + import/export power columns at a 15-minute capture_period. Disconnect Control (class 70) supports islanding/load-shed actions, relevant on Koh Tao.

#### A3. OBIS codes — structure and reference

OBIS (IEC 62056-61, now folded into IEC 62056-6-1) uses six value groups **A-B:C.D.E*F**:
- **A** = medium/energy type (0 = abstract, 1 = electricity, 6 = heat, 7 = gas, 8 = water)
- **B** = channel (instance/measurement channel; 0 when single)
- **C** = physical quantity (e.g. 1 = active power import A+, 2 = active power export A−, current/voltage groups)
- **D** = quantity processing/algorithm (e.g. 8 = time-integral/energy, 7 = instantaneous, 6 = max demand)
- **E** = tariff/classification (0 = total, 1–4 = tariff rates T1–T4)
- **F** = billing-period/historical storage (255 = not used/current)

**Reference subset for a bidirectional prosumer meter:**

| OBIS | Meaning |
|---|---|
| 1.0.1.8.0.255 | Positive active energy A+ (import), total [kWh] |
| 1.0.1.8.1 / .2 / .3 / .4 | A+ in tariffs T1–T4 |
| 1.0.2.8.0.255 | Negative active energy A− (export to grid), total [kWh] |
| 1.0.2.8.1–.4 | A− in tariffs T1–T4 |
| 1.0.1.7.0.255 | Instantaneous active power import (+A) [W] |
| 1.0.2.7.0.255 | Instantaneous active power export (−A) [W] |
| 1.0.3.8.0 / 4.8.0 | Reactive energy Q+ / Q− [kvarh] |
| 1.0.32.7.0 / 52.7.0 / 72.7.0 | Instantaneous voltage L1/L2/L3 [V] |
| 1.0.31.7.0 / 51.7.0 / 71.7.0 | Instantaneous current L1/L2/L3 [A] |
| 1.0.13.7.0 | Instantaneous power factor |
| 1.0.14.7.0 | Frequency [Hz] |
| 1.0.99.1.0.255 | Load profile (general) |
| 0.0.1.0.0.255 | Clock object |
| 0.0.96.1.0.255 | Device/meter serial number |
| 0.0.0.2.0.255 | Firmware/active firmware version |
| 0.0.40.0.0.255 | Current Association (LN) |
| 0.0.41.0.0.255 | SAP assignment |
| 0.0.43.0.0.255 | Security setup |
| 0.0.43.1.0.255 | Invocation counter (frame counter), commonly used |
| 1.0.99.98.0.255 | Event log (typical) |

**Solar PV inverter / DER note**: DLMS is overwhelmingly used on the *revenue meter*, not the inverter. Inverters typically speak SunSpec Modbus or IEEE 2030.5 (see Part C). For a prosumer, the canonical settlement quantities are the meter's import/export registers and load profile; inverter telemetry (DC/AC production) is a separate, lower-trust data stream.

**Manufacturer-specific OBIS**: vendors place proprietary diagnostics, tamper flags and configuration in C-codes (e.g. C.1.0 serial number, C.53.x tamper registers, 0.0.96.x.x manufacturer ranges). Handling: never hardcode — read the Association object_list (attribute 2) at association time to discover class_id + logical_name + access_rights, and maintain a per-vendor OBIS map keyed by manufacturer/FLAG ID and firmware version.

#### A4. xDLMS service layer and APDUs

- **Core LN services**: GET (read attributes), SET (write attributes), ACTION (invoke methods), EventNotification (server→client unsolicited), DataNotification (push). SN referencing uses READ/WRITE/UNCONFIRMED-WRITE. Clients always use LN referencing in modern deployments.
- **Service variants**: GET/SET-normal, with-list (multiple attributes in one APDU), and with-block / general-block-transfer (GBT) for payloads exceeding the negotiated max PDU size. The Green Book is explicit that once one party uses GBT, the other must continue with GBT to completion.
- **SELECTIVE_ACCESS** for Profile Generic: access-selector 1 = **range descriptor** (restricting_object = a capture object, usually Clock attr 2; from_value, to_value; optional selected_values columns); access-selector 2 = **entry descriptor** (from_entry, to_entry, from_selected_value, to_selected_value).
- **A-XDR / BER encoding**: ACSE APDUs (AARQ = APPLICATION 0 / 0x60, AARE, RLRQ = 0x62, RLRE = 0x63) are BER-encoded; the user-information field carries the xDLMS InitiateRequest/Response as an A-XDR OCTET STRING wrapped in BER. xDLMS data is A-XDR encoded. Key common data-type tags: 0 = null-data, 1 = array, 2 = structure, 3 = boolean, 4 = bit-string, 5 = double-long (int32), 6 = double-long-unsigned (uint32), 9 = octet-string, 10 = visible-string, 15 = integer (int8), 16 = long (int16), 17 = unsigned (uint8), 18 = long-unsigned (uint16), 22 = enum, 25 = date-time (Cosem-Date-Time = 12-byte octet string). The COSEM instance-id is a 6-byte octet string = the OBIS code without separators.
- **General APDU tags** (Green Book ASN.1): general-glo-ciphering [219], general-ded-ciphering [220], general-ciphering [221], general-signing [223], general-block-transfer [224]. Tags 230/231 reserved for DLMS Gateway.

#### A5. Application-layer associations and authentication

Authentication levels:
- **Lowest** (no authentication).
- **Low (LLS)**: shared password sent — in plaintext if no ciphering — making LLS a key downgrade risk.
- **High (HLS)**: 4-pass mutual challenge/response. The flow: client sends CtoS challenge in AARQ; server returns StoC in AARE; client processes f(StoC) and sends it via ACTION to `reply_to_HLS_authentication` (Association LN class 15, instance 0.0.40.0.0.255, method 1); server replies with f(CtoS). Challenge length is 8–64 octets for HLS-2..6, 32–64 for HLS-7.
- **HLS mechanism IDs**: HLS-2 (manufacturer-specific, commonly AES-128-ECB), HLS-3 (MD5, RFC 1321 — deprecated), HLS-4 (SHA-1 — deprecated), HLS-5 (GMAC), HLS-6 (SHA-256), HLS-7 (ECDSA).

#### A6. Security suites 0, 1, 2 and key management

| Suite | Auth-Enc | Signature | Key agreement | Hash | Key transport |
|---|---|---|---|---|---|
| 0 | AES-GCM-128 | — | — | — | AES-128 key wrap |
| 1 | AES-GCM-128 | ECDSA P-256 | ECDH P-256 | SHA-256 | AES-128 key wrap (+ optional V.44 compression) |
| 2 | AES-GCM-256 | ECDSA P-384 | ECDH P-384 | SHA-384 | AES-256 key wrap |

- **Security header**: ciphered xDLMS APDUs carry a Security Control (SC) byte + a 4-byte invocation counter (frame counter) + ciphertext + (for authentication) a 12-byte GCM tag. The SC byte bits select security_suite_id (bits 0–3) and Authentication / Encryption / key-set flags (bits 4–5 for authenticated-encryption, plus compression and broadcast-key bits). The GCM nonce/IV = 8-byte system-title ‖ 4-byte invocation counter.
- **glo_ / ded_ / general ciphering**: `glo_` APDUs use the global block-cipher key; `ded_` use a per-association dedicated key; general-glo/ded-ciphering and general-ciphering carry the system-title explicitly (needed for push and for unknown senders). general-signing carries an ECDSA signature using the signing (asymmetric) key — distinct from the symmetric block-cipher and authentication keys.
- **Key types**: Master Key / KEK (key-encrypting key, wraps new global keys), Global Authentication Key (GAK), Global/Block Encryption Key (GUEK), and (Suite 1/2) ECDSA signing key pairs + X.509 certificates. Key change uses the Security Setup object methods (key_transfer with RFC 3394 AES key wrap; key_agreement via ECDH). On any new key, the related invocation counter resets to 0.
- **Replay protection**: the receiver accepts a frame only if its invocation counter is strictly greater than the last seen; counters at/below expected are discarded. The public client can read the current invocation counter (commonly via a Data object near 0.0.43.1.0.255) before establishing a ciphered association.

**Known vulnerabilities (research, 2018–2025)**: academic and industry analyses (Eindhoven TU thesis; ValiDLMS framework; SciTePress 2023; CyTAL ProtoCrawler; Czech Decree 359/2020 testing methodology) document: HLS off-line dictionary attacks and server impersonation against HLS-3/4; responses not cryptographically bound to requests in some implementations; replay during HLS association if nonces are predictable; catastrophic GCM nonce/invocation-counter reuse; and parser-level memory-safety bugs (buffer/integer overflow, type confusion) in embedded DLMS servers. I did not find specific public CVE identifiers cataloged for the core DLMS/COSEM standard itself; the documented issues are predominantly implementation- and configuration-level rather than assigned CVEs — flag as a partial research gap.

#### A7. Transport and lower layers

- **HDLC profile (IEC 62056-46)**: byte-stuffed frames delimited by 0x7E flags; format/type+length; destination then source address; control byte; HCS then FCS (CRC-16). Addressing: client address (e.g. 0x10 management, 0x20 public) and server address split into upper HDLC (logical device) + lower HDLC (physical/multidrop). Connection: SNRM → UA (negotiating max info field sizes and window — commonly window 1, info field 128); data via I-frames with RR/RNR flow control; DISC to close. Each address can be 1/2/4 bytes.
- **DLMS over TCP/IP — Wrapper (IEC 62056-47 / 62056-9-7)**: the WPDU prepends an 8-byte header: version (2 bytes, = 0x0001) + source wPort (2) + destination wPort (2) + length (2), followed by the xDLMS APDU. wPorts mirror the HDLC client/server addresses. TCP port 4059 is the registered DLMS port. There is no HDLC framing/CRC in wrapper mode — TCP provides reliability.
- **UDP wrapper**: same WPDU used over UDP, typically for push/DataNotification where a session is not maintained.
- **Lower-layer profiles**: G3-PLC and PRIME (OFDM power-line carrier, used in European Linky/Iskraemeco deployments — Blue Book maps G3-PLC IB attributes to COSEM ICs), RF mesh (Wi-SUN), and cellular (NB-IoT / LTE-M / GPRS/4G) for the typical Thai AMI WAN. Optical probe (IEC 62056-21 → HDLC) is used for local commissioning.
- **Web Services (IEC TS 62056-9-1)**: a COSEM Access Service (CAS) exposing COSEM over SOAP/REST web services for cloud-native head-ends — relevant if GridTokenX ever consumes meter data via a utility's WS gateway rather than direct DLMS.

#### A8. Profile Generic deep dive

Profile Generic (class 7) is the time-series workhorse. Its `capture_objects` (attr 3) defines the columns (each = {class_id, logical_name, attribute_index, data_index}); `capture_period` (attr 4) is the interval in seconds (900 for 15-min); `sort_method` (attr 5, usually FIFO) and `sort_object` (attr 6, usually Clock attr 2) define ordering; `entries_in_use` (attr 7) and `profile_entries` (attr 8) give current/maximum row counts; the `buffer` (attr 2) holds the rows. Methods: reset, capture.

- **Sizing**: a 15-minute load profile = 96 entries/day per column. With Clock + import-power + export-power = 3 columns, a meter storing ~60 days ≈ 5,760 rows. Reads must be bounded by **selective access by range** (Clock from/to) to avoid pulling the whole buffer.
- **Field gotchas**: read `capture_objects` *before* reading the buffer so columns can be decoded; some meters require from/to times rounded to the hour; some return rows with timestamps `>` vs `==` the start time; large reads need block transfer (GBT or get-with-block) and can throw buffer-overrun errors on constrained meters.

### PART B — INTEGRATION: IoT/Edge → Chain-Bridge → On-Chain Attestation

#### B9. Edge gateway / aggregator-bridge architecture for DLMS ingestion

**Rust client libraries**: the `dlms_cosem` crate on crates.io/docs.rs is a `no_std` *parser* for DLMS/COSEM messages — useful but not a full stack (no association management, limited ciphering). There is no mature, full-featured pure-Rust DLMS client equivalent to Gurux. The most mature options are **Gurux** (Java, .NET, ANSI C, C++, Python — actively maintained, GXDLMSDirector UI), the Python **dlms-cosem** library by Utilitarian (u9n) (sans-IO design, HDLC + TCP, GlobalCiphering, HLS method-2; licensed under BUSL-1.1 transitioning to Apache-2.0), the EPRI C++ DLMS-COSEM library, jDLMS (Java), and a pure-Dart `dlms` package. **Recommendation for GridTokenX**: because the platform's chain-bridge is Rust, either (a) FFI-wrap Gurux.DLMS.c (ANSI C, permissive, battle-tested) behind a safe Rust crate, or (b) run a sidecar in Python (u9n dlms-cosem) or Java (Gurux) that speaks DLMS and emits normalized messages onto the bus. A from-scratch pure-Rust stack is a multi-month effort and a research gap worth scoping.
- **Edge gateway pattern**: meter → DLMS client (association + GET/selective-access or DataNotification listener) → normalization → message bus (NATS JetStream / MQTT / Kafka) → aggregator-bridge → chain-bridge.
- **Connection management**: pool and reuse associations (association setup is expensive over cellular); apply exponential backoff with jitter on NB-IoT/LTE-M; persist the last invocation counter so ciphered sessions resume without replay rejection.
- **Time**: the Clock object (0.0.1.0.0.255) is the meter's time authority for profile timestamps. Do not silently rewrite profile timestamps to gateway/NTP time — record both meter-clock and gateway-NTP time and the offset; treat the meter clock as the canonical settlement timestamp but flag drift.
- **Read strategy**: buffered selective-access reads (by range) for settlement-grade interval data; DataNotification push for low-latency events; avoid high-frequency real-time polling for billing.
- **Concentrators**: multiple meters behind one IP are addressed by upper/lower HDLC server addresses or DLMS Gateway addressing; the gateway must demultiplex by server address and serial number.

#### B10. Schema mapping: DLMS → canonical schema → on-chain attestation

Map each COSEM reading to a canonical protobuf/Avro record preserving: OBIS code, class_id, attribute_index, raw value, **scaler_unit** (so kWh scaling is never lost), timestamp (meter-clock), status/quality flags, meter serial/system-title, invocation counter, and a chain-of-custody envelope (gateway id, gateway signature, ingest time).

- **GridTokenX dual-token mapping**: net imported energy and exported energy are derived from the import (1.0.1.8.0) / export (1.0.2.8.0) registers or the signed load-profile deltas; exported kWh drive settlement/mint events for the GRID token, while consumption maps to the utility/settlement token. **Settlement period decision**: align the on-chain settlement window to the meter's native 15-minute interval (PEA/EDMI deliver 15-minute data), aggregating intervals into the chosen billing/trade period rather than minting per-interval.
- **Tariff handling**: for TOU settlement, read per-tariff registers (E-group 1–4) and the Activity Calendar, not just the total register, so trades price against the correct tariff window.

#### B11. End-to-end cryptographic provenance (the oracle integrity problem)

- **Root of trust**: under Suite 1/2 the meter signs/authenticates its APDUs (system-title + invocation counter + GCM tag, or ECDSA general-signing). This proves *meter → gateway* integrity within the *utility* PKI.
- **The trust-domain gap**: DLMS system-titles and keys are provisioned and held by the utility (e.g. Landis+Gyr Gridstream issues master keys from a production system to the head-end). A blockchain settlement layer is not part of that PKI, so a DLMS signature is not directly verifiable on-chain, and the platform usually cannot extract the meter's private key. **Therefore DLMS alone is insufficient** — the edge must re-attest into the blockchain trust domain.
- **Re-signing pattern**: an edge secure element (Microchip ATECC608 or NXP SE050/A5000 — the latter supports P-256 and P-384, ECDSA/ECDH/SHA, RFC 3394 key unwrap, CC EAL6+) holds a gateway key whose public key is registered on-chain. The gateway verifies the DLMS-layer integrity, then signs the canonical record (or its hash) with the SE key, producing an on-chain-verifiable attestation.
- **Batch attestation**: hash each 15-minute reading, build a Merkle tree over a settlement window, and post only the Merkle root on-chain with per-reading proofs available off-chain (the established tamper-evident pattern: hash off-chain data, anchor root on-chain; cf. Ubirch UPP/Merkle anchoring and the energy-settlement second-tier blockchain literature). This bounds on-chain cost while preserving per-interval verifiability.
- **Dual verification (third leg)**: crosscheck the edge attestation against a **Switchboard TEE attestation** so that two independent roots (edge SE + TEE oracle) must agree before settlement — this is the dual-verification recommendation already in GridTokenX's architecture and directly mitigates a single-gateway compromise.
- **Approach comparison**: per-reading on-chain signatures (highest integrity, highest cost/throughput burden — and SHA-256/ECDSA are heavy on constrained MCUs); windowed Merkle batch (efficient, recommended); zk-proofs of correct aggregation (strongest privacy + succinct verification, but the highest engineering complexity and a genuine research gap for GridTokenX).

#### B12. Integration with the chain-bridge (Rust) service

- **Placement**: DLMS parsing belongs in a dedicated `dlms-gateway` (edge or regional), **not** inside the chain-bridge. The chain-bridge should receive already-normalized, already-attested canonical records over gRPC / NATS JetStream and remain protocol-agnostic.
- **Trust-domain bridging**: DLMS security keys (utility domain) and Vault Transit keyless signing (platform domain, for Solana tx signing) are deliberately separate. The bridge is the edge SE attestation: DLMS verifies meter→gateway; the SE/Vault chain verifies gateway→chain. Vault Transit should never hold DLMS keys, and DLMS keys should never sign Solana transactions.
- **Policy engine**: the chain-bridge's instruction-level transaction policy engine should validate DLMS-sourced data before signing — checks: monotonic invocation counter, monotonic energy registers (no negative deltas unless export), scaler/unit sanity, meter-clock-vs-platform drift within tolerance, attestation signature validity, and TEE crosscheck agreement. Only then does it authorize the mint/settlement instruction.
- **Audit log**: keep an append-only, hash-chained, tamper-evident log of raw DLMS APDU traces (ciphered + decoded) with timestamps and gateway signatures, for dispute resolution and regulator audit.
- **Testing**: use LiteSVM simnet to test the full DLMS→canonical→attestation→Solana pipeline with recorded/replayed APDU fixtures and a DLMS server simulator (Gurux server examples), validating policy-engine rejection paths (replayed counters, drifted clocks, bad attestations).

#### B13. NILM and forecasting pipelines

- DLMS load-profile data (15-min, or 1-min on capable meters) feeds the Dual-Target LightGBM forecaster and the NILM Sparse MoE model as low-frequency time series. The NILM literature confirms a steady shift to "very-low-rate" disaggregation at 15–60 min resolution, but accuracy is limited at these rates (indistinct ON/OFF transitions, overlapping appliances).
- **Hard limit**: utility DLMS meters cap at 1-min or 15-min; true appliance-signature NILM needs kHz sampling. Per Kelly & Knottenbelt (Scientific Data 2:150007, Nature, 2015; arXiv:1404.0284), the UK-DALE dataset records "Domestic Appliance-Level Electricity at a sample rate of 16 kHz for the whole-house and at 1/6 Hz for individual appliances" across five houses — producing GBs/day, impractical over DLMS/cellular. **Bridge**: use DLMS data for billing-grade aggregate load and forecasting; deploy separate high-frequency NILM sensors behind the meter for appliance disaggregation, fusing the two streams (DLMS as ground-truth energy totals, NILM sensors for decomposition).

### PART C — COMPARATIVE AND STRATEGIC

#### C16. DLMS/COSEM vs alternative protocols

- **DLMS/COSEM**: revenue/billing meters; secure, object-oriented, utility-standard; the right choice for the *settlement meter*.
- **Modbus RTU/TCP**: simple register map, ubiquitous on industrial devices and inverters; no built-in security; good for local telemetry, not billing trust.
- **SunSpec Modbus**: standardized Modbus register models for inverters/storage/DER; semantically aligned with IEEE 2030.5; "behind-the-meter" local comms; historically no over-the-wire security.
- **IEEE 2030.5 (SEP 2)**: IP/REST/TLS with X.509 certificate auth; designed for utility↔DER WAN comms, demand response, the Common Smart Inverter Profile (CA Rule 21 / UL 1741 SB).
- **IEC 61850(-90-10)**: substation/DER automation, GOOSE/MMS; heavy, for grid-edge automation not consumer metering.
- **OpenADR**: demand-response signaling, not metering.
- **MQTT Sparkplug B**: lightweight IIoT pub/sub transport/payload spec; a good *internal bus* choice, not a meter protocol.
- **When to use which**: DLMS for the prosumer settlement meter (and Thai AMI reality); SunSpec Modbus or IEEE 2030.5 for the solar inverter/battery telemetry and control; IEC 61850 only if integrating with substation automation. DLMS UA and IEEE have a liaison relationship and a DLMS↔CIM (IEC 61968-9) mapping exists (IEC 62056-6-9).

#### C17. Open-source tooling landscape (2025-2026)

- **Gurux suite** (Java/.NET/ANSI C/C++/Python): the de-facto open-source DLMS stack; includes GXDLMSDirector (client UI), server/simulator examples, a push listener, and an online APDU translator. The most production-proven option.
- **u9n `dlms-cosem`** (Python): clean sans-IO design, HDLC + TCP, GlobalCiphering, HLS-2; BUSL-1.1 license (→ Apache-2.0). Good reference and sidecar candidate.
- **Rust `dlms_cosem`**: `no_std` parser only — immature for a full client.
- **EPRI DLMS-COSEM** (C++), **jDLMS** (Java), pure-Dart `dlms`: additional implementations.
- **OSGP / Open Smart Grid Platform**: open platform with DLMS support for head-end-style integration.
- **Wireshark DLMS dissector** (e.g. bearxiong99/wireshark-dlms): essential for APDU/HDLC/wrapper traffic analysis and debugging.
- **Simulators / conformance**: the DLMS UA Conformance Test Tool (CTT v3.x) and IDIS iDTT/iCTT3 (DNV-accredited) for certification; Gurux server examples and the ASE62056 Test Set for development without physical meters. (Note: a fully featured open-source meter *simulator* generating push messages is a known gap — Gurux historically lacked a push-generating server simulator.)

#### C14/C18. Thailand context and GridTokenX-specific recommendations

**Thai AMI reality**: Per Itron's June 19, 2018 announcement, PEA — with consortium partner ALT Telecom Public Company Limited — deployed 116,000 Itron OpenWay Riva meters in Pattaya as a national pilot (with Itron Enterprise Edition MDM; AMI project manager Pongsakorn Yuthagovit), and per Smart Energy International / Pimagazine Asia "PEA…supplies electricity to 20.5 million households across the country, except in Bangkok and other central provinces," with the national rollout to scale to "around 1 million meters per year." PEA has installed 300,000+ smart meters and proposes a one-million-meter national plan; EDMI supplies rural metering delivering 15-minute interval data every 15 minutes; Trilliant/Samart (STS Consortium) and Landis+Gyr/Iskraemeco are also active. These are DLMS/COSEM, frequently IDIS-aligned (the IDIS Association merged into the DLMS UA; IDIS Package 3 certification runs through the DLMS UA via DNV's accredited lab). Thai utility tenders typically reference a DLMS conformance certificate plus an IDIS/companion-spec conformance block. MEA (Bangkok metro) and EGAT (generation/transmission, smart-grid pilots) complete the trio.

**Thai regulatory frame**: P2P energy trading in Thailand is permitted only inside the **ERC Sandbox**. Per Nikrawesh et al., *Energies* 15(3):1229 (MDPI, 2022), Thailand's ERC "launched the ERC sandbox program in 2019…From a total of 34 projects approved by the program, 8 projects were based on the assessment of the P2P energy trading model," constrained by Thailand's "single-buyer model." The landmark blockchain P2P pilot was the **T77 precinct in Bangkok** (Sansiri/BCPG/Power Ledger, launched August 2018): per Power Ledger's case study, "up to 635KW of BCPG solar PV" was deployed "across four participating entities" — Habito shopping mall, Bangkok International Preparatory & Secondary School, Park Court Serviced Apartments and Dental Hospital Bangkok — via "18 meter points" with data "provided in 15-minute intervals," transacted "across the meter" with Metropolitan Electricity Authority (MEA) network access (The Nation reports the per-building split as 54 kW Habito / 413 kW Bangkok Prep / 168 kW Park Court). Rooftop solar is compensated under a **net billing** scheme: per Zero Carbon Analytics (Mar 2026), "The net billing rate increased to THB 2.2 per kWh from 2021 to 2024, although the average retail rate remained higher at THB 4.18 per kWh," and the residential scheme's 90 MW quota (2021–2030) "was reached in 2024" — the Bangkok Post notes ">10,000 households applied, with approved capacity reaching 89.8MW…forcing authorities to close applications by September 2024." Full net metering remains "under consideration." A March 2026 Royal Gazette tax deduction (up to 200,000 THB) supports ≤10 kWp residential systems. SEC Thailand has (2024–2025) amended digital-asset rules to permit tokenized RECs/carbon credits as utility tokens under the Emergency Decree on Digital Asset Businesses B.E. 2561 (2018), distinguishing Group-1 (exempt if not exchange-traded) from Group-2 (SEC approval + ICO portal + disclosure). No explicit chain-of-custody/audit-trail mandate for *metered data* was found — a regulatory gap GridTokenX should monitor. Separately, the ERC unveiled a draft Direct PPA regulation on October 3, 2025 allowing qualified users up to 2,000 MW via Third Party Access — a potential future expansion path beyond the sandbox.

**Koh Tao pilot context**: Koh Tao was historically an **isolated 24/7 diesel microgrid** operated by PEA (1×6 MW diesel engine generator, 33 kV system, >4 million litres of fuel/year in 2009), ~72 km from Chumphon. PEA has since funded a **33 kV submarine cable** (≈45 km from Koh Pha-ngan, ≈1.7 billion THB, with Interlink/Hengtong), and EGAT's larger 230 kV Koh Samui submarine project (two circuits, ~50 km, ~400 MW total; construction 2026, circuits 2028–2029) explicitly targets stability for Koh Samui/Koh Pha-ngan/Koh Tao. Comparable PEA/island RE projects: the off-grid **Koh Jik** microgrid (72 kWp PV + 266 kWh Li-ion battery, ~95% solar share, ~100 households — community-operated, *not* PEA grid-connected), PEA's **Koh Samui** BESS (one of Thailand's first large-scale, MoU with Nuovo Plus June 2024, capacity undisclosed) and **Koh Paluay** microgrid (Surat Thani), and **Koh Lan** (Chonburi). Islanded-grid logic (frequency/voltage stability, Disconnect Control, BESS coordination) must remain a first-class GridTokenX design constraint even though the cable now backstops the island.

**GridTokenX-specific recommendations:**
1. **Component placement**: build a dedicated **`dlms-gateway` microservice** (edge or per-island concentrator) that owns DLMS associations, ciphering, selective-access reads and push listening. The existing **aggregator-bridge** consumes normalized+attested records; the **chain-bridge** stays protocol-agnostic and enforces policy + signs Solana tx via Vault Transit. Do **not** put DLMS parsing in the chain-bridge.
2. **OBIS subset for Koh Tao prosumer meters**: 1.0.1.8.0.255 (import), 1.0.2.8.0.255 (export), 1.0.1.7.0.255 / 1.0.2.7.0.255 (instantaneous import/export power), per-phase V/I (1.0.32/52/72.7.0, 1.0.31/51/71.7.0), 1.0.14.7.0 (frequency — important on an islanded grid), 1.0.99.1.0.255 (15-min load profile, capturing Clock + import + export columns), 0.0.1.0.0.255 (clock), 0.0.96.1.0.255 (serial), 0.0.43.x (security setup + invocation counter), and the TOU tariff registers (1.0.1.8.1–4 / 1.0.2.8.1–4) if net billing/TOU applies.
3. **Security**: require **Security Suite 1 minimum** (Suite 2 where meters expose P-384), authenticate with **HLS-5 (GMAC)** or **HLS-7 (ECDSA)**; forbid LLS and HLS-3/4; enforce strict invocation-counter monotonicity and persistence; manage keys via the Security Setup object with RFC 3394 key wrap.
4. **Attestation**: **per-interval signature + windowed Merkle batch (per settlement period) + Switchboard TEE crosscheck**, with edge re-signing via ATECC608/SE050 whose public key is on-chain; settle on the meter's native 15-minute boundary.
5. **Audit & test**: append-only hash-chained APDU audit log; LiteSVM simnet tests driven by recorded APDU fixtures and a Gurux server simulator, exercising policy-engine rejection paths.

**Open research gaps for Chanthawat to investigate:**
- A production-grade **pure-Rust DLMS client** (or a safe FFI wrapper around Gurux.DLMS.c) — none currently mature.
- **zk-proofs of aggregation** for 15-min interval batches (succinct on-chain verification of correct summation/settlement).
- Confirming the **exact companion/conformance block** (IDIS package, security suite, HLS level) in current PEA/MEA meter tenders and whether **island/remote AMI** (incl. Koh Tao) is covered — not confirmed in public sources.
- Whether ERC/SEC will impose **chain-of-custody/audit requirements** on tokenized metered energy — currently unregulated.
- Reconciling DLMS settlement timestamps with **DST** — simplified in Thailand, which does **not** observe DST, removing a major TOU-rollover failure mode.

## Recommendations
1. **Now (design)**: stand up the `dlms-gateway` microservice with a Gurux-C FFI or Python (u9n) sidecar; implement Suite 1 + HLS-5/7; define the canonical schema preserving OBIS/scaler-unit/timestamp/status/system-title/invocation-counter. Benchmark to advance: successful ciphered association + selective-access 15-min read from a representative Itron/EDMI/Landis+Gyr meter or simulator.
2. **Next (attestation)**: integrate ATECC608/SE050 re-signing + Merkle batching + Switchboard TEE crosscheck; wire the chain-bridge policy engine validation gates. Benchmark: end-to-end LiteSVM test passes including rejection of replayed counters and drifted clocks.
3. **Pilot (Koh Tao)**: deploy against real prosumer meters with islanded-grid frequency monitoring and Disconnect Control handling; operate within the ERC Sandbox and net-billing constraints. Threshold to change approach: if meters cap at 15-min and NILM accuracy is insufficient, add behind-meter high-frequency sensors.
4. **Watch items**: ERC Direct PPA / net-metering evolution (the Oct 2025 draft Direct PPA / 2,000 MW TPA framework); SEC token classification (Group 1 vs 2); island AMI coverage confirmation. A move from net billing to full net metering or a Direct-PPA TPA framework would materially expand GridTokenX's addressable settlement logic.

## Caveats
- DLMS UA "colored books" are paywalled; precise current edition numbers and byte-level details here are drawn from secondary sources (Gurux, icube.ch, vendor docs, academic papers, Wireshark dissector, ASN.1 excerpts) and should be confirmed against the purchased Blue/Green Books before implementation.
- No specific CVE identifiers for the core standard were located; documented vulnerabilities are implementation/configuration-level. Any specific DLMS UA certification-count figure should be treated as unverified.
- Thai net-metering rate claims vary across lower-quality sources; the net-billing 2.20 THB/kWh figure (and ~89.8 MW/2024 quota closure) are corroborated by Bangkok Post, BloombergNEF and Zero Carbon Analytics, whereas "Net Metering Act 2024" framing is unreliable.
- Island/remote AMI coverage (including Koh Tao) and the exact conformance block in Thai tenders are not publicly confirmed.
- "Thailand Micro grid pilot" is treated as a GridTokenX design premise The T77 pilot's participant count (4 vs later 7) and battery storage (press "co-located storage" vs GO-P2P "0 kWh as built") differ across sources, reflecting project expansion over time.
