"""
File I/O utilities for the extraction pipeline.

Handles saving JSON output, downloading images/diagrams,
and ensuring output directories exist.
"""
import json
import httpx
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Directory where downloaded diagrams are saved
DIAGRAMS_DIR = settings.output_dir / "diagrams"


def ensure_dir(directory: Path) -> Path:
    """
    Create directory (and parents) if it doesn't exist.

    Args:
        directory: Path to create.

    Returns:
        The same path, for chaining.
    """
    directory.mkdir(parents=True, exist_ok=True)
    return directory


async def download_image(
    url: str, 
    save_path: Path, 
    client: Optional[httpx.AsyncClient] = None
) -> bool:
    """
    Download an image from a URL and save to disk.

    Used to fetch diagrams from LlamaCloud's presigned URLs.

    Args:
        url:       Presigned URL to download from.
        save_path: Local path to save the image file.
        client:    Optional persistent AsyncClient to reuse.

    Returns:
        True if download succeeded, False otherwise.
    """
    try:
        ensure_dir(save_path.parent)

        if client:
            response = await client.get(url)
            response.raise_for_status()
        else:
            async with httpx.AsyncClient() as new_client:
                response = await new_client.get(url)
                response.raise_for_status()

        save_path.write_bytes(response.content)
        logger.info(f"Downloaded image → {save_path.name}")
        return True

    except Exception as e:
        logger.error(f"Failed to download image from {url}: {e}")
        return False


async def batch_download_images(
    image_data: List[Dict[str, Any]], 
    image_dir: Path
) -> List[str]:
    """
    Download multiple images concurrently using a single client.

    Args:
        image_data: List of dicts with 'presigned_url' and 'filename'.
        image_dir:  Directory to save images in.

    Returns:
        List of local file paths to successfully downloaded images.
    """
    if not image_data:
        return []

    ensure_dir(image_dir)
    saved_images = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = []
        for img in image_data:
            if not img.get("presigned_url"):
                continue
            
            save_path = image_dir / img["filename"]
            tasks.append(download_image(img["presigned_url"], save_path, client))
        
        results = await asyncio.gather(*tasks)
        
        # Correlate results back to paths
        for success, img in zip(results, [i for i in image_data if i.get("presigned_url")]):
            if success:
                saved_images.append(str(image_dir / img["filename"]))

    return saved_images


def save_json(data: Any, filename: str, output_dir: Path = None) -> Path:
    """
    Save data as a formatted JSON file.

    Args:
        data:       Data to serialize (dict, list, or Pydantic model).
        filename:   Name for the output file (e.g. "results.json").
        output_dir: Directory to save in. Defaults to settings.output_dir.

    Returns:
        Path to the saved JSON file.
    """
    output_dir = output_dir or settings.output_dir
    ensure_dir(output_dir)

    filepath = output_dir / filename

    # If data is a Pydantic model, convert to dict first
    if hasattr(data, "model_dump"):
        data = data.model_dump()

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved JSON → {filepath}")
    return filepath
