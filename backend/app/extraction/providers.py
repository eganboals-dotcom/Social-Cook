"""Concrete provider stubs — implemented in Phase 1.

These satisfy the interfaces in `base.py` so the architecture is reviewable now.
Each raises NotImplementedError until Phase 1 wires the real logic.
"""
from __future__ import annotations

from app.extraction.base import IngestResult, Transcriber, VideoIngest, VisionReader


class ShareSheetIngest(VideoIngest):
    """Primary, ToS-safe path: the mobile share sheet hands us the caption/text
    directly, so no platform scraping is required. The pipeline can run on
    caption text alone."""

    def supports(self, url: str) -> bool:
        # A caption may be supplied for any URL via the share sheet.
        return True

    async def ingest(self, url: str, *, caption: str | None = None) -> IngestResult:
        # Phase 1: detect platform from the URL and pass the caption through.
        raise NotImplementedError("ShareSheetIngest.ingest — Phase 1")


class WhisperTranscriber(Transcriber):
    """OpenAI Whisper API transcription (the chosen default backend)."""

    async def transcribe(self, audio_path: str) -> str:
        raise NotImplementedError("WhisperTranscriber.transcribe — Phase 1")


class AnthropicVisionReader(VisionReader):
    """On-screen text reading via the Anthropic API (claude-sonnet-4-6)."""

    async def read_frames(self, frame_paths: list[str]) -> str:
        raise NotImplementedError("AnthropicVisionReader.read_frames — Phase 1")
