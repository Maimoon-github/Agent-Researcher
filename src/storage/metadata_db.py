"""
Metadata Database

SQLite-based storage for metadata and audit trails.
"""

import sqlite3
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from contextlib import contextmanager

from loguru import logger

from ..core.config import get_config


class MetadataDB:
    """
    SQLite database for storing metadata and audit information.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.config = get_config()
        self.db_path = db_path or self.config.storage.metadata_db.path
        
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_db()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    query TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    status TEXT,
                    output_path TEXT,
                    quality_score REAL,
                    metadata TEXT
                )
            """)
            
            # Sources table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    url TEXT,
                    path TEXT,
                    source_type TEXT,
                    credibility_score REAL,
                    discovered_at TEXT,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)
            
            # Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    title TEXT,
                    format TEXT,
                    output_path TEXT,
                    quality_score REAL,
                    created_at TEXT,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)
            
            # Metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    metric_name TEXT,
                    metric_value REAL,
                    recorded_at TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)
            
            logger.debug("Database initialized")
    
    def save_session(
        self,
        session_id: str,
        query: str,
        started_at: str,
        completed_at: Optional[str] = None,
        status: str = "running",
        output_path: Optional[str] = None,
        quality_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Save or update a session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO sessions 
                (id, query, started_at, completed_at, status, output_path, quality_score, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                query,
                started_at,
                completed_at,
                status,
                output_path,
                quality_score,
                json.dumps(metadata or {}),
            ))
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent sessions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM sessions ORDER BY started_at DESC LIMIT ?",
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def save_source(
        self,
        source_id: str,
        session_id: str,
        url: Optional[str],
        path: Optional[str],
        source_type: str,
        credibility_score: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Save a source."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO sources
                (id, session_id, url, path, source_type, credibility_score, discovered_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source_id,
                session_id,
                url,
                path,
                source_type,
                credibility_score,
                datetime.now().isoformat(),
                json.dumps(metadata or {}),
            ))
    
    def save_document(
        self,
        doc_id: str,
        session_id: str,
        title: str,
        format: str,
        output_path: str,
        quality_score: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Save a document record."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO documents
                (id, session_id, title, format, output_path, quality_score, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id,
                session_id,
                title,
                format,
                output_path,
                quality_score,
                datetime.now().isoformat(),
                json.dumps(metadata or {}),
            ))
    
    def save_metric(
        self,
        session_id: str,
        metric_name: str,
        metric_value: float,
    ) -> None:
        """Save a metric value."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO metrics (session_id, metric_name, metric_value, recorded_at)
                VALUES (?, ?, ?, ?)
            """, (
                session_id,
                metric_name,
                metric_value,
                datetime.now().isoformat(),
            ))
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total sessions
            cursor.execute("SELECT COUNT(*) FROM sessions")
            total_sessions = cursor.fetchone()[0]
            
            # Average quality score
            cursor.execute("SELECT AVG(quality_score) FROM sessions WHERE quality_score IS NOT NULL")
            avg_quality = cursor.fetchone()[0] or 0
            
            # Total documents
            cursor.execute("SELECT COUNT(*) FROM documents")
            total_documents = cursor.fetchone()[0]
            
            return {
                "total_sessions": total_sessions,
                "average_quality": avg_quality,
                "total_documents": total_documents,
            }
