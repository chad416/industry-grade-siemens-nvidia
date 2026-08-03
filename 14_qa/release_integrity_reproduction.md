# Published Revision-D release-integrity reproduction

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

A fresh GitHub clone of commit `f1e34bd15b29ecd2fc6a8f0110861a721ee5b9d1` produced `PASS=396 FAIL=1`; the failed check was the historical QElectroTech baseline hash. The pristine manifest reported 243 listed and 243 actual controlled files with four discrepancies: QET size/hash and DXF size/hash.

The published QET blob was 870,838 bytes with SHA-256 `f7698afa0439e5f7defb23fb5a4fdc5071f9b59f68a7b4e6c2c75626ef4ffdec`; its verified original CRLF native file is 875,734 bytes with SHA-256 `d817036497afbf0f48379da4dbce81cd1d7b7cca28bfc8341d5b437d2421660b`. Adding one CR before each of 4,896 LF bytes reproduces the controlled hash exactly. The published DXF blob was 11,893 bytes with SHA-256 `d8e9ea765d9efc1871b24cd07243ac54e0f729d90c05753b18f5be756a28d875`; its verified original CRLF file is 15,277 bytes with SHA-256 `9ddd38069e43c74c92393bf7f2d3dda729dfce041cedcd16fcdfca0dd433828d`, exactly accounting for 3,384 CR bytes.

Root cause: Git normalized the pre-existing files to LF before Revision C later added `* -text`; they were never re-added, while the OneDrive working copies remained CRLF and supplied the manifest/hard-coded hashes. D.1 treats QET/DXF/native exchange artifacts as byte-exact, recommits the verified CRLF originals, normalizes ordinary text to LF, builds manifests from the staged index and verifies final manifests against `HEAD`.

The contaminated OneDrive checkout contained exactly twelve untracked Revision-C files. Every one matched its recoverable Revision-C Git blob. D.1 denies their exact paths and its preflight runs before any generator removal, preventing cleanup from hiding contamination.
