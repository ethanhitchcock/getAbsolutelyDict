from __future__ import annotations

import logging
import time
from typing import Optional

from openai import OpenAI, OpenAIError
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential

from .models import TranscriptionError, TranscriptionRequest, TranscriptionResult
from .settings import Settings

logger = logging.getLogger(__name__)


class TranscriptionClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = self._create_client()

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    def _create_client(self) -> Optional[OpenAI]:
        if not self._settings.api_key:
            logger.warning("No API key configured; transcription will be disabled")
            return None
        kwargs = {"api_key": self._settings.api_key}
        if self._settings.transcription.api_base_url:
            kwargs["base_url"] = self._settings.transcription.api_base_url
        return OpenAI(**kwargs)

    def transcribe(self, request: TranscriptionRequest) -> TranscriptionResult:
        if self._client is None:
            raise TranscriptionError("Transcription client is not configured")
        start = time.monotonic()
        try:
            text = self._transcribe_with_retry(request)
        except RetryError as exc:
            raise TranscriptionError("Transcription failed after retries") from exc
        duration = time.monotonic() - start
        return TranscriptionResult(text=text, duration_seconds=duration)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def _transcribe_with_retry(self, request: TranscriptionRequest) -> str:
        assert self._client is not None
        logger.info("Submitting transcription request for %s", request.audio_path)
        try:
            with open(request.audio_path, "rb") as fh:
                response = self._client.audio.transcriptions.create(
                    model=self._settings.transcription.model,
                    file=fh,
                    temperature=self._settings.transcription.temperature,
                    language=self._settings.transcription.language,
                    prompt=request.prompt,
                    response_format="text",
                )
        except OpenAIError as exc:
            logger.exception("OpenAI transcription error: %s", exc)
            raise
        logger.debug("Transcription response received: %s", response)
        return getattr(response, "text", str(response))
