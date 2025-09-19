# Building Your Own API Endpoints: A Step-by-Step Guide

This guide teaches you how to create new FastAPI endpoints by understanding existing patterns and building a complete example from scratch.

## Understanding an Existing Endpoint

Let's break down the `/cells` endpoint to understand how FastAPI endpoints work:

```python
@app.get("/cells", response_model=APIResponse, tags=["Administrative"])
async def get_cells(
    province: Optional[str] = Query(None, description="Filter by province name"),
    district: Optional[str] = Query(None, description="Filter by district name"),
    sector: Optional[str] = Query(None, description="Filter by sector name"),
    limit: int = Query(50, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """Get all cells with optional filtering"""
    try:
        # 1. Get database connection
        cursor, conn = get_db_cursor()
        
        # 2. Build dynamic SQL query
        query = "SELECT * FROM cells WHERE 1=1"
        params = []
        
        # 3. Add filters based on parameters
        if province:
            query += " AND province_name ILIKE %s"
            params.append(f"%{province}%")
        if district:
            query += " AND district_name ILIKE %s"
            params.append(f"%{district}%")
        if sector:
            query += " AND sector_name ILIKE %s"
            params.append(f"%{sector}%")
            
        # 4. Add ordering and pagination
        query += " ORDER BY province_name, district_name, sector_name LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        # 5. Execute query
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # 6. Clean up database connection
        cursor.close()
        conn.close()
        
        # 7. Return standardized response
        return APIResponse(
            success=True,
            data=[dict(row) for row in results],
            count=len(results)
        )
        
    except Exception as e:
        # 8. Handle errors gracefully
        raise HTTPException(status_code=500, detail=str(e))
```

## Endpoint Anatomy Explained

### 1. **Decorator: `@app.get("/cells", ...)`**
- **HTTP Method**: `get`, `post`, `put`, `delete`
- **URL Path**: `/cells` - what users type after your domain
- **Response Model**: Tells FastAPI what structure to return
- **Tags**: Groups endpoints in documentation

### 2. **Function Definition: `async def get_cells(...)`**
- **async**: Allows the function to handle multiple requests simultaneously
- **Function name**: Should be descriptive of what it does
- **Parameters**: Define what users can customize in their requests

### 3. **Query Parameters**
```python
province: Optional[str] = Query(None, description="Filter by province name")
limit: int = Query(50, ge=1, le=1000, description="Number of results to return")
```
- **Type hints**: `str`, `int`, `Optional[str]` for validation
- **Default values**: What happens if user doesn't provide the parameter
- **Validation**: `ge=1, le=1000` means "greater or equal to 1, less or equal to 1000"
- **Documentation**: Description appears in the API docs

### 4. **Database Operations Pattern**
```python
# Always follow this pattern:
cursor, conn = get_db_cursor()  # 1. Connect
cursor.execute(query, params)   # 2. Execute
results = cursor.fetchall()     # 3. Get results
cursor.close()                  # 4. Clean up
conn.close()                    # 5. Close connection
```

### 5. **Dynamic Query Building**
```python
query = "SELECT * FROM cells WHERE 1=1"  # Base query
params = []                               # Parameters list

if province:                              # Add filters conditionally
    query += " AND province_name ILIKE %s"
    params.append(f"%{province}%")
```

### 6. **Error Handling**
```python
try:
    # Database operations here
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

### 7. **Response Formatting**
```python
return APIResponse(
    success=True,
    data=[dict(row) for row in results],  # Convert database rows to dictionaries
    count=len(results)
)
```

## Building a New Endpoint: Population Aggregation

Let's create a new endpoint that aggregates population data by administrative level.

### Step 1: Plan Your Endpoint

**Goal**: Create an endpoint that returns population totals by province, district, or sector

**Design Decisions**:
- **URL**: `GET /population/aggregate`
- **Parameters**: 
  - `level`: "province", "district", or "sector" (required)
  - `province`: Filter by specific province (optional)
  - `district`: Filter by specific district (optional)
- **Response**: Aggregated population statistics with totals

### Step 2: Create the Pydantic Model

**Why do we need a new model when we already have the `Cell` model?**

The existing `Cell` model represents **individual cells** from the database:
```python
class Cell(BaseModel):
    cell_id: str
    province_name: Optional[str]
    district_name: Optional[str]
    sector_name: Optional[str] 
    cell_name: Optional[str]
```

But our new endpoint returns **aggregated data** - totals across multiple cells. This has a completely different structure:
- **Different fields**: Instead of `cell_id`, we have `total_population`, `cell_count`, etc.
- **Different purpose**: Cell = one administrative unit, PopulationAggregate = summary statistics
- **Different data source**: Cell comes from one table, PopulationAggregate comes from complex SQL with GROUP BY

**Each endpoint response structure needs its own model!**

Add this to `src/models.py`:

```python
class PopulationAggregate(BaseModel):
    """
    Aggregated population data by administrative level.
    
    This model represents SUMMARY statistics across multiple cells,
    NOT individual cell data. That's why we need a separate model
    from the Cell model which represents individual administrative units.
    
    Used for endpoints that sum population across multiple cells
    to show totals at province, district, or sector level.
    """
    level: str                    # "province", "district", or "sector"
    name: str                     # Name of the administrative unit
    total_population: float       # Sum of general_pop across all cells
    total_children_under5: float  # Sum of children_under5 across all cells
    total_elderly_60: float       # Sum of elderly_60 across all cells
    total_youth_15_24: float      # Sum of youth_15_24 across all cells
    total_men: float              # Sum of men_2020 across all cells
    total_women: float            # Sum of women_2020 across all cells
    total_buildings: float        # Sum of building_count across all cells
    cell_count: int               # COUNT(*) - how many cells are in this group
```

**Key principle**: **One Pydantic model per unique response structure**. Even if the data comes from the same database tables, if the response format is different, you need a different model.

### Step 3: Write the Endpoint Function

Add this to your `main.py`:

```python
@app.get("/population/aggregate", response_model=APIResponse, tags=["Population"])
async def get_population_aggregate(
    level: str = Query(..., regex="^(province|district|sector)$", 
                      description="Aggregation level: province, district, or sector"),
    province: Optional[str] = Query(None, description="Filter by province name"),
    district: Optional[str] = Query(None, description="Filter by district name")
):
    """
    Get aggregated population statistics by administrative level.
    
    This endpoint demonstrates:
    - SQL GROUP BY operations for data aggregation
    - Parameter validation using regex patterns
    - Complex query building based on user input
    - Professional response formatting
    
    Examples:
    - /population/aggregate?level=province (all provinces)
    - /population/aggregate?level=district&province=Kigali (districts in Kigali)
    - /population/aggregate?level=sector&district=Gasabo (sectors in Gasabo)
    """
    try:
        cursor, conn = get_db_cursor()
        
        # Build the aggregation query based on requested level
        if level == "province":
            group_by_field = "c.province_name"
            select_field = "c.province_name as name"
        elif level == "district":
            group_by_field = "c.district_name, c.province_name"
            select_field = "CONCAT(c.district_name, ' (', c.province_name, ')') as name"
        else:  # sector
            group_by_field = "c.sector_name, c.district_name, c.province_name"
            select_field = "CONCAT(c.sector_name, ' (', c.district_name, ', ', c.province_name, ')') as name"
        
        # Base aggregation query using GROUP BY
        query = f"""
        SELECT 
            '{level}' as level,
            {select_field},
            COALESCE(SUM(p.general_pop), 0) as total_population,
            COALESCE(SUM(p.children_under5), 0) as total_children_under5,
            COALESCE(SUM(p.elderly_60), 0) as total_elderly_60,
            COALESCE(SUM(p.youth_15_24), 0) as total_youth_15_24,
            COALESCE(SUM(p.men_2020), 0) as total_men,
            COALESCE(SUM(p.women_2020), 0) as total_women,
            COALESCE(SUM(p.building_count), 0) as total_buildings,
            COUNT(*) as cell_count
        FROM cells c
        JOIN pop p ON c.cell_id = p.cell_id
        WHERE 1=1
        """
        
        params = []
        
        # Add optional filters
        if province:
            query += " AND c.province_name ILIKE %s"
            params.append(f"%{province}%")
        if district:
            query += " AND c.district_name ILIKE %s"
            params.append(f"%{district}%")
        
        # Complete the query with GROUP BY and ORDER BY
        query += f" GROUP BY {group_by_field}"
        query += " ORDER BY total_population DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return APIResponse(
            success=True,
            data=[dict(row) for row in results],
            count=len(results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 4: Test Your New Endpoint

**Test these URLs in your browser or with curl:**

1. **All provinces**: 
   ```
   GET /population/aggregate?level=province
   ```

2. **Districts in Kigali**: 
   ```
   GET /population/aggregate?level=district&province=Kigali
   ```

3. **Sectors in Gasabo district**: 
   ```
   GET /population/aggregate?level=sector&district=Gasabo
   ```

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "level": "province",
      "name": "Kigali",
      "total_population": 1132686.0,
      "total_children_under5": 145123.0,
      "total_elderly_60": 67890.0,
      "total_youth_15_24": 289456.0,
      "total_men": 556789.0,
      "total_women": 575897.0,
      "total_buildings": 234567.0,
      "cell_count": 35
    }
  ],
  "count": 1
}
```

## 🎯 Key Concepts Explained

### 1. **SQL Aggregation with GROUP BY**
```sql
SELECT 
    province_name,
    SUM(general_pop) as total_population,
    COUNT(*) as cell_count
FROM cells c
JOIN pop p ON c.cell_id = p.cell_id
GROUP BY province_name
```
- **SUM()**: Adds up values across multiple rows
- **COUNT()**: Counts number of rows in each group
- **GROUP BY**: Creates groups for aggregation
- **COALESCE()**: Handles NULL values by providing defaults

### 2. **Parameter Validation with Regex**
```python
level: str = Query(..., regex="^(province|district|sector)$")
```
- **`...`**: Parameter is required (no default)
- **regex**: Only allows specific values
- **Automatic validation**: FastAPI rejects invalid values

### 3. **Dynamic Query Building**
```python
if level == "province":
    group_by_field = "c.province_name"
    select_field = "c.province_name as name"
elif level == "district":
    group_by_field = "c.district_name, c.province_name"
    select_field = "CONCAT(c.district_name, ' (', c.province_name, ')') as name"
```
- **Conditional logic**: Different SQL for different parameters
- **String formatting**: Build complex queries programmatically
- **Field aliasing**: Use `as name` for consistent response structure

### 4. **JOIN Operations**
```sql
FROM cells c
JOIN pop p ON c.cell_id = p.cell_id
```
- **INNER JOIN**: Only include cells that have population data
- **Table aliases**: `c` for cells, `p` for pop (cleaner code)
- **ON clause**: Specifies how tables are related

## 📝 Best Practices Checklist

When building endpoints, always:

- [ ] **Plan first**: URL structure, parameters, response format
- [ ] **Create Pydantic models**: Define response structure before coding
- [ ] **Validate inputs**: Use Query() parameters with proper constraints
- [ ] **Handle errors**: Wrap database operations in try/catch blocks
- [ ] **Clean up resources**: Always close database connections
- [ ] **Document thoroughly**: Use docstrings and parameter descriptions
- [ ] **Follow patterns**: Use consistent response formats (APIResponse)
- [ ] **Test edge cases**: Empty results, invalid parameters, database errors
- [ ] **Use meaningful names**: Functions and variables should be self-explanatory
- [ ] **Add to API docs**: Use tags to organize endpoints logically

## 🚀 Practice Exercises

Try building these endpoints to practice your skills:

### Exercise 1: Population Density Calculator
**Goal**: Calculate population per building for each cell
```
GET /population/density?min_density=50&province=Kigali
```
**Formula**: `general_pop / building_count`
**Challenge**: Handle division by zero when building_count is 0

### Exercise 2: NTL Brightness Rankings
**Goal**: Rank cells by their night-time light intensity
```
GET /ntl/rankings?year=2023&top=10&province=Kigali
```
**Order by**: `ntl_mean DESC`
**Challenge**: Allow sorting by different NTL metrics (mean, max, sum)

### Exercise 3: Time Series Trends
**Goal**: Show how NTL values change over time for one cell
```
GET /ntl/trends/{cell_id}?start_year=2020&end_year=2023
```
**Data**: Monthly and annual trends for specific cell
**Challenge**: Combine data from both ntl_annual and ntl_monthly tables

### Exercise 4: Population-NTL Correlation
**Goal**: Find relationship between population and lighting
```
GET /analytics/population-light-correlation?level=district
```
**Analysis**: Calculate correlation coefficient between population and NTL mean
**Challenge**: Implement statistical calculations in SQL or Python

## 🔍 Advanced Patterns

### 1. **Path Parameters vs Query Parameters**
```python
# Path parameter (part of URL)
@app.get("/cells/{cell_id}")
async def get_cell(cell_id: str):

# Query parameter (after ? in URL)
@app.get("/cells")
async def get_cells(province: Optional[str] = Query(None)):
```

### 2. **Multiple Response Models**
```python
from typing import Union

@app.get("/data")
async def get_data() -> Union[APIResponse, ErrorResponse]:
    # Can return different response types
```

### 3. **Request Body for POST Endpoints**
```python
@app.post("/cells")
async def create_cell(cell_data: Cell):
    # cell_data automatically validated against Cell model
```

### 4. **Async Database Operations**
```python
import asyncpg

async def get_data_async():
    async with asyncpg.connect(DATABASE_URL) as conn:
        results = await conn.fetch("SELECT * FROM cells")
    return results
```

## 🎓 Next Steps

1. **Master the basics**: Build the practice exercises above
2. **Add authentication**: Learn about API keys and JWT tokens
3. **Implement caching**: Use Redis for faster repeated queries
4. **Add testing**: Write unit tests for your endpoints
5. **Deploy your API**: Put it on a cloud platform
6. **Monitor performance**: Add logging and metrics
7. **Version your API**: Learn about API versioning strategies

Remember: Great APIs are built incrementally. Start simple, test thoroughly, then add complexity!