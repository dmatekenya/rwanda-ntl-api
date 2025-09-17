import sys, os

from fastapi import FastAPI, HTTPException, Query, Path
from typing import Optional, List
import psycopg2.extras
from datetime import date

# Debug the path
current_file = __file__
current_dir = os.path.dirname(__file__)
src_path = os.path.join(os.path.dirname(__file__), 'src')

print(f"Current file: {current_file}")
print(f"Current directory: {current_dir}")
print(f"Trying to add to path: {src_path}")
print(f"Does src directory exist? {os.path.exists(src_path)}")

sys.path.append(src_path)
from database import get_db_cursor
from models import Cell, Population, NTLAnnual, NTLMonthly, APIResponse, ErrorResponse

app = FastAPI(
    title="Night-Time Lights API",
    description="API for Rwanda night-time lights and population data",
    version="1.0.0"
)

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {"message": "Night-Time Lights API is running", "status": "healthy"}

@app.get("/health", tags=["Health"])
async def health_check():
    """Database health check"""
    try:
        cursor, conn = get_db_cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# ===== CELLS ENDPOINTS =====

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
        cursor, conn = get_db_cursor()
        
        query = "SELECT * FROM cells WHERE 1=1"
        params = []
        
        if province:
            query += " AND province_name ILIKE %s"
            params.append(f"%{province}%")
        if district:
            query += " AND district_name ILIKE %s"
            params.append(f"%{district}%")
        if sector:
            query += " AND sector_name ILIKE %s"
            params.append(f"%{sector}%")
            
        query += " ORDER BY province_name, district_name, sector_name LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
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

@app.get("/cells/{cell_id}", response_model=APIResponse, tags=["Administrative"])
async def get_cell_by_id(
    cell_id: str = Path(..., description="Cell ID to retrieve")
):
    """Get specific cell by ID"""
    try:
        cursor, conn = get_db_cursor()
        
        cursor.execute("SELECT * FROM cells WHERE cell_id = %s", (cell_id,))
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail=f"Cell {cell_id} not found")
        
        cursor.close()
        conn.close()
        
        return APIResponse(
            success=True,
            data=[dict(result)],
            count=1
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== POPULATION ENDPOINTS =====

@app.get("/population", response_model=APIResponse, tags=["Population"])
async def get_population(
    province: Optional[str] = Query(None, description="Filter by province name"),
    district: Optional[str] = Query(None, description="Filter by district name"),
    min_population: Optional[float] = Query(None, description="Minimum general population"),
    max_population: Optional[float] = Query(None, description="Maximum general population"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get population data with optional filtering"""
    try:
        cursor, conn = get_db_cursor()
        
        query = """
        SELECT p.*, c.province_name, c.district_name, c.sector_name, c.cell_name
        FROM pop p
        JOIN cells c ON p.cell_id = c.cell_id
        WHERE 1=1
        """
        params = []
        
        if province:
            query += " AND c.province_name ILIKE %s"
            params.append(f"%{province}%")
        if district:
            query += " AND c.district_name ILIKE %s"
            params.append(f"%{district}%")
        if min_population:
            query += " AND p.general_pop >= %s"
            params.append(min_population)
        if max_population:
            query += " AND p.general_pop <= %s"
            params.append(max_population)
            
        query += " ORDER BY p.general_pop DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
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

@app.get("/population/{cell_id}", response_model=APIResponse, tags=["Population"])
async def get_population_by_cell(
    cell_id: str = Path(..., description="Cell ID to get population for")
):
    """Get population data for specific cell"""
    try:
        cursor, conn = get_db_cursor()
        
        query = """
        SELECT p.*, c.province_name, c.district_name, c.sector_name, c.cell_name
        FROM pop p
        JOIN cells c ON p.cell_id = c.cell_id
        WHERE p.cell_id = %s
        """
        
        cursor.execute(query, (cell_id,))
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail=f"Population data for cell {cell_id} not found")
        
        cursor.close()
        conn.close()
        
        return APIResponse(
            success=True,
            data=[dict(result)],
            count=1
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== NTL ANNUAL ENDPOINTS =====

@app.get("/ntl/annual", response_model=APIResponse, tags=["Night-Time Lights"])
async def get_ntl_annual(
    year: Optional[int] = Query(None, description="Filter by year"),
    province: Optional[str] = Query(None, description="Filter by province name"),
    district: Optional[str] = Query(None, description="Filter by district name"),
    min_mean: Optional[float] = Query(None, description="Minimum NTL mean value"),
    max_mean: Optional[float] = Query(None, description="Maximum NTL mean value"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get annual NTL data with optional filtering"""
    try:
        cursor, conn = get_db_cursor()
        
        query = """
        SELECT n.*, c.province_name, c.district_name, c.sector_name, c.cell_name
        FROM ntl_annual n
        JOIN cells c ON n.cell_id = c.cell_id
        WHERE 1=1
        """
        params = []
        
        if year:
            query += " AND n.year = %s"
            params.append(year)
        if province:
            query += " AND c.province_name ILIKE %s"
            params.append(f"%{province}%")
        if district:
            query += " AND c.district_name ILIKE %s"
            params.append(f"%{district}%")
        if min_mean:
            query += " AND n.ntl_mean >= %s"
            params.append(min_mean)
        if max_mean:
            query += " AND n.ntl_mean <= %s"
            params.append(max_mean)
            
        query += " ORDER BY n.year DESC, n.ntl_mean DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
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

@app.get("/ntl/annual/{cell_id}", response_model=APIResponse, tags=["Night-Time Lights"])
async def get_ntl_annual_by_cell(
    cell_id: str = Path(..., description="Cell ID to get NTL data for"),
    year: Optional[int] = Query(None, description="Filter by specific year")
):
    """Get annual NTL data for specific cell"""
    try:
        cursor, conn = get_db_cursor()
        
        query = """
        SELECT n.*, c.province_name, c.district_name, c.sector_name, c.cell_name
        FROM ntl_annual n
        JOIN cells c ON n.cell_id = c.cell_id
        WHERE n.cell_id = %s
        """
        params = [cell_id]
        
        if year:
            query += " AND n.year = %s"
            params.append(year)
            
        query += " ORDER BY n.year DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        if not results:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail=f"NTL annual data for cell {cell_id} not found")
        
        cursor.close()
        conn.close()
        
        return APIResponse(
            success=True,
            data=[dict(row) for row in results],
            count=len(results)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== NTL MONTHLY ENDPOINTS =====

@app.get("/ntl/monthly", response_model=APIResponse, tags=["Night-Time Lights"])
async def get_ntl_monthly(
    year: Optional[int] = Query(None, description="Filter by year"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filter by month (1-12)"),
    start_date: Optional[date] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date filter (YYYY-MM-DD)"),
    province: Optional[str] = Query(None, description="Filter by province name"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get monthly NTL data with optional filtering"""
    try:
        cursor, conn = get_db_cursor()
        
        query = """
        SELECT n.*, c.province_name, c.district_name, c.sector_name, c.cell_name
        FROM ntl_monthly n
        JOIN cells c ON n.cell_id = c.cell_id
        WHERE 1=1
        """
        params = []
        
        if year:
            query += " AND n.year = %s"
            params.append(year)
        if month:
            query += " AND n.month = %s"
            params.append(month)
        if start_date:
            query += " AND n.date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND n.date <= %s"
            params.append(end_date)
        if province:
            query += " AND c.province_name ILIKE %s"
            params.append(f"%{province}%")
            
        query += " ORDER BY n.date DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
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

# ===== ANALYTICS ENDPOINTS =====

@app.get("/analytics/population-summary", response_model=APIResponse, tags=["Analytics"])
async def get_population_summary():
    """Get population summary statistics by province"""
    try:
        cursor, conn = get_db_cursor()
        
        query = """
        SELECT 
            c.province_name,
            COUNT(*) as cell_count,
            SUM(p.general_pop) as total_population,
            AVG(p.general_pop) as avg_population,
            SUM(p.children_under5) as total_children,
            SUM(p.elderly_60) as total_elderly,
            SUM(p.building_count) as total_buildings
        FROM cells c
        JOIN pop p ON c.cell_id = p.cell_id
        GROUP BY c.province_name
        ORDER BY total_population DESC
        """
        
        cursor.execute(query)
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

@app.get("/analytics/ntl-trends", response_model=APIResponse, tags=["Analytics"])
async def get_ntl_trends(
    province: Optional[str] = Query(None, description="Filter by province name")
):
    """Get NTL trends over time by province"""
    try:
        cursor, conn = get_db_cursor()
        
        query = """
        SELECT 
            c.province_name,
            n.year,
            COUNT(*) as cell_count,
            AVG(n.ntl_mean) as avg_ntl_mean,
            SUM(n.ntl_sum) as total_ntl_sum,
            MAX(n.ntl_max) as max_ntl_value
        FROM cells c
        JOIN ntl_annual n ON c.cell_id = n.cell_id
        WHERE 1=1
        """
        params = []
        
        if province:
            query += " AND c.province_name ILIKE %s"
            params.append(f"%{province}%")
            
        query += """
        GROUP BY c.province_name, n.year
        ORDER BY c.province_name, n.year
        """
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)