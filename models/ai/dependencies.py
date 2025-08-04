# models/ai/dependencies.py
"""Dependencies for AI models - imports from parent models directory."""

# Import from parent models directory
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from models.dependencies import Base, utcnow
from datetime import datetime

# Re-export for AI models
__all__ = ['Base', 'utcnow', 'datetime']
