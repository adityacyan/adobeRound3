# Backend package initialization"""PDF Document Processing Package"""

# Import all the classes you want to make available
from .document_processor import (
    DocumentProcessor,
    ProcessedDocument,
    ProcessingProgress,
    DocumentSection,
    document_processor  # The global instance
)

# Optional: Define what gets imported with "from package import *"
__all__ = [
    "DocumentProcessor",
    "ProcessedDocument", 
    "ProcessingProgress",
    "DocumentSection",
    "document_processor"
]

# Optional: Package metadata
__version__ = "1.0.0"
__author__ = "CYAN"
