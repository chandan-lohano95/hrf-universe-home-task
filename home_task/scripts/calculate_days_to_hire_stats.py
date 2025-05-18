#!/usr/bin/env python3
"""
Script to calculate and store days to hire statistics.

This script calculates statistics for days to hire values, removing outliers
using percentiles, and stores the results in the database. It processes data
for each standard job ID and country combination, as well as global statistics.

The script is designed to handle large datasets by:
- Using SQL for efficient data processing
- Using transactions for data safety
- Handling errors gracefully
"""

import argparse
from dataclasses import dataclass
from typing import List, Optional, Tuple, Set, Dict
from contextlib import contextmanager

from sqlalchemy import select, text, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from home_task.db import get_session
from home_task.models.db_schema.days_to_hire import DaysToHireStats
from home_task.models.db_schema.job_posting import JobPosting
from home_task.scripts.sql.days_to_hire_stats import CALCULATE_STATS_QUERY
from home_task.utils.logging_config import setup_logging

# Configure logging
logger = setup_logging()

@dataclass
class DaysToHireStatistics:
    """Container for days to hire statistics."""
    min_days: float
    max_days: float
    avg_days: float
    filtered_count: int
    total_count: int


@dataclass
class ProcessingResult:
    """Container for processing results."""
    success: bool
    error_message: Optional[str] = None
    stats: Optional[DaysToHireStatistics] = None


class DaysToHireStatsCalculator:
    """Calculator for days to hire statistics.
    
    This class handles the calculation and storage of days to hire statistics,
    including data validation and error handling.
    """
    
    def __init__(
        self,
        min_postings: int = 5,
        log_level: str = 'INFO'
    ):
        """Initialize the calculator.
        
        Args:
            min_postings: Minimum number of job postings required
            log_level: Logging level
        """
        self.min_postings = min_postings
        logger.setLevel(log_level)
        self.session = None
        self.stats_count = 0
        self.error_count = 0
        self.failed_combinations: Dict[str, List[str]] = {}  # job_id -> list of country codes
    
    def __enter__(self):
        """Context manager entry."""
        self.session = get_session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.session:
            self.session.close()
            logger.info("Database session closed")
    
    @contextmanager
    def safe_transaction(self):
        """Context manager for safe database transactions.
        
        Ensures that database operations are either fully completed or fully rolled back.
        """
        try:
            yield
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.error(f"Transaction failed: {str(e)}", exc_info=True)
            raise
    
    def calculate_stats_for_group(
        self,
        standard_job_id: str,
        country_code: Optional[str]
    ) -> ProcessingResult:
        """Calculate statistics for a specific standard job and country combination using SQL.
        
        Args:
            standard_job_id: ID of the standard job
            country_code: Country code (None for global statistics)
        
        Returns:
            ProcessingResult containing success status and either statistics or error message
        """
        try:
            result = self.session.execute(
                CALCULATE_STATS_QUERY,
                {
                    "standard_job_id": standard_job_id,
                    "country_code": country_code
                }
            ).first()
            
            if not result or result.filtered_count < self.min_postings:
                message = (
                    f"Not enough postings for {standard_job_id} in {country_code or 'global'}: "
                    f"{result.filtered_count if result else 0} < {self.min_postings}"
                )
                logger.debug(message)
                return ProcessingResult(success=False, error_message=message)
            
            return ProcessingResult(
                success=True,
                stats=DaysToHireStatistics(
                    min_days=float(result.min_days),
                    max_days=float(result.max_days),
                    avg_days=float(result.avg_days),
                    filtered_count=result.filtered_count,
                    total_count=result.total_count
                )
            )
            
        except SQLAlchemyError as e:
            error_msg = f"Database error: {str(e)}"
            logger.error(
                f"Error calculating statistics for {standard_job_id} in {country_code or 'global'}: {error_msg}",
                exc_info=True
            )
            return ProcessingResult(success=False, error_message=error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(
                f"Error calculating statistics for {standard_job_id} in {country_code or 'global'}: {error_msg}",
                exc_info=True
            )
            return ProcessingResult(success=False, error_message=error_msg)
    
    def get_unique_job_ids(self) -> Set[str]:
        """Get all unique standard job IDs from the database.
        
        Returns:
            Set of unique standard job IDs
        """
        try:
            return set(self.session.execute(
                select(JobPosting.standard_job_id).distinct()
            ).scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting unique job IDs: {str(e)}", exc_info=True)
            raise
    
    def get_unique_country_codes(self) -> Set[Optional[str]]:
        """Get all unique country codes from the database.
        
        Returns:
            Set of unique country codes (including None)
        """
        try:
            return set(self.session.execute(
                select(JobPosting.country_code).distinct()
            ).scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting unique country codes: {str(e)}", exc_info=True)
            raise
    
    def save_statistics(
        self,
        standard_job_id: str,
        country_code: Optional[str],
        stats: DaysToHireStatistics
    ) -> None:
        """Save statistics to the database.
        
        Args:
            standard_job_id: ID of the standard job
            country_code: Country code (None for global statistics)
            stats: Statistics to save
        """
        try:
            db_stats = DaysToHireStats(
                standard_job_id=standard_job_id,
                country_code=country_code,
                min_days_to_hire=stats.min_days,
                max_days_to_hire=stats.max_days,
                avg_days_to_hire=stats.avg_days,
                job_postings_count=stats.filtered_count
            )
            self.session.add(db_stats)
        except SQLAlchemyError as e:
            logger.error(
                f"Error saving statistics for {standard_job_id} in {country_code or 'global'}: {str(e)}",
                exc_info=True
            )
            raise
    
    def log_statistics(
        self,
        standard_job_id: str,
        country_code: Optional[str],
        stats: DaysToHireStatistics
    ) -> None:
        """Log statistics to the console.
        
        Args:
            standard_job_id: ID of the standard job
            country_code: Country code (None for global statistics)
            stats: Statistics to log
        """
        location = f"{standard_job_id} in {country_code}" if country_code else f"{standard_job_id} (global)"
        logger.info(
            f"Statistics for {location}: "
            f"avg={stats.avg_days:.1f}, min={stats.min_days:.1f}, "
            f"max={stats.max_days:.1f}, count={stats.filtered_count}"
        )
    
    def clear_existing_statistics(self) -> None:
        """Clear existing statistics from the database."""
        with self.safe_transaction():
            self.session.execute(DaysToHireStats.__table__.delete())
            logger.info("Deleted existing statistics")
    
    def process_job_and_country(
        self,
        standard_job_id: str,
        country_code: Optional[str]
    ) -> None:
        """Process statistics for a specific job and country combination.
        
        Args:
            standard_job_id: ID of the standard job
            country_code: Country code (None for global statistics)
        """
        result = self.calculate_stats_for_group(standard_job_id, country_code)
        
        if result.success and result.stats:
            try:
                self.log_statistics(standard_job_id, country_code, result.stats)
                with self.safe_transaction():
                    self.save_statistics(standard_job_id, country_code, result.stats)
                self.stats_count += 1
            except Exception as e:
                self._record_failure(standard_job_id, country_code, str(e))
        else:
            self._record_failure(standard_job_id, country_code, result.error_message)
    
    def _record_failure(
        self,
        standard_job_id: str,
        country_code: Optional[str],
        error_message: str
    ) -> None:
        """Record a failed calculation.
        
        Args:
            standard_job_id: ID of the standard job
            country_code: Country code (None for global statistics)
            error_message: Error message describing the failure
        """
        self.error_count += 1
        if standard_job_id not in self.failed_combinations:
            self.failed_combinations[standard_job_id] = []
        self.failed_combinations[standard_job_id].append(country_code or 'global')
        logger.error(
            f"Failed to process {standard_job_id} in {country_code or 'global'}: {error_message}"
        )
    
    def run(self) -> None:
        """Run the statistics calculation process."""
        logger.info("Starting days to hire statistics calculation")
        logger.info(f"Minimum postings threshold: {self.min_postings}")

        # Get unique identifiers
        standard_jobs = self.get_unique_job_ids()
        countries = self.get_unique_country_codes()
        logger.info(f"Found {len(standard_jobs)} unique standard job IDs")
        logger.info(f"Found {len(countries)} unique country codes")
        
        # Clear existing statistics
        self.clear_existing_statistics()
        
        # Calculate statistics for each standard job and country combination
        for standard_job_id in standard_jobs:
            logger.debug(f"Processing standard job ID: {standard_job_id}")
            
            # Calculate global statistics (including NULL country_code)
            self.process_job_and_country(standard_job_id, None)
            
            # Calculate statistics for each country
            for country_code in countries:
                if country_code is not None:  # Skip NULL as it's handled in global stats
                    self.process_job_and_country(standard_job_id, country_code)
        
        # Log final results
        logger.info(f"Successfully saved {self.stats_count} statistics records to database")
        if self.error_count > 0:
            logger.warning(f"Encountered {self.error_count} errors during processing")
            logger.warning("Failed combinations:")
            for job_id, country_codes in self.failed_combinations.items():
                logger.warning(f"  {job_id}: {', '.join(country_codes)}")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description='Calculate days to hire statistics')
    parser.add_argument(
        '--min-postings',
        type=int,
        default=5,
        help='Minimum number of job postings required to calculate statistics'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Set the logging level'
    )
    return parser.parse_args()


def main() -> None:
    """Main function to calculate and store days to hire statistics."""
    args = parse_args()
    
    try:
        with DaysToHireStatsCalculator(
            min_postings=args.min_postings,
            log_level=args.log_level
        ) as calculator:
            calculator.run()
    except Exception as e:
        logger.error(f"Fatal error occurred: {str(e)}", exc_info=True)
        raise


if __name__ == '__main__':
    main() 