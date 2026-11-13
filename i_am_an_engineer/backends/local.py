"""Local-GPU backend stub. Clear interface for later talking models."""
from __future__ import annotations

from typing import Any

from i_am_an_engineer.backends.base import LocalTwinBackend, registry


class LocalGpuTwinBackend(LocalTwinBackend):
    name = "local-gpu"

    def status(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "role": "twin stub",
            "configured": False,
            "message": "Local GPU twin backend is a stub. Implement EchoMimic/InfiniteTalk later.",
        }


registry.register("local-gpu", LocalGpuTwinBackend)
