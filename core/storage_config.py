# core/storage_config.py

"""Phase 7: Storage configuration and setup for document management."""

import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class StorageProvider(str, Enum):
    """Supported storage providers."""
    LOCAL = "local"
    AWS_S3 = "aws_s3"
    AZURE_BLOB = "azure_blob"
    GCP_STORAGE = "gcp_storage"

class EncryptionProvider(str, Enum):
    """Supported encryption providers."""
    AES_GCM = "aes_gcm"
    AWS_KMS = "aws_kms"
    AZURE_KEY_VAULT = "azure_key_vault"

class StorageConfig:
    """Central storage configuration."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._setup_default_config()

    def _setup_default_config(self):
        """Setup default storage configuration."""
        defaults = {
            "provider": StorageProvider.LOCAL,
            "encryption": {
                "provider": EncryptionProvider.AES_GCM,
                "key_rotation_days": 90,
                "encrypt_at_rest": True
            },
            "local": {
                "storage_root": self._get_storage_root(),
                "max_file_size_mb": 100,
                "cleanup_retention_days": 30
            },
            "virus_scanning": {
                "enabled": True,
                "quarantine_infected": True,
                "scan_timeout_seconds": 30
            },
            "exports": {
                "retention_hours": 24,
                "max_concurrent_exports": 5,
                "compression_enabled": True
            },
            "court_packages": {
                "retention_days": 7,
                "auto_cleanup": True,
                "e_filing_integration": False
            },
            "audit": {
                "log_file_access": True,
                "log_exports": True,
                "log_court_packages": True,
                "retention_days": 365
            }
        }

        # Merge with provided config
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
            elif isinstance(value, dict) and isinstance(self.config[key], dict):
                # Merge nested dicts
                merged = value.copy()
                merged.update(self.config[key])
                self.config[key] = merged

    def _get_storage_root(self) -> str:
        """Get storage root directory."""
        # Try environment variable first
        storage_root = os.getenv("GOLDLEAVES_STORAGE_ROOT")
        if storage_root:
            return storage_root

        # Default to project storage directory
        project_root = Path(__file__).parent.parent
        storage_dir = project_root / "storage"
        storage_dir.mkdir(exist_ok=True)

        return str(storage_dir)

    def get_provider(self) -> StorageProvider:
        """Get configured storage provider."""
        return StorageProvider(self.config["provider"])

    def get_storage_root(self) -> str:
        """Get storage root directory."""
        return self.config["local"]["storage_root"]

    def get_max_file_size_mb(self) -> int:
        """Get maximum file size in MB."""
        return self.config["local"]["max_file_size_mb"]

    def is_encryption_enabled(self) -> bool:
        """Check if encryption at rest is enabled."""
        return self.config["encryption"]["encrypt_at_rest"]

    def get_encryption_provider(self) -> EncryptionProvider:
        """Get encryption provider."""
        return EncryptionProvider(self.config["encryption"]["provider"])

    def is_virus_scanning_enabled(self) -> bool:
        """Check if virus scanning is enabled."""
        return self.config["virus_scanning"]["enabled"]

    def get_export_retention_hours(self) -> int:
        """Get export file retention in hours."""
        return self.config["exports"]["retention_hours"]

    def get_court_package_retention_days(self) -> int:
        """Get court package retention in days."""
        return self.config["court_packages"]["retention_days"]

    def is_audit_logging_enabled(self) -> bool:
        """Check if audit logging is enabled."""
        return self.config["audit"]["log_file_access"]

    def get_full_config(self) -> Dict[str, Any]:
        """Get complete configuration."""
        return self.config.copy()

# Global storage config instance
_storage_config: Optional[StorageConfig] = None

def get_storage_config() -> StorageConfig:
    """Get global storage configuration."""
    global _storage_config
    if _storage_config is None:
        _storage_config = StorageConfig()
    return _storage_config

def configure_storage(config: Dict[str, Any]) -> None:
    """Configure storage with custom settings."""
    global _storage_config
    _storage_config = StorageConfig(config)

def setup_storage_directories() -> None:
    """Setup required storage directories."""
    config = get_storage_config()
    storage_root = Path(config.get_storage_root())

    # Create directory structure
    directories = [
        storage_root / "documents",
        storage_root / "exports",
        storage_root / "packages",
        storage_root / "temp",
        storage_root / "quarantine"
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

        # Create .gitkeep for empty directories
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

# Default configuration for different environments
def get_development_config() -> Dict[str, Any]:
    """Get development storage configuration."""
    return {
        "provider": StorageProvider.LOCAL,
        "encryption": {
            "encrypt_at_rest": False,  # Disabled for development
            "provider": EncryptionProvider.AES_GCM
        },
        "virus_scanning": {
            "enabled": False  # Disabled for development
        },
        "audit": {
            "log_file_access": True,
            "retention_days": 30  # Shorter retention for dev
        }
    }

def get_production_config() -> Dict[str, Any]:
    """Get production storage configuration."""
    return {
        "provider": StorageProvider.AWS_S3,  # Use cloud storage
        "encryption": {
            "encrypt_at_rest": True,
            "provider": EncryptionProvider.AWS_KMS,
            "key_rotation_days": 90
        },
        "virus_scanning": {
            "enabled": True,
            "quarantine_infected": True
        },
        "exports": {
            "retention_hours": 24,
            "max_concurrent_exports": 10
        },
        "court_packages": {
            "retention_days": 30,  # Longer retention in production
            "e_filing_integration": True
        },
        "audit": {
            "log_file_access": True,
            "log_exports": True,
            "log_court_packages": True,
            "retention_days": 2555  # 7 years
        }
    }

# Initialize storage on import
setup_storage_directories()
