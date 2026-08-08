# Build requires an explicitly approved immutable DeepStream base digest.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}
ARG BASE_IMAGE
ARG APP_UID=10001
RUN test -n "${BASE_IMAGE}" && useradd --uid ${APP_UID} --create-home --shell /usr/sbin/nologin fc01edge
WORKDIR /opt/fc01
COPY 07_nvidia_vision/edge_service/requirements-opcua.txt /tmp/requirements-opcua.txt
RUN python3 -m pip install --no-cache-dir -r /tmp/requirements-opcua.txt
COPY 07_nvidia_vision/edge_service /opt/fc01/edge_service
USER fc01edge
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENTRYPOINT ["python3", "/opt/fc01/edge_service/main.py"]
CMD ["--config", "/run/fc01/opcua_runtime_config.json"]
