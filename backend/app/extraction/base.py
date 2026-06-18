"""Extraction interfaces — implemented in Phase 1.

The recipe pipeline combines up to three signals — caption text, transcribed
audio, and on-screen/vision text — and hands them to an LLM that returns a
structured recipe. Each signal source sits behind an interface so providers are
pluggable and swappable without touching the rest of the app.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class IngestResult:
    """Whatever a VideoIngest provider managed to retrieve for a post."""

    caption: str | None = None  # post caption / description text
    audio_path: str | None = None  # local path to extracted audio, if any
    frame_paths: list[str] = field(default_factory=list)  # sampled video frames
    platform: str | None = None
    extra: dict = field(default_factory=dict)


class VideoIngest(ABC):
    """Best-effort retrieval of a post's caption / audio / frames.

    ToS: The major platforms (TikTok, Instagram, YouTube) do NOT offer an
    official API to download a video by link, and downloading their video files
    generally violates their Terms of Service. Implementations MUST NOT assume a
    download API exists. The PRIMARY path is the mobile share sheet — the client
    hands us caption/text directly, no scraping required. Treat any media
    download as a best-effort enhancement, and document the ToS assumptions of
    any provider that fetches media right here in its docstring.
    """

    @abstractmethod
    def supports(self, url: str) -> bool:
        """Return True if this provider can handle the given URL/platform."""

    @abstractmethod
    async def ingest(self, url: str, *, caption: str | None = None) -> IngestResult:
        """Gather whatever signals are available for the post."""


class Transcriber(ABC):
    """Speech-to-text over an audio file (the audio signal).

    Default implementation (Phase 1) wraps the OpenAI Whisper API. Pluggable so
    we can swap to Groq / local faster-whisper without touching callers.
    """

    @abstractmethod
    async def transcribe(self, audio_path: str) -> str: ...


class VisionReader(ABC):
    """Read on-screen text / infer steps from sampled frames (vision signal).

    The most expensive and slowest signal — callers should only invoke it when
    caption + audio are insufficient.
    """

    @abstractmethod
    async def read_frames(self, frame_paths: list[str]) -> str: ...
