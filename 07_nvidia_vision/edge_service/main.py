"""FC01 edge-service entry point.

No inference backend is supplied in Revision E.  Running this entry point proves
configuration/transport supervision only; VISION_READY remains false until a
controlled backend is implemented and injected by a later approved change.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import signal

from observability import HealthServer, Metrics, configure_logging
from opcua_adapter import AdapterConfig, OpcUaVisionAdapter
from service import VisionService


async def run(config_path: Path) -> None:
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    logger = configure_logging(file_path=os.environ.get("FC01_EDGE_LOG_PATH"))
    metrics = Metrics()
    service = VisionService()  # Deliberately fail-closed: no model/backend exists.
    adapter = OpcUaVisionAdapter(AdapterConfig.from_files(config_path), service,
                                 metrics=metrics, logger=logger)
    health = HealthServer(raw["health"]["bind"], raw["health"]["port"],
                          adapter.health_snapshot, metrics)
    stop = asyncio.Event()

    def request_stop(*_args) -> None:
        stop.set()

    for signum in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(signum, request_stop)
        except (AttributeError, ValueError):
            pass

    logger.warning(
        "no controlled inference backend is delivered; VISION_READY will remain low",
        extra={"event": "model_backend_absent", "diagnostic_code": "NO_CONTROLLED_MODEL"},
    )
    await health.start()
    try:
        await adapter.run_forever(stop)
    finally:
        await health.stop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FC01 non-safety vision OPC UA edge service")
    parser.add_argument("--config", type=Path, required=True,
                        help="Path to opcua_runtime_config.json")
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(run(parse_args().config.resolve()))
