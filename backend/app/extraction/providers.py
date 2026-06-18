"""Concrete extraction providers.

Each implements an interface from `base.py`. The share-sheet ingest is the
primary, ToS-safe path (the client hands us the caption); the Whisper and vision
providers are the best-effort, more-expensive signals and only run when a
provider actually supplies media.
"""
from __future__ import annotations

import base64
from pathlib import Path

from app.config import get_settings
from app.extraction.base import IngestResult, Transcriber, VideoIngest, VisionReader
from app.extraction.clients import anthropic_client, openai_client
from app.extraction.platforms import detect_platform


class ShareSheetIngest(VideoIngest):
    """Primary, ToS-safe path: the client (share sheet or paste) supplies the
    caption/text directly, so no platform scraping or media download happens.

    ToS: this provider never fetches platform media. A future provider could add
    best-effort media retrieval behind this same interface — and would document
    its ToS assumptions here.
    """

    def supports(self, url: str) -> bool:
        return True

    async def ingest(self, url: str, *, caption: str | None = None) -> IngestResult:
        return IngestResult(caption=caption, platform=detect_platform(url))


class WhisperTranscriber(Transcriber):
    """OpenAI Whisper API transcription (the chosen default backend)."""

    async def transcribe(self, audio_path: str) -> str:
        client = openai_client()
        model = get_settings().whisper_model
        with open(audio_path, "rb") as fh:
            resp = await client.audio.transcriptions.create(model=model, file=fh)
        return getattr(resp, "text", "") or ""


_IMAGE_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


class AnthropicVisionReader(VisionReader):
    """Read on-screen text from sampled frames via claude-sonnet-4-6."""

    MAX_FRAMES = 8

    async def read_frames(self, frame_paths: list[str]) -> str:
        if not frame_paths:
            return ""
        client = anthropic_client()
        settings = get_settings()

        content: list[dict] = []
        for raw_path in frame_paths[: self.MAX_FRAMES]:
            path = Path(raw_path)
            media_type = _IMAGE_MEDIA_TYPES.get(path.suffix.lower(), "image/jpeg")
            data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
            content.append(
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": data},
                }
            )
        content.append(
            {
                "type": "text",
                "text": (
                    "These are frames from a cooking video. Transcribe any on-screen "
                    "text relevant to the recipe — ingredient names, amounts, and step "
                    "instructions. Return plain text only; if there is no "
                    "recipe-relevant text, return an empty string."
                ),
            }
        )

        resp = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1024,
            messages=[{"role": "user", "content": content}],
        )
        return next(
            (b.text for b in resp.content if getattr(b, "type", None) == "text"), ""
        )
