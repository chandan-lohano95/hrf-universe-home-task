from dataclasses import dataclass
from typing import Optional
from sqlalchemy import Column, Integer, String, Table, Float

from home_task.models.db_schema import Model, mapper_registry

@mapper_registry.mapped
@dataclass
class DaysToHireStats(Model):
    __table__ = Table(
        "days_to_hire_stats",
        mapper_registry.metadata,
        Column("id", Integer, nullable=False, primary_key=True, autoincrement=True),
        Column("standard_job_id", String, nullable=False),
        Column("country_code", String, nullable=True),  # NULL means global statistics
        Column("avg_days_to_hire", Float, nullable=False),
        Column("min_days_to_hire", Float, nullable=False),
        Column("max_days_to_hire", Float, nullable=False),
        Column("job_postings_count", Integer, nullable=False),
    )

    standard_job_id: str
    avg_days_to_hire: float
    min_days_to_hire: float
    max_days_to_hire: float
    job_postings_count: int
    id: Optional[int] = None
    country_code: Optional[str] = None 