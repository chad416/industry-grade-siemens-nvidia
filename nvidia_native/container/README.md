# Container build and rollback boundary

> FICTIONAL ENGINEERING PROJECT - NOT FOR CONSTRUCTION.

> CONCEPTUAL SAFETY ARCHITECTURE - REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE/UKCA CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

No container was built in Revision G. From the repository root, after selecting an official compatible DeepStream image by immutable digest and approving network/package access, run:

`docker build --file nvidia_native/container/Dockerfile --build-arg BASE_IMAGE=<approved-registry/image@sha256:digest> --tag fc01-edge:<approved-version> .`

The adjacent `Dockerfile.dockerignore` limits the repository-root build context. Record the base digest, requirements hash, build command, image digest, SBOM and vulnerability report. Do not tag `latest`. Deploy by immutable image digest; rollback by restoring the last approved configuration/model/container tuple. Mount the runtime OPC UA configuration and certificates read-only, and provide writable log/audit paths explicitly. The service has no model backend and must remain not-ready until a separately approved production adapter is injected.
