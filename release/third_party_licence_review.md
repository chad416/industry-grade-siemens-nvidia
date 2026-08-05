# Third-party software inventory boundary - Revision F

The controlled Python runtime inventory is derived from the locked OPC UA requirements and installed package metadata. It supports engineering review but is not legal advice, a vulnerability scan or production-distribution approval.

Before production deployment, the named owner must:

1. resolve the missing `aiosqlite` licence declaration from the authoritative upstream distribution;
2. review the dual licence terms recorded for `python-dateutil`;
3. collect complete licence texts and notices for the approved container/image;
4. run an approved software-composition and vulnerability scan against the exact target digest;
5. document remediation, exceptions, support period and update owner.

CUDA, TensorRT, DeepStream, TAO, JetPack, camera SDKs and model licences are excluded because none is installed, selected or distributed by this revision.
