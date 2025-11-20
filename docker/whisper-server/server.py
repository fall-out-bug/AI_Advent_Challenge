"""Whisper STT FastAPI server for speech-to-text transcription.

Purpose:
    Provides HTTP API endpoint for transcribing audio files using OpenAI's Whisper model.
    Supports async model loading to prevent blocking server startup.
"""

import asyncio
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import whisper
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

app = FastAPI(title="Whisper STT Server")

# Global model and loading state
_model: Optional[whisper.Whisper] = None
_model_loading = False
_model_name: str = os.getenv("WHISPER_MODEL", "base")


@app.on_event("startup")
async def startup_event() -> None:
    """Load Whisper model asynchronously on startup.

    Purpose:
        Loads the Whisper model in a background task to prevent blocking
        the server startup. Model loading happens in a thread pool executor
        to avoid blocking the event loop.

    Example:
        >>> # Model will be loaded automatically on server startup
        >>> # Check /health endpoint to monitor loading status
    """
    global _model, _model_loading

    if _model is not None:
        return  # Already loaded

    _model_loading = True
    loop = asyncio.get_event_loop()

    def load_model() -> whisper.Whisper:
        """Load Whisper model synchronously.

        Returns:
            Loaded Whisper model instance.
        """
        print(f"Loading Whisper model '{_model_name}' on device: cuda")
        return whisper.load_model(_model_name, device="cuda")

    # Load model in executor to avoid blocking
    executor = ThreadPoolExecutor(max_workers=1)
    try:
        _model = await loop.run_in_executor(executor, load_model)
        print(f"Model '{_model_name}' loaded successfully")
        _model_loading = False
    except Exception as e:
        print(f"Failed to load model: {e}")
        _model_loading = False
        raise


@app.get("/health")
async def health() -> JSONResponse:
    """Health check endpoint.

    Purpose:
        Returns server health status including model loading state.

    Returns:
        JSON response with status, model name, and loaded flag.

    Example:
        >>> response = await client.get("/health")
        >>> response.json()
        {"status": "ok", "model": "base", "loaded": True}
    """
    return JSONResponse(
        content={
            "status": "ok",
            "model": _model_name,
            "loaded": _model is not None,
            "loading": _model_loading,
        }
    )


@app.post("/api/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: str = Form(default="ru"),
    model: Optional[str] = Form(default=None),
    initial_prompt: Optional[str] = Form(default=None),
) -> JSONResponse:
    """Transcribe audio file using Whisper.

    Purpose:
        Accepts audio file upload, transcribes it using Whisper model,
        and returns transcribed text with confidence scores and metadata.

    Args:
        file: Audio file to transcribe.
        language: Language code (default: "ru" for Russian).
        model: Optional model override (not used, uses loaded model).
        initial_prompt: Optional initial prompt for better context.

    Returns:
        JSON response with transcribed text, confidence, language, duration, and segments.

    Raises:
        HTTPException: If model is not loaded or transcription fails.

    Example:
        >>> response = await client.post(
        ...     "/api/transcribe",
        ...     files={"file": audio_file},
        ...     data={"language": "ru"}
        ... )
        >>> response.json()
        {
            "text": "Привет, мир!",
            "confidence": 0.95,
            "language": "ru",
            "duration_ms": 2000,
            "segments": [...]
        }
    """
    try:
        # Check if model is loaded
        global _model, _model_loading
        if _model is None:
            if _model_loading:
                raise HTTPException(
                    status_code=503,
                    detail="Model is still loading. Please try again in a few moments.",
                )
            else:
                raise HTTPException(
                    status_code=503,
                    detail="Model is not available. Please check server logs.",
                )

        # Use the already loaded model
        whisper_model = _model

        # Save uploaded file to temp location
        content = await file.read()

        # Save to temp file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f".{file.filename.split('.')[-1] if file.filename else '.wav'}",
        ) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # Transcribe audio with improved parameters for better quality
            transcribe_kwargs = {
                "language": language if language != "auto" else None,
                "task": "transcribe",
                "beam_size": 5,
                "best_of": 5,
                "temperature": (0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
                "condition_on_previous_text": True,
                "compression_ratio_threshold": 2.4,
                "logprob_threshold": -1.0,
                "no_speech_threshold": 0.6,
            }

            # Add initial_prompt if provided or use default Russian prompt
            if initial_prompt:
                transcribe_kwargs["initial_prompt"] = initial_prompt
            elif language == "ru":
                transcribe_kwargs[
                    "initial_prompt"
                ] = "Это голосовое сообщение на русском языке."

            result = whisper_model.transcribe(tmp_path, **transcribe_kwargs)

            # Extract text and segments
            text = result.get("text", "").strip()
            segments = result.get("segments", [])

            # Calculate average confidence from segments
            if segments:
                confidences = [
                    seg.get("no_speech_prob", 0.5)
                    for seg in segments
                    if "no_speech_prob" in seg
                ]
                if confidences:
                    avg_no_speech = sum(confidences) / len(confidences)
                    confidence = 1.0 - avg_no_speech
                else:
                    confidence = 0.85
            else:
                confidence = 0.85

            # Calculate duration from segments or result
            duration_ms = int(result.get("duration", 0) * 1000)

            # Return JSON response
            return JSONResponse(
                content={
                    "text": text,
                    "confidence": confidence,
                    "language": result.get("language", language),
                    "duration_ms": duration_ms,
                    "segments": [
                        {
                            "id": seg.get("id", 0),
                            "text": seg.get("text", ""),
                            "start": seg.get("start", 0),
                            "end": seg.get("end", 0),
                            "confidence": (
                                1.0 - seg.get("no_speech_prob", 0.5)
                                if "no_speech_prob" in seg
                                else 0.85
                            ),
                        }
                        for seg in segments
                    ],
                }
            )

        except Exception as e:
            import traceback

            error_trace = traceback.format_exc()
            print(f"Transcription error: {str(e)}")
            print(f"Traceback: {error_trace}")
            raise HTTPException(
                status_code=500, detail=f"Transcription failed: {str(e)}"
            )
        finally:
            # Cleanup temp file
            if "tmp_path" in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        error_trace = traceback.format_exc()
        print(f"Unexpected error in transcribe endpoint: {str(e)}")
        print(f"Traceback: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
