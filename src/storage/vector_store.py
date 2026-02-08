"""
Vector Store Wrapper

Provides unified interface to ChromaDB vector storage.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from loguru import logger

from ..core.config import get_config


class VectorStore:
    """
    Wrapper around ChromaDB for vector storage operations.
    """
    
    def __init__(self, collection_name: Optional[str] = None):
        self.config = get_config()
        self.collection_name = collection_name or self.config.storage.vector_db.collection_name
        self._client = None
        self._collection = None
    
    @property
    def client(self):
        """Lazy load ChromaDB client."""
        if self._client is None:
            import chromadb
            from chromadb.config import Settings
            
            self._client = chromadb.PersistentClient(
                path=self.config.storage.vector_db.persist_directory,
                settings=Settings(anonymized_telemetry=False),
            )
        return self._client
    
    @property
    def collection(self):
        """Get or create collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection
    
    def add(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Add documents to the collection."""
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas or [{}] * len(ids),
        )
        logger.debug(f"Added {len(ids)} documents to {self.collection_name}")
    
    def upsert(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Upsert documents to the collection."""
        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas or [{}] * len(ids),
        )
        logger.debug(f"Upserted {len(ids)} documents to {self.collection_name}")

    def update(
        self,
        ids: List[str],
        documents: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Update documents in the collection."""
        self.collection.update(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.debug(f"Updated {len(ids)} documents in {self.collection_name}")
    
    def query(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Query the collection."""
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )
    
    def get(self, ids: List[str]) -> Dict[str, Any]:
        """Get documents by IDs."""
        return self.collection.get(ids=ids)
    
    def delete(self, ids: List[str]) -> None:
        """Delete documents by IDs."""
        self.collection.delete(ids=ids)
        logger.debug(f"Deleted {len(ids)} documents from {self.collection_name}")
    
    def count(self) -> int:
        """Get document count."""
        return self.collection.count()
    
    def clear(self) -> None:
        """Clear all documents from collection."""
        # Delete and recreate collection
        self.client.delete_collection(self.collection_name)
        self._collection = None
        _ = self.collection  # Recreate
        logger.info(f"Cleared collection: {self.collection_name}")
