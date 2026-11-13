"""Local-GPU backend stub. Clear interface for later talking models."""
from __future__ import annotations

from i_am_an_engineer.backends.base import LocalTwinBackend, registry

# Re-export and ensure registration
registry.register("local-gpu", LocalTwinBackend)
