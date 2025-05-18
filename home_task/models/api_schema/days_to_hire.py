from typing import Optional
from pydantic import BaseModel, Field

class DaysToHireResponse(BaseModel):
    standard_job_id: str = Field(..., description="The standard job ID")
    country_code: Optional[str] = Field(None, description="Country code for the statistics. None indicates global statistics")
    min_days: float = Field(..., description="Minimum days to hire", ge=0)
    avg_days: float = Field(..., description="Average days to hire", ge=0)
    max_days: float = Field(..., description="Maximum days to hire", ge=0)
    job_postings_number: int = Field(..., description="Number of job postings analyzed", ge=1)

    class Config:
        from_attributes = True 