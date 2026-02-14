"""
Reprocess specific PDFs that failed during a previous pipeline run.

Accepts one or more PDF filenames and re-runs the parse → extract → save
pipeline for just those files.

Usage:
    python scripts/reprocess.py file1.pdf file2.pdf
    python scripts/reprocess.py --all   # reprocess all PDFs in data/input/new/
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from llama_cloud import AsyncLlamaCloud

from config.settings import settings
from src.parsers.llama_parser import parse_single_pdf, NEW_PDF_DIR
from src.extractors.question_extractor import extract_and_save
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def reprocess(filenames: list):
    """
    Re-run the pipeline for specific PDF files.

    Args:
        filenames: List of PDF filenames (just the name, not full path).
    """
    client = AsyncLlamaCloud(api_key=settings.llama_cloud_api_key)

    for filename in filenames:
        pdf_path = NEW_PDF_DIR / filename

        if not pdf_path.exists():
            logger.error(f"File not found: {pdf_path}")
            continue

        logger.info(f"Reprocessing: {filename}")

        try:
            # Parse
            parsed = await parse_single_pdf(client, pdf_path)

            # Extract and save
            output_path = await extract_and_save(client, parsed)

            if output_path:
                logger.info(f"✓ Saved → {output_path}")
            else:
                logger.warning(f"✗ Extraction failed for {filename}")

        except Exception as e:
            logger.error(f"✗ Failed to reprocess {filename}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Reprocess specific PDFs")
    parser.add_argument("files", nargs="*", help="PDF filenames to reprocess")
    parser.add_argument("--all", action="store_true", help="Reprocess all PDFs in input/new/")
    args = parser.parse_args()

    if args.all:
        # Get all PDF filenames from the input directory
        filenames = [f.name for f in sorted(NEW_PDF_DIR.glob("*.pdf"))]
    elif args.files:
        filenames = args.files
    else:
        parser.print_help()
        sys.exit(1)

    if not filenames:
        print("No PDF files found to reprocess.")
        sys.exit(0)

    print(f"Reprocessing {len(filenames)} file(s)...")
    asyncio.run(reprocess(filenames))


if __name__ == "__main__":
    main()
