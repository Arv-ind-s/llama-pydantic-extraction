"""
PSC Question Extraction Pipeline — Entry Point.

Orchestrates the full extraction flow:
    1. Scan data/input/new/ for PDF files
    2. Parse each PDF via LlamaCloud (markdown + images)
    3. Extract structured questions via LLM
    4. Validate against Pydantic schema
    5. Save validated JSON to data/output/

Usage:
    python main.py
"""
import asyncio
import sys
from datetime import datetime

from llama_cloud import AsyncLlamaCloud

from config.settings import settings
from src.parsers.llama_parser import parse_all_pdfs
from src.extractors.question_extractor import extract_and_save
from src.utils.logger import get_logger
from src.utils.file_utils import ensure_dir

logger = get_logger(__name__)


async def run_pipeline():
    """
    Main pipeline: parse → extract → validate → save.

    Returns:
        Number of successfully processed PDFs.
    """
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("PSC Question Extraction Pipeline — Starting")
    logger.info(f"Input:  {settings.input_dir / 'new'}")
    logger.info(f"Output: {settings.output_dir}")
    logger.info("=" * 60)

    # Ensure output directory exists
    ensure_dir(settings.output_dir)

    # Step 1: Parse all PDFs (upload to LlamaCloud, get markdown + images)
    logger.info("[1/2] Parsing PDFs...")
    parsed_results = await parse_all_pdfs()

    if not parsed_results:
        logger.warning("No PDFs were parsed. Nothing to extract.")
        return 0

    logger.info(f"Parsed {len(parsed_results)} PDF(s)")

    # Step 2: Extract, validate, and save each parsed result
    logger.info("[2/2] Extracting questions...")
    client = AsyncLlamaCloud(api_key=settings.llama_cloud_api_key)

    success_count = 0
    # Process extractions in batches for concurrency
    for i in range(0, len(parsed_results), settings.batch_size):
        batch = parsed_results[i : i + settings.batch_size]
        logger.info(f"Extracting batch {i//settings.batch_size + 1}: {[p['filename'] for p in batch]}")
        
        tasks = [extract_and_save(client, parsed) for parsed in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for parsed, result in zip(batch, results):
            if isinstance(result, Exception):
                logger.error(f"✗ Failed {parsed['filename']}: {result}")
            elif result:
                logger.info(f"✓ Saved → {result}")
                success_count += 1
            else:
                logger.warning(f"✗ No output for {parsed['filename']}")

    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info("=" * 60)
    logger.info("Pipeline Complete")
    logger.info(f"  Processed: {success_count}/{len(parsed_results)} PDFs succeeded")
    logger.info(f"  Time:      {elapsed:.1f}s")
    logger.info(f"  Output:    {settings.output_dir}")
    logger.info("=" * 60)

    return success_count


def main():
    """Entry point — runs the async pipeline."""
    try:
        result = asyncio.run(run_pipeline())
        sys.exit(0 if result > 0 else 1)
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
