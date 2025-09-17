# Rwanda Night-Time Lights API

A FastAPI tutorial project demonstrating how to build a REST API for serving Rwanda's night-time lights and demographic data.

## Project Structure

```
rwanda-ntl-api/
├── main.py              # Main FastAPI application entry point
├── src/
│   ├── __init__.py      # Makes src a Python package
│   ├── database.py      # Database connection and utilities
│   └── models.py        # Pydantic data models for API responses
├── .env                 # Environment variables (database credentials)
├── .gitignore          # Git ignore file
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Module Documentation

### `main.py` - FastAPI Application Entry Point

The main application file that defines all API endpoints and starts the FastAPI server.

**Key Components:**

- **FastAPI App Instance**: Creates the main application with metadata
- **Health Check Endpoints**: Basic endpoints to verify API and database connectivity
- **CRUD Endpoints**: Full Create, Read, Update, Delete operations for each data type
- **Analytics Endpoints**: Complex queries for data analysis and insights

**Selected Functions Defining Endpoints:**

```python
# Health check endpoints
@app.get("/")                    # Basic API status
@app.get("/health")              # Database connectivity check

# Administrative data endpoints
@app.get("/cells")               # Get all administrative cells with filtering
@app.get("/cells/{cell_id}")     # Get specific cell by ID

# Population data endpoints
@app.get("/population")          # Get population data with filtering options
@app.get("/population/{cell_id}") # Get population for specific cell

```

### `src/database.py` - Database Connection Module

Handles PostgreSQL database connections using psycopg2 with connection management utilities.

**Key Functions:**

```python
def get_db_cursor():
    """
    Creates a database connection and returns cursor with RealDictCursor.
    
    Returns:
        tuple: (cursor, connection) - Use cursor for queries, connection for commit/rollback
        
    Usage:
        cursor, conn = get_db_cursor()
        cursor.execute("SELECT * FROM table")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
    """
```

### `src/models.py` - Pydantic Data Models

Defines data structures using Pydantic for request/response validation and serialization.

**Why Do Pydantic Models Need to Match Database Tables?**

The Pydantic models serve as a **bridge between your database and your API**:

1. **Data Structure Consistency**: 
   - Database returns rows with specific columns (cell_id, province_name, etc.)
   - Pydantic models define the exact same structure in Python
   - This ensures data integrity from database → API → client

2. **Type Safety**:
   - Database column types (TEXT, INTEGER, REAL) map to Python types (str, int, float)
   - Pydantic validates that database data matches expected types
   - Catches data inconsistencies before they reach the API user

3. **Automatic Serialization**:
   ```python
   # Database returns: ('RW001', 'Kigali', 'Gasabo', 'Kimironko', 'Biryogo')
   # Pydantic converts to: {"cell_id": "RW001", "province_name": "Kigali", ...}
   # API returns clean JSON instead of raw database tuples
   ```

4. **Documentation Generation**:
   - API documentation shows exactly what data structure users will receive
   - Matches the actual database schema, so documentation is always accurate
   - Users know what fields are available and their data types

5. **Validation**:
   - Ensures all data returned by API endpoints is properly formatted
   - Catches cases where database might have NULL values or unexpected types
   - Provides clear error messages if data doesn't match expected structure

**What is Pydantic?**

Pydantic is a Python library that provides data validation and settings management using Python type hints. It automatically validates data types, converts between formats, and generates JSON schemas - making it perfect for API development.

**How Pydantic + FastAPI Creates Automatic Documentation:**

When you define Pydantic models and use them in FastAPI endpoints, magic happens:

1. **Type Hints → Schema**: Pydantic converts your Python classes into JSON schemas
2. **Schema → OpenAPI**: FastAPI uses these schemas to generate OpenAPI specifications
3. **OpenAPI → Docs**: The interactive documentation at `/docs` is automatically created
4. **Validation**: All incoming requests are automatically validated against your models
5. **Serialization**: Response data is automatically converted to JSON format



## API Endpoints Overview

### Health & Status
- `GET /` - Basic API health check
- `GET /health` - Database connectivity verification

### Administrative (Cells) Data
- `GET /cells` - List all administrative cells
  - **Query Parameters**: `province`, `district`, `sector`, `limit`, `offset`
- `GET /cells/{cell_id}` - Get specific cell details

### Population Data
- `GET /population` - Population data with filtering
  - **Query Parameters**: `province`, `district`, `min_population`, `max_population`, `limit`, `offset`
- `GET /population/{cell_id}` - Population data for specific cell

### Night-Time Lights Data
- `GET /ntl/annual` - Annual NTL statistics
  - **Query Parameters**: `year`, `province`, `district`, `min_mean`, `max_mean`, `limit`, `offset`
- `GET /ntl/annual/{cell_id}` - Annual NTL data for specific cell
- `GET /ntl/monthly` - Monthly NTL statistics
  - **Query Parameters**: `year`, `month`, `start_date`, `end_date`, `province`, `limit`, `offset`

### Analytics
- `GET /analytics/population-summary` - Population statistics by province
- `GET /analytics/ntl-trends` - NTL trends over time with optional province filtering


## Getting Started

See [SETUP.md](SETUP.md) for detailed installation and setup instructions.

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)
