This is a task to check your skills in Python and SQL.
It is a simplified version of a real task in our project.

Create a public fork of this repository and send us a link to your fork when you are done.

# Table of Contents
- [Task Overview](#task-overview)
- [Solution Approach](#solution-approach)
  - [Database Schema](#database-schema)
  - [Design Decisions](#design-decisions)
- [Running the Application](#running-the-application)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the CLI Script](#running-the-cli-script)
  - [Running the API Server](#running-the-api-server)
- [Testing](#testing)

# Task Overview

We have millions of job postings crawled from the internet and want to calculate some statistics about days to hire.

Job posting structure:

```python
@dataclass
class JobPosting:
    id: str
    title: str
    standard_job_id: str
    country_code: Optional[str] = None
    days_to_hire: Optional[int] = None
```

- `standard_job_id` -- all job postings are assigned to a standard job. It is a job title normalized to a common form,
  e.g. "Software Engineer" and "Software Developer" are both assigned to "Software Engineer".
- `country_code` -- country code in ISO 3166-1 alpha-2 format. 
  It can be `None` if we can't determine the country.
- `days_to_hire` -- a number of days between posting date and hire date. 
  It can be `None` if a job posting is not hired yet.

## Requirements

### 1. Create a table in the database to store "days to hire" statistics. 

- Statistics should be per country(also global for the world) and per standard job.
- It should contain average, minimum, and maximum days to hire.
- Also, it should contain a number of job postings used to calculate the average. 
We use this value to measure statistics quality. If the number of job postings is small, values can be inaccurate.

You can add SQLAlchemy model to `home_task.models` module and generate a migration with:

    alembic revision --autogenerate -m "<description>"

### 2. Write a CLI script to calculate "days to hire" statistics and store it in a created table.

`days_to_hire` can contain potentially invalid values, because it is quite difficult to gather this information.
For example, 1 day in most cases means that job posting was closed and reopened without real hiring.
Large values can be caused by incorrect parsing of dates. 
So we want to cut lowest and highest percentiles of `days_to_hire` before calculating average.

- Minimum days to hire is 10 percentile.
- Maximum days to hire is 90 percentile.
- Average days to hire is an average of **remaining values after cutting 10 and 90 percentiles**.
- Number of job postings is a number of rows used to calculate an average.
- Do not save resulted row if a number of job postings is less than 5. 
  Allow passing this threshold as a parameter.
- For each country and standard job create a separate row in a table.
- Also, create a row for world per standard job. 
  Job postings with `country_code` equal to `NULL` should be included in this calculation.
- Overwrite existing rows in the table. We need only the latest statistics.

### 3. Create REST API with one endpoint to get "days to hire" statistics.

- Endpoint should accept `standard_job_id` and `country_code` as request parameters.
- If `country_code` is not specified, return statistics for the world.

Response example:

    {
        "standard_job_id": "5affc1b4-1d9f-4dec-b404-876f3d9977a0",
        "country_code": "DE",
        "min_days": 11.0,
        "avg_days": 50.5,
        "max_days": 80.9,
        "job_postings_number": 100,
    }

# Solution Approach

## Database Schema
- Created a `days_to_hire_stats` table using SQLAlchemy with the following columns:
  - `id` (Integer, primary key)
  - `standard_job_id` (String)
  - `country_code` (String, nullable)
  - `avg_days_to_hire` (Float)
  - `min_days_to_hire` (Float)
  - `max_days_to_hire` (Float)
  - `job_postings_count` (Integer)

## Design Decisions

### SQL-based Processing
The solution uses SQL for data processing instead of loading data into memory for several reasons:

1. **Memory Efficiency**
   - With millions of rows, loading all data into memory would be impractical and could cause out-of-memory errors
   - SQL allows processing data in the database where it's already stored, eliminating the need for large memory allocations
   - Data is processed in groups by standard_job_id and country_code, reducing memory requirements

2. **Data Safety**
   - SQL transactions ensure data consistency even if the process fails
   - If the script crashes, the database remains in a consistent state
   - No risk of partial updates or corrupted data

3. **Performance**
   - Database engines are optimized for large-scale data processing
   - Percentile calculations are performed efficiently using SQL's built-in functions
   - Reduces network overhead by processing data where it's stored
   - Each job-country combination is processed independently, allowing for parallel processing if needed

4. **Real-time Data Handling**
   - SQL queries always work with the latest data
   - No need to worry about data changes during processing
   - Queries are atomic and consistent

## CLI Script
- Implemented a CLI script `calculate_days_to_hire_stats.py` that:
  - Uses SQL for efficient data processing with percentiles
  - Handles transactions safely
  - Processes data in chunks to handle large datasets
  - Includes error handling and logging
  - Supports configurable minimum postings threshold
  - Calculates both country-specific and global statistics

## REST API
- Built using FastAPI with the following endpoints:
  - `GET /api/v1/health` - Health check endpoint
  - `GET /api/v1/days-to-hire` - Get days to hire statistics
    - Query parameters:
      - `standard_job_id` (required): The standard job ID
      - `country_code` (optional): Country code for country-specific statistics

# Running the Application

## Prerequisites
- Python 3.10 or higher
- Docker and Docker Compose
- Poetry (Python package manager)

## Installation

1. Create and activate a virtual environment:
    ```bash
    python3 -m venv venv
    . venv/bin/activate
    ```

2. Install dependencies:
    ```bash
    pip install poetry
    poetry install
    ```

3. Start the database:
    ```bash
    docker-compose up -d
    ```

4. Run database migrations:
    ```bash
    docker cp migrations/data/ hrf_universe_postgres:/tmp
    poetry run alembic upgrade head
    ```

## Running the CLI Script

Calculate days to hire statistics:
```bash
poetry run python -m home_task.scripts.calculate_days_to_hire_stats [--min-postings MIN_POSTINGS] [--log-level LOG_LEVEL]
```

Options:
- `--min-postings`: Minimum number of job postings required (default: 5)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) (default: INFO)

## Running the API Server

Start the FastAPI server:

For development (with auto-reload):
```bash
poetry run uvicorn home_task.app:app --reload --host 0.0.0.0 --port 8000
```

For production:
```bash
poetry run uvicorn home_task.app:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

# Testing

Run the test suite:
```bash
poetry run pytest
```

The test suite includes:
- API endpoint tests
- CLI script tests
- Database model tests

Test coverage includes:
- Health check endpoint
- Days to hire statistics endpoint
- Error handling
- Database operations
- CLI script functionality
