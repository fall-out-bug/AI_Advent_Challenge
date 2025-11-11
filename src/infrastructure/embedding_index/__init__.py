"""Embedding index infrastructure package."""

from .chunking.sliding_window_chunker import SlidingWindowChunker
from .collectors.filesystem_collector import FilesystemDocumentCollector
from .gateways.local_embedding_gateway import LocalEmbeddingGateway
from .preprocessing.text_preprocessor import TextPreprocessor
from .repositories.mongo_document_repository import (
    MongoChunkRepository,
    MongoDocumentRepository,
)

__all__ = [
    "FilesystemDocumentCollector",
    "LocalEmbeddingGateway",
    "MongoChunkRepository",
    "MongoDocumentRepository",
    "SlidingWindowChunker",
    "TextPreprocessor",
]
