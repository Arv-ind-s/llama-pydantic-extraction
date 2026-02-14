"""
LlamaParse PDF parser.

Scans data/input/new/ for PDF files, sends each to LlamaCloud for parsing,
and returns the raw markdown content for downstream extraction.

Uses the llama_cloud SDK (AsyncLlamaCloud) with async file upload + parse.
"""
import asyncio
from pathlib import Path
from typing import Dict, List

from llama_cloud import AsyncLlamaCloud

from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


# Subfolder inside data/input/ where new PDFs are placed for processing
NEW_PDF_DIR = settings.input_dir / "new"


async def parse_single_pdf(client: AsyncLlamaCloud, pdf_path: Path) -> Dict:
    """
    Upload and parse a single PDF via LlamaCloud.

    Args:
        client:   Authenticated AsyncLlamaCloud client.
        pdf_path: Path to the PDF file on disk.

    Returns:
        Dict with 'filename' and 'markdown' content from parsing.
    """
    logger.info(f"Uploading: {pdf_path.name}")

    # Step 1: Upload the file to LlamaCloud
    file_obj = await client.files.create(
        file=str(pdf_path),
        purpose="parse"
    )
    logger.info(f"Uploaded {pdf_path.name} → file_id: {file_obj.id}")

    # Step 2: Parse the uploaded file
    result = await client.parsing.parse(
        file_id=file_obj.id,
        tier="agentic",         # good balance of accuracy and structure
        version="latest",
        expand=["markdown"],    # we only need markdown content for extraction
    )
    logger.info(f"Parsed {pdf_path.name} successfully")

    # Step 3: Collect markdown from all pages into a single string
    full_markdown = "\n\n".join(
        page.markdown for page in result.markdown.pages
    )

    return {
        "filename": pdf_path.name,
        "markdown": full_markdown,
    }


def find_pdfs(directory: Path) -> List[Path]:
    """
    Find all PDF files in the given directory.

    Args:
        directory: Path to scan for .pdf files.

    Returns:
        Sorted list of PDF file paths.
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return []

    pdfs = sorted(directory.glob("*.pdf"))
    logger.info(f"Found {len(pdfs)} PDF(s) in {directory}")
    return pdfs


async def parse_all_pdfs() -> List[Dict]:
    """
    Main entry point: find all PDFs in data/input/new/ and parse them.

    Returns:
        List of dicts, each with 'filename' and 'markdown' keys.
    """
    pdfs = find_pdfs(NEW_PDF_DIR)

    if not pdfs:
        logger.warning("No PDF files found to process.")
        return []

    # Create an authenticated client using the API key from settings
    client = AsyncLlamaCloud(api_key=settings.llama_cloud_api_key)

    results = []
    for i, pdf_path in enumerate(pdfs, 1):
        logger.info(f"Processing [{i}/{len(pdfs)}]: {pdf_path.name}")
        try:
            result = await parse_single_pdf(client, pdf_path)
            results.append(result)
        except Exception as e:
            # Log and skip failed PDFs — don't let one failure stop the batch
            logger.error(f"Failed to parse {pdf_path.name}: {e}")

    logger.info(f"Parsing complete: {len(results)}/{len(pdfs)} succeeded")
    return results


# Allow running this module directly for quick testing
if __name__ == "__main__":
    parsed = asyncio.run(parse_all_pdfs())
    for item in parsed:
        print(f"\n{'='*60}")
        print(f"File: {item['filename']}")
        print(f"Content length: {len(item['markdown'])} chars")
        print(item["markdown"][:500])  # preview first 500 chars
