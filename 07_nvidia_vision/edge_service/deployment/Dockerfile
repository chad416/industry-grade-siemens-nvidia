FROM python:3.12-slim

ARG APP_UID=10501
ARG APP_GID=10501
RUN groupadd --gid ${APP_GID} fc01-vision \
    && useradd --uid ${APP_UID} --gid ${APP_GID} --no-create-home --shell /usr/sbin/nologin fc01-vision

WORKDIR /opt/fc01-vision-edge
COPY requirements-opcua.txt ./
RUN python -m pip install --no-cache-dir --disable-pip-version-check -r requirements-opcua.txt \
    && python -m pip check
COPY *.py *.json ./

USER fc01-vision:fc01-vision
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "main.py"]
CMD ["--config", "/etc/fc01-vision-edge/opcua_runtime_config.json"]

# Build/runtime validation is BLOCKED until a controlled Linux/Jetson container
# host is available. Site deployment must pin the reviewed base-image digest,
# mount config/PKI read-only, provide external log/state paths and apply the
# systemd/firewall controls in the runbook. No GPU/model is included.
