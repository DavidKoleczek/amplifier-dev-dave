# Copyright (c) Microsoft. All rights reserved.

import asyncio
import sys
from pathlib import Path

import click
from eval_recipes.benchmarking.semantic_test import semantic_test
from eval_recipes.benchmarking.test_utils import get_instructions_from_file_or_default
from eval_recipes.benchmarking.test_utils import get_test_id_from_env_or_default
from eval_recipes.benchmarking.test_utils import write_test_result
from loguru import logger

STEPS_VALIDATE = """1. Check if nfl_standings_2024.csv exists and contains NFL regular season standings data
2. Check if nfl_report.md exists and is a well-formatted markdown report
3. Verify the report has an introduction section
4. Verify the report has an appendix with regular season standings in a markdown table format
5. Check if the report has three team sections: Patriots, Seahawks, and Eagles
6. For each team section, verify it contains:
   - Season game results
   - Analysis of two inflection points in their season
   - References to or information from news articles about those inflection points
"""

RUBRIC_VALIDATE = {
    "csv_file_created": "str - (10 points) nfl_standings_2024.csv file exists with NFL standings data",
    "report_file_created": "str - (10 points) nfl_report.md file exists and is valid markdown",
    "report_introduction": "str - (10 points) Report has a proper introduction section",
    "standings_table": "str - (10 points) Report has appendix with standings in markdown table format",
    "team_sections_present": "str - (15 points) Report has sections for Patriots, Seahawks, and Eagles",
    "game_results": "str - (15 points) Each team section includes their season game results",
    "inflection_analysis": "str - (20 points) Each team section analyzes two inflection points in their season",
    "news_articles_cited": "str - (10 points) Analysis is grounded in information from news articles",
    "score": "float - Score between 0 and 100 based on the above criteria. Sum the points earned from each criterion.",
}


@click.command()
@click.option(
    "--test-id",
    default=lambda: get_test_id_from_env_or_default("dev"),
    help="Test ID for result file naming (defaults to EVAL_RECIPES_TEST_ID env var)",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=lambda: Path(__file__).parents[0],
    help="Directory to write result file",
)
@click.option(
    "--instructions-file",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to instructions file (defaults to ./instructions.txt in working directory)",
)
def main(test_id: str, output_dir: Path, instructions_file: Path | None) -> int:
    """Test script for nfl_season_analysis task."""
    return asyncio.run(run_test(test_id, output_dir, instructions_file))


async def run_test(test_id: str, output_dir: Path, instructions_file: Path | None) -> int:
    instructions = get_instructions_from_file_or_default(instructions_file=instructions_file)

    try:
        logger.info("Running semantic test: NFL season analysis validation...")
        result = await semantic_test(
            steps=STEPS_VALIDATE,
            rubric=RUBRIC_VALIDATE,
            context=instructions,
            working_dir=Path("/project"),
        )

        metadata = {
            "instructions": instructions,
            "semantic_test_result": {
                "score": result.score,
                "details": result.metadata,
            },
        }

        write_test_result(output_dir, test_id, result.score, metadata)
        logger.info(f"Test completed with score: {result.score:.1f}/100")
        return 0

    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        metadata = {
            "instructions": instructions,
            "error": str(e),
        }
        write_test_result(output_dir, test_id, 0, metadata)
        return 0


if __name__ == "__main__":
    sys.exit(main())
