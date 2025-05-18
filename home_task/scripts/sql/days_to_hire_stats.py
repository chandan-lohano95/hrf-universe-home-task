"""SQL queries for days to hire statistics calculations."""

from sqlalchemy import text

CALCULATE_STATS_QUERY = text("""
    WITH percentiles AS (
        SELECT 
            PERCENTILE_CONT(0.1) WITHIN GROUP (ORDER BY days_to_hire) as min_percentile,
            PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY days_to_hire) as max_percentile,
            COUNT(*) as total_count
        FROM job_posting
        WHERE standard_job_id = :standard_job_id
        AND (
            (:country_code IS NULL AND country_code IS NULL)
            OR country_code = :country_code
        )
        AND days_to_hire IS NOT NULL
        AND days_to_hire > 0
    ),
    filtered_data AS (
        SELECT days_to_hire
        FROM job_posting j, percentiles p
        WHERE j.standard_job_id = :standard_job_id
        AND (
            (:country_code IS NULL AND j.country_code IS NULL)
            OR j.country_code = :country_code
        )
        AND j.days_to_hire BETWEEN p.min_percentile AND p.max_percentile
    )
    SELECT 
        p.min_percentile as min_days,
        p.max_percentile as max_days,
        p.total_count as total_count,
        COUNT(f.days_to_hire) as filtered_count,
        COALESCE(AVG(f.days_to_hire), 0.0) as avg_days
    FROM percentiles p
    LEFT JOIN filtered_data f ON true
    GROUP BY p.min_percentile, p.max_percentile, p.total_count
""") 