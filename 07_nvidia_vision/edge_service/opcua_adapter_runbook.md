# FC01 Revision-E OPC UA adapter execution runbook

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

## Delivered boundary

The adapter is a non-safety OPC UA client. The Siemens PLC remains authoritative for machine state, permissives, motion, timing, result correlation and product disposition. The adapter cannot command motion or bypass PLC interlocks. The delivered entry point contains no production inference backend and therefore remains not ready by design.

Local integration evidence uses asyncua 2.0.1, an ephemeral test CA, Basic256Sha256/SignAndEncrypt, a named X.509 user and a real in-process OPC UA server/client. It is not evidence of a configured S7-1500 endpoint, site PKI, production network, camera, model or target Jetson runtime.

## Controlled software installation

1. Create an isolated Python 3.12 environment outside the release tree.
2. Populate a controlled wheelhouse from the versions in `requirements-opcua.txt`; record every downloaded filename and SHA-256 in the site deployment record.
3. Install from the approved wheelhouse with dependency resolution disabled after the complete locked set has been reviewed.
4. Run `python -m pip check` and retain the result.
5. Do not create a virtual environment, cache, log, certificate or private key inside the controlled Git checkout.

The Revision-E test environment used Python 3.12.13 and asyncua 2.0.1. The dependency set is source-controlled, but the target Linux/Jetson environment remains unbuilt and unqualified.

## PKI and identity provisioning

Provision the seven paths named in `opcua_runtime_config.json` through service environment variables. Private keys must be readable only by the dedicated `fc01-vision` account. Do not store keys or site certificates in Git.

- Issue the application and user certificates from the approved site CA.
- Include the exact application URI `urn:fc01:vision-edge:client` in the application certificate URI SAN.
- Configure the PLC server for Basic256Sha256/SignAndEncrypt only, unless the site security authority formally selects a stronger mutually supported policy.
- Disable anonymous user tokens.
- Trust the named edge certificate/user in the TIA project and restrict that user to read PLC-owned nodes and write only NVIDIA-owned nodes.
- Export and pin the exact PLC server certificate; populate the trusted-CA and CRL directories.
- Record issuer, subject, serial, validity, thumbprint, URI SAN, responsible owner and renewal/revocation procedure.

The adapter rejects missing paths, an untrusted/revoked server, a URI mismatch, wrong node types, duplicate/missing NodeIds, write access to PLC-owned nodes or missing write access to NVIDIA-owned nodes.

## Siemens request handshake

Revision-E source implements the preferred transport contract: `FB_VisionInterface` holds `INSPECTION_TRIGGER` high with a stable payload and ID until coherent `VISION_BUSY` observation or a terminal result. `FB_CellMain` prevents a repeated upstream pulse from allocating a different ID while the interface is pending. This closes the one-scan source-design defect, but it is not native evidence.

Import and compile the Revision-E SCL in TIA Portal, then measure the actual S7 OPC UA sampling/publish behavior. Confirm that the edge sees the held request, raises BUSY, the PLC deasserts Trigger only after that observation, and the transaction ID never changes while pending. Revision E's adapter fails closed if it observes an advanced inspection ID without a sampled request level; do not weaken that diagnostic to conceal a native configuration error.

## Local verification

From the repository root, using the isolated environment:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest discover -s 07_nvidia_vision\edge_service\tests -p 'test_*.py' -v
python -m unittest discover -s 07_nvidia_vision -p 'test_plc_interface_harness.py' -v
python -m pip check
```

The integration tests use temporary directories and delete their ephemeral keys/certificates on completion. Test certificates must never be copied into a production trust store.

## Target deployment and commissioning

1. Install source and the reviewed environment under `/opt/fc01-vision-edge`. Install both `opcua_runtime_config.json` and its referenced `service_config.json` together under `/etc/fc01-vision-edge`; install PKI only at externally provisioned service-environment paths.
2. Create the locked, non-login `fc01-vision` account and external state/log directories.
3. Review the provided systemd hardening directives against the chosen camera/GPU runtime; relax a directive only through a recorded cybersecurity change.
4. Configure the firewall so the edge initiates OPC UA TCP 4840 only to PLC-A100. Keep `/healthz`, `/readyz` and `/metrics` loopback-only unless an authenticated site monitoring conduit is approved.
5. Start with machine production disabled. Confirm READY remains low while `VISION_ENABLE` is high and while no controlled model exists.
6. Verify all 27 resolved NodeIds, types, directions, user access levels and TIA server namespace/export evidence.
7. Execute disconnect, PLC restart, edge restart, certificate expiry/revocation, stale heartbeat, wrong ACK, duplicate ID, session regression, timeout and retained-publication tests.
8. Confirm payload nodes are written before `RESULT_VALID`, remain immutable until exact ACK and are never reused across sessions.
9. Retain structured logs, metrics, TIA diagnostics, packet-free security evidence, software hashes and test records.

## Offline and reconnect disposition

- Do not queue requests, camera images or unpublished results while the PLC connection is unavailable. There is no replay queue for later product disposition.
- The sole retained transaction is one immutable result already published on the OPC UA server and waiting for the exact same-session acknowledgement. Do not overwrite or infer acknowledgement from a timeout.
- On disconnect, ambiguous write/read completion, heartbeat loss or incoherent counter snapshot, force READY low. The PLC must deterministically HOLD the affected product.
- Reconnect only through disabled-state synchronization. Reconcile `VISION_SESSION_EPOCH`, `INSPECTION_ID`, `RESULT_ACK_ID` and `PLC_HEARTBEAT` as one coherent snapshot before READY may return.
- Never apply a buffered image or result to a different bottle, inspection ID or controller/edge session. An uncompleted online transaction requires explicit operator disposition under the PLC-owned workflow.

## Controlled adapter rollback

1. Record the rollback request, responsible approver, affected software/config/model identifiers and reason. Model rollback remains a separate blocked workflow until a controlled model exists.
2. Disable production, verify the PLC is holding product safely and stop `fc01-vision-edge.service`.
3. Preserve the current logs, metrics, package hashes, configuration hash and service-unit hash for the incident record.
4. Restore the previously reviewed versioned adapter package, complete locked requirements set, `opcua_runtime_config.json`, `service_config.json` and systemd unit as one controlled release. Do not mix versions.
5. Verify every restored file hash, ownership and least-privilege permission. Revalidate application/user certificate identity, trust/CRL paths and the pinned PLC server certificate.
6. Cold-start with production disabled and READY low. Resolve and validate all 27 NodeIds, data types, directions and access rights before enabling readiness.
7. Repeat heartbeat-loss, disconnect/reconnect, stale/future/duplicate ID, session regression, wrong acknowledgement, immutable-publication and malformed-data negative tests.
8. Obtain the required site cybersecurity/operations approval, record the evidence and only then return the edge subsystem to the PLC-controlled enable sequence. No automatic production restart is permitted.

Production commissioning remains blocked until the source-designed handshake is natively compiled and exercised against a real S7 endpoint, and until site PKI, target edge hardware/runtime and a controlled inference backend are available. No model accuracy, latency or production OPC UA acceptance result is claimed.
