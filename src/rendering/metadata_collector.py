"""
Metadata collection service for adaptive threshold monitoring.

This module provides a service to collect and store metadata from sprite
generation operations for monitoring and analysis purposes.
"""

import json
import logging
import uuid
from pathlib import Path
from typing import Optional, Any
from datetime import datetime
import threading

from src.rendering.metadata_schema import SpriteMetadata

logger = logging.getLogger(__name__)


class MetadataCollector:
    """
    Collects and stores adaptive threshold metadata for monitoring.
    
    This service provides non-blocking metadata collection that doesn't
    impact sprite generation performance. Metadata is stored as JSON files
    for later analysis and threshold tuning.
    
    Thread-safe for concurrent sprite generation.
    
    Example:
        >>> collector = MetadataCollector()
        >>> metadata = {
        ...     "request_id": "abc123",
        ...     "complexity_metrics": {...},
        ...     # ... other fields
        ... }
        >>> collector.collect(metadata)  # Non-blocking
        >>> all_metadata = collector.get_all()
        >>> print(f"Collected {len(all_metadata)} records")
    """
    
    _instance: Optional['MetadataCollector'] = None
    _lock = threading.Lock()
    
    def __new__(cls, storage_dir: str = "metadata") -> 'MetadataCollector':
        """Implement singleton pattern for consistent storage location."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, storage_dir: str = "metadata"):
        """
        Initialize metadata collector.
        
        Args:
            storage_dir: Directory to store metadata JSON files (default: "metadata")
        """
        # Only initialize once (singleton pattern)
        if hasattr(self, '_initialized'):
            return
            
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._write_lock = threading.Lock()
        self._initialized = True
        
        logger.info(f"MetadataCollector initialized: {self.storage_dir.absolute()}")
    
    def collect(self, metadata: SpriteMetadata) -> None:
        """
        Collect and store metadata from a sprite generation.
        
        This operation is designed to be non-blocking and will not raise
        exceptions that could interrupt sprite generation. Any errors are
        logged but not propagated.
        
        Args:
            metadata: Complete sprite metadata to store
        """
        try:
            # Generate unique filename with timestamp, request ID, and UUID
            timestamp = metadata["timestamp"].replace(":", "-").replace(".", "-")
            request_id = metadata["request_id"][:8]  # First 8 chars for brevity
            unique_id = str(uuid.uuid4())[:8]  # Add UUID for uniqueness
            filename = f"{timestamp}_{request_id}_{unique_id}.json"
            filepath = self.storage_dir / filename
            
            # Write to file with thread safety
            with self._write_lock:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2)
            
            logger.debug(f"Metadata collected: {filename}")
            
        except Exception as e:
            # Log error but don't propagate to avoid breaking sprite generation
            logger.warning(f"Failed to collect metadata: {e}", exc_info=True)
    
    def get_all(self) -> list[SpriteMetadata]:
        """
        Load all collected metadata records.
        
        Returns:
            List of all metadata records, sorted by timestamp (newest first)
            
        Raises:
            No exceptions - invalid files are logged and skipped
        """
        metadata_list: list[SpriteMetadata] = []
        
        if not self.storage_dir.exists():
            logger.warning(f"Metadata directory does not exist: {self.storage_dir}")
            return metadata_list
        
        for filepath in self.storage_dir.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                    metadata_list.append(metadata)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in {filepath}: {e}")
            except Exception as e:
                logger.error(f"Failed to load {filepath}: {e}")
        
        # Sort by timestamp (newest first)
        metadata_list.sort(
            key=lambda m: m.get("timestamp", ""), 
            reverse=True
        )
        
        logger.info(f"Loaded {len(metadata_list)} metadata records")
        return metadata_list
    
    def clear(self) -> int:
        """
        Clear all collected metadata files.
        
        **Use with caution!** This permanently deletes all metadata files.
        Typically used only for testing or when archiving old data.
        
        Returns:
            Number of files deleted
        """
        if not self.storage_dir.exists():
            logger.warning(f"Metadata directory does not exist: {self.storage_dir}")
            return 0
        
        deleted_count = 0
        for filepath in self.storage_dir.glob("*.json"):
            try:
                filepath.unlink()
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete {filepath}: {e}")
        
        logger.info(f"Cleared {deleted_count} metadata files from {self.storage_dir}")
        return deleted_count
    
    def get_count(self) -> int:
        """
        Get count of collected metadata files.
        
        Returns:
            Number of metadata JSON files in storage
        """
        if not self.storage_dir.exists():
            return 0
        
        return sum(1 for _ in self.storage_dir.glob("*.json"))
    
    def get_summary(self) -> dict[str, Any]:
        """
        Get summary statistics of collected metadata.
        
        Returns:
            Dictionary with summary statistics
        """
        records = self.get_all()
        
        if not records:
            return {
                "total_records": 0,
                "date_range": None,
                "encoding_distribution": {},
                "avg_analysis_time_ms": None,
            }
        
        # Calculate summary statistics
        encoding_counts: dict[str, int] = {}
        analysis_times: list[float] = []
        
        for record in records:
            # Count encoding types
            encoding = record.get("encoding_decision", {}).get("selected_encoding", "unknown")
            encoding_counts[encoding] = encoding_counts.get(encoding, 0) + 1
            
            # Collect analysis times
            perf = record.get("performance_metrics", {})
            if "analysis_time_ms" in perf:
                analysis_times.append(perf["analysis_time_ms"])
        
        return {
            "total_records": len(records),
            "date_range": {
                "earliest": records[-1].get("timestamp"),
                "latest": records[0].get("timestamp"),
            },
            "encoding_distribution": encoding_counts,
            "avg_analysis_time_ms": sum(analysis_times) / len(analysis_times) if analysis_times else None,
        }
    
    def __repr__(self) -> str:
        """String representation of the collector."""
        count = self.get_count()
        return f"MetadataCollector(storage_dir={self.storage_dir}, records={count})"