"""Dependency-free structured logging, metrics and local health endpoints."""
from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable


class JsonFormatter(logging.Formatter):
    """One bounded JSON object per line; no credentials or payload images."""

    def format(self, record: logging.LogRecord) -> str:
        document = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in (
            "event", "diagnostic_code", "session_epoch", "inspection_id",
            "plc_heartbeat", "attempt", "duration_ms",
        ):
            value = getattr(record, key, None)
            if value is not None:
                document[key] = value
        if record.exc_info:
            document["exception"] = self.formatException(record.exc_info)
        return json.dumps(document, ensure_ascii=True, separators=(",", ":"))


def configure_logging(*, level: str = "INFO", file_path: str | None = None,
                      max_bytes: int = 10_000_000, backup_count: int = 5) -> logging.Logger:
    logger = logging.getLogger("fc01.vision.edge")
    logger.handlers.clear()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False
    formatter = JsonFormatter()

    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    logger.addHandler(stream)
    if file_path:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger


class Metrics:
    """Fixed-name counters and gauges rendered in Prometheus text format."""

    PREFIX = "fc01_vision_edge_"

    def __init__(self) -> None:
        self._counters: dict[str, int] = defaultdict(int)
        self._gauges: dict[str, int | float] = {}

    @staticmethod
    def _valid_name(name: str) -> bool:
        return bool(name) and all(char.islower() or char.isdigit() or char == "_" for char in name)

    def increment(self, name: str, amount: int = 1) -> None:
        if not self._valid_name(name) or type(amount) is not int or amount < 0:
            raise ValueError("metric counter name or increment is invalid")
        self._counters[name] += amount

    def gauge(self, name: str, value: int | float | bool) -> None:
        if not self._valid_name(name) or type(value) not in {int, float, bool}:
            raise ValueError("metric gauge name or value is invalid")
        self._gauges[name] = int(value) if type(value) is bool else value

    def render(self) -> bytes:
        lines: list[str] = []
        for name in sorted(self._counters):
            full = self.PREFIX + name
            lines.extend((f"# TYPE {full} counter", f"{full} {self._counters[name]}"))
        for name in sorted(self._gauges):
            full = self.PREFIX + name
            lines.extend((f"# TYPE {full} gauge", f"{full} {self._gauges[name]}"))
        return ("\n".join(lines) + "\n").encode("ascii")


@dataclass(frozen=True)
class HealthSnapshot:
    alive: bool
    connected: bool
    ready: bool
    busy: bool
    result_valid: bool
    session_epoch: int
    diagnostic_code: str

    def json_bytes(self) -> bytes:
        return (json.dumps(self.__dict__, ensure_ascii=True, separators=(",", ":")) + "\n").encode("ascii")


class HealthServer:
    """Loopback-only HTTP/1.1 health service with a deliberately tiny surface."""

    def __init__(self, host: str, port: int, snapshot: Callable[[], HealthSnapshot],
                 metrics: Metrics, request_timeout_s: float = 1.0) -> None:
        if host not in {"127.0.0.1", "::1", "localhost"}:
            raise ValueError("health endpoint must bind to loopback")
        if type(port) is not int or not 0 <= port <= 65535:
            raise ValueError("health port is invalid")
        self.host = host
        self.port = port
        self.snapshot = snapshot
        self.metrics = metrics
        self.request_timeout_s = request_timeout_s
        self._server: asyncio.AbstractServer | None = None

    @property
    def bound_port(self) -> int | None:
        if self._server is None or not self._server.sockets:
            return None
        return int(self._server.sockets[0].getsockname()[1])

    async def start(self) -> None:
        self._server = await asyncio.start_server(self._handle, self.host, self.port)

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        status = 400
        content_type = "application/json"
        body = b'{"error":"bad request"}\n'
        try:
            request = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), self.request_timeout_s)
            if len(request) > 8192:
                raise ValueError("request too large")
            first_line = request.split(b"\r\n", 1)[0]
            parts = first_line.split(b" ")
            if len(parts) != 3 or parts[0] != b"GET":
                raise ValueError("only GET is supported")
            path = parts[1]
            snapshot = self.snapshot()
            if path == b"/healthz":
                status = 200 if snapshot.alive else 503
                body = snapshot.json_bytes()
            elif path == b"/readyz":
                status = 200 if snapshot.connected and snapshot.ready else 503
                body = snapshot.json_bytes()
            elif path == b"/metrics":
                status = 200
                content_type = "text/plain; version=0.0.4"
                body = self.metrics.render()
            else:
                status = 404
                body = b'{"error":"not found"}\n'
        except Exception:
            pass
        reason = {200: "OK", 400: "Bad Request", 404: "Not Found", 503: "Service Unavailable"}[status]
        header = (
            f"HTTP/1.1 {status} {reason}\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(body)}\r\n"
            "Cache-Control: no-store\r\n"
            "Connection: close\r\n\r\n"
        ).encode("ascii")
        writer.write(header + body)
        try:
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
