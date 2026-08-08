# NVIDIA native execution report

> FICTIONAL ENGINEERING PROJECT - NOT FOR CONSTRUCTION.

> CONCEPTUAL SAFETY ARCHITECTURE - REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE/UKCA CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

The local RTX 5060 driver query executed successfully. CUDA toolkit (`nvcc`), Docker, NVIDIA Container Toolkit, TAO, TensorRT, DeepStream, OpenUSD and Omniverse were not found. No cloud GPU resource exists. The deterministic synthetic smoke exercises the existing acquisition/preprocess/mock boundary and proves the mock backend is refused by `VisionService`; it does not decode representative images, train a model, create ONNX/TensorRT artifacts, measure latency or validate production OPC UA.

Current official planning baseline is DeepStream 9.1 on Ubuntu 24.04; dGPU prerequisites include driver 595.58.03, CUDA 13.2 and TensorRT 10.16.0.72. TAO-trained engines must be regenerated for their exact TensorRT/CUDA/hardware environment. Sources: https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Installation.html and https://docs.nvidia.com/tao/tao-toolkit/latest/text/ds_tao/deepstream_tao_integration.html.
