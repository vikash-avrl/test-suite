"""
Helper utilities for Chrome Extension testing
"""
import os
from pathlib import Path


def get_extension_path():
    """
    Get the Chrome extension path from environment variable or default
    
    Returns:
        Path: Path to the Chrome extension directory
    """
    default_path = Path(__file__).parent / "chrome-extension"
    extension_path = Path(os.getenv("EXTENSION_PATH", default_path))
    
    if not extension_path.exists():
        raise FileNotFoundError(
            f"Chrome extension not found at {extension_path}. "
            f"Set EXTENSION_PATH environment variable to correct path."
        )
    
    return extension_path


def validate_extension(extension_path: Path):
    """
    Validate that the extension directory contains required files
    
    Args:
        extension_path: Path to extension directory
        
    Returns:
        bool: True if valid, raises exception otherwise
    """
    manifest_path = extension_path / "manifest.json"
    
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"manifest.json not found in {extension_path}. "
            f"Please ensure this is a valid Chrome extension directory."
        )
    
    return True

