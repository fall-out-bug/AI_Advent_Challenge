"""
Token Analysis Service - FastAPI service for heavy ML operations.

This service runs in a separate container and provides:
- Accurate token counting with HuggingFace tokenizers
- Advanced text compression strategies
- TF-IDF based summarization
- Semantic chunking

Refactored to use TokenServiceHandler for separation of concerns.
"""

import uvicorn
from api.handlers.token_handler import TokenServiceHandler


def create_app():
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    handler = TokenServiceHandler()
    return handler.create_app()


# Create the FastAPI app
app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)