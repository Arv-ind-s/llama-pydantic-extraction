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


async def reprocess_batch(client: AsyncLlamaCloud, filenames: list):
    """
    Process a batch of files concurrently.
    """
    tasks = []
    for filename in filenames:
        pdf_path = NEW_PDF_DIR / filename

        if not pdf_path.exists():
            logger.error(f"File not found: {pdf_path}")
            continue

        logger.info(f"Reprocessing: {filename}")
        
        async def process_file(fname, path):
            try:
                parsed = await parse_single_pdf(client, path)
                output_path = await extract_and_save(client, parsed)
                return fname, output_path
            except Exception as e:
                logger.error(f"✗ Failed to reprocess {fname}: {e}")
                return fname, None

        tasks.append(process_file(filename, pdf_path))

    results = await asyncio.gather(*tasks)
    return results


async def reprocess(filenames: list):
    """
    Re-run the pipeline for specific PDF files in batches.
    """
    client = AsyncLlamaCloud(api_key=settings.llama_cloud_api_key)

    success_count = 0
    total = len(filenames)

    for i in range(0, total, settings.batch_size):
        batch = filenames[i : i + settings.batch_size]
        logger.info(f"Reprocessing batch {i//settings.batch_size + 1}: {batch}")
        
        results = await reprocess_batch(client, batch)
        
        for fname, output_path in results:
            if output_path:
                logger.info(f"✓ Saved → {output_path}")
                success_count += 1
            else:
                logger.warning(f"✗ Extraction failed for {fname}")

    logger.info(f"Reprocessing complete: {success_count}/{total} succeeded")


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
