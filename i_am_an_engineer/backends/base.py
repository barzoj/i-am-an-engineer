"""Backend interfaces. Local-GPU can stub these; API backends implement them."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class TwinCreateResult:
    avatar_group_id: str
    look_id: str | None = None
    default_voice_id: str | None = None
    status: str = "pending"
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class VideoJob:
    video_id: str
    status: str = "pending"
    download_url: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class VoiceCloneResult:
    voice_id: str
    provider: str
    status: str = "ready"
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrollClip:
    path: Path | None
    prompt: str
    duration_s: float
    model: str
    job_id: str | None = None
    url: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


class Backend(ABC):
    name: str = "base"

    def status(self) -> dict[str, Any]:
        return {"name": self.name, "configured": False}


class TwinBackend(Backend):
    @abstractmethod
    def create_digital_twin(self, footage: Path, *, name: str) -> TwinCreateResult: ...

    @abstractmethod
    def request_consent(self, avatar_group_id: str) -> dict[str, Any]: ...

    @abstractmethod
    def poll_avatar(self, look_id: str) -> dict[str, Any]: ...

    @abstractmethod
    def render_aroll(
        self,
        *,
        avatar_id: str,
        script: str,
        voice_id: str | None,
        aspect_ratio: str,
        engine: str = "avatar_v",
        resolution: str = "1080p",
    ) -> VideoJob: ...

    @abstractmethod
    def poll_video(self, video_id: str) -> VideoJob: ...


class VoiceBackend(Backend):
    @abstractmethod
    def clone_instant(self, samples: list[Path], *, name: str) -> VoiceCloneResult: ...

    @abstractmethod
    def tts(self, text: str, voice_id: str, out: Path) -> Path: ...

    @abstractmethod
    def sts(self, audio: Path, voice_id: str, out: Path) -> Path: ...


class BrollBackend(Backend):
    @abstractmethod
    def generate(self, prompt: str, *, duration_s: float, model: str, out_dir: Path) -> BrollClip: ...


class LocalTwinBackend(TwinBackend):
    """Stub for a future local-GPU talking model. Interface only."""

    name = "local"

    def status(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "configured": False,
            "message": "Local GPU twin backend is a stub. Implement EchoMimic/InfiniteTalk later.",
        }

    def create_digital_twin(self, footage: Path, *, name: str) -> TwinCreateResult:
        raise NotImplementedError("local twin backend is a stub")

    def request_consent(self, avatar_group_id: str) -> dict[str, Any]:
        raise NotImplementedError("local twin backend is a stub")

    def poll_avatar(self, look_id: str) -> dict[str, Any]:
        raise NotImplementedError("local twin backend is a stub")

    def render_aroll(self, **kwargs) -> VideoJob:
        raise NotImplementedError("local twin backend is a stub")

    def poll_video(self, video_id: str) -> VideoJob:
        raise NotImplementedError("local twin backend is a stub")


class BackendRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], Backend]] = {}

    def register(self, name: str, factory: Callable[[], Backend]) -> None:
        self._factories[name] = factory

    def create(self, name: str) -> Backend:
        if name not in self._factories:
            raise KeyError(f"unknown backend {name!r}; known: {sorted(self._factories)}")
        return self._factories[name]()

    def names(self) -> list[str]:
        return sorted(self._factories)


registry = BackendRegistry()
registry.register("local", LocalTwinBackend)
