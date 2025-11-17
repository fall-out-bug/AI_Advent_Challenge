"""FastAPI server for Whisper speech-to-text transcription.

Purpose:
    HTTP API server for offline Whisper STT transcription.
    Provides /api/transcribe endpoint accepting audio files.
"""

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
import whisper
import tempfile
import os
from typing import Optional

app = FastAPI(title="Whisper STT Server", version="1.0.0")

# Load Whisper model (default: large-v3 for best quality, GPU recommended)
_model_name = os.getenv("WHISPER_MODEL", "large-v3")
_model = None
_model_loading = False
_model_loaded = False


def get_model():
    """Get Whisper model (loads on startup or on first request)."""
    global _model, _model_loaded
    if _model is None:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading Whisper model '{_model_name}' on device: {device}")
        _model = whisper.load_model(_model_name, device=device)
        print(f"Model loaded successfully on {device}")
        _model_loaded = True
    return _model


@app.on_event("startup")
async def startup_event():
    """Load Whisper model in background on application startup."""
    import asyncio

    async def load_model_background():
        """Load model asynchronously without blocking server startup."""
        global _model_loading, _model, _model_loaded
        _model_loading = True
        try:
            print("Starting Whisper model pre-loading...")
            # Run blocking model load in thread pool to avoid blocking event loop
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Loading Whisper model '{_model_name}' on device: {device}")
            
            # Run in executor to avoid blocking event loop
            loop = asyncio.get_event_loop()
            _model = await loop.run_in_executor(
                None, whisper.load_model, _model_name, device
            )
            print(f"Model loaded successfully on {device}")
            _model_loaded = True
            print("Whisper model pre-loaded successfully")
        except Exception as e:
            print(f"Failed to pre-load Whisper model: {e}")
            import traceback
            traceback.print_exc()
            _model_loading = False
        finally:
            _model_loading = False

    # Start model loading in background
    asyncio.create_task(load_model_background())


@app.post("/api/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: str = Form(default="ru"),
    model: Optional[str] = Form(default=None),
    initial_prompt: Optional[str] = Form(default=None),
) -> JSONResponse:
    """Transcribe audio file using Whisper.

    Args:
        file: Audio file (WAV, MP3, OGG, etc.)
        language: ISO language code (default "ru")
        model: Optional model name override

    Returns:
        JSON with text, confidence (segments), language, duration_ms
    """
    try:
        # Check if model is loaded
        global _model, _model_loading
        if _model is None:
            if _model_loading:
                raise HTTPException(
                    status_code=503,
                    detail="Model is still loading. Please try again in a few moments."
                )
            else:
                # Model failed to load or hasn't started loading yet
                raise HTTPException(
                    status_code=503,
                    detail="Model is not available. Please check server logs."
                )
        
        # Use the already loaded model
        whisper_model = _model

        # Save uploaded file to temp location
        # Read file content once
        content = await file.read()
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1] if file.filename else '.wav'}") as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # Transcribe audio with improved parameters for better quality
            # For Russian: use beam search for accuracy, initial_prompt for context
            transcribe_kwargs = {
                "language": language if language != "auto" else None,
                "task": "transcribe",
                # Quality improvement parameters
                # Note: When using beam_size, temperature is ignored (beam search uses greedy decoding)
                "beam_size": 5,  # Beam search size (better accuracy, slower) - recommended for Russian
                "best_of": 5,  # Sample best_of candidates (only used if temperature > 0)
                "temperature": (0.0, 0.2, 0.4, 0.6, 0.8, 1.0),  # Multiple temperatures for beam search
                "condition_on_previous_text": True,  # Use previous segments context (improves accuracy)
                "compression_ratio_threshold": 2.4,  # Filter out hallucinations
                "logprob_threshold": -1.0,  # Filter low-confidence segments
                "no_speech_threshold": 0.6,  # Better speech detection
            }
            
            # Add initial_prompt if provided or use default Russian prompt
            if initial_prompt:
                transcribe_kwargs["initial_prompt"] = initial_prompt
            elif language == "ru":
                transcribe_kwargs["initial_prompt"] = "Это голосовое сообщение на русском языке."
            
            result = whisper_model.transcribe(tmp_path, **transcribe_kwargs)

            # Extract text and segments
            text = result.get("text", "").strip()
            segments = result.get("segments", [])
            
            # Calculate average confidence from segments
            if segments:
                confidences = [seg.get("no_speech_prob", 0.5) for seg in segments if "no_speech_prob" in seg]
                # Convert no_speech_prob to confidence (1 - no_speech_prob)
                if confidences:
                    avg_no_speech = sum(confidences) / len(confidences)
                    confidence = 1.0 - avg_no_speech  # Invert: lower no_speech = higher confidence
                else:
                    confidence = 0.85  # Default confidence
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
                            "confidence": 1.0 - seg.get("no_speech_prob", 0.5) if "no_speech_prob" in seg else 0.85,
                        }
                        for seg in segments
                    ],
                }
            )

        except Exception as e:
            # Log error for debugging
            import traceback
            error_trace = traceback.format_exc()
            print(f"Transcription error: {str(e)}")
            print(f"Traceback: {error_trace}")
            raise HTTPException(
                status_code=500,
                detail=f"Transcription failed: {str(e)}"
            )
        finally:
            # Cleanup temp file
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except HTTPException:
        # Re-raise HTTP exceptions (e.g., 503 for model not loaded)
        raise
    except Exception as e:
        # Log unexpected errors
        import traceback
        error_trace = traceback.format_exc()
        print(f"Unexpected error in transcribe endpoint: {str(e)}")
        print(f"Traceback: {error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )


@app.get("/health")
async def health():
    """Health check endpoint - checks if model is loaded."""
    global _model_loaded, _model
    if _model is None:
        return JSONResponse(
            status_code=503,
            content={"status": "loading", "model": _model_name, "message": "Model is still loading"}
        )
    return {"status": "ok", "model": _model_name, "loaded": True}


@app.get("/")
async def root():
    """Root endpoint."""
    return {"service": "Whisper STT Server", "version": "1.0.0", "model": _model_name}

