from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class APIResponse(BaseModel):
    success: bool
    data: List[dict]
    count: int
    message: Optional[str] = None

class ErrorResponse(BaseModel):
    success: bool
    error: str
    message: str

class Cell(BaseModel):
    cell_id: str
    province_name: Optional[str]
    district_name: Optional[str]
    sector_name: Optional[str]
    cell_name: Optional[str]

class Population(BaseModel):
    id: int
    cell_id: str
    elderly_60: Optional[float]
    general_pop: Optional[float]
    children_under5: Optional[float]
    youth_15_24: Optional[float]
    men_2020: Optional[float]
    women_2020: Optional[float]
    building_count: Optional[float]

class NTLAnnual(BaseModel):
    id: int
    cell_id: str
    ntl_min: Optional[float]
    ntl_max: Optional[float]
    ntl_mean: Optional[float]
    ntl_median: Optional[float]
    ntl_sum: Optional[float]
    pixel_count: Optional[float]
    raster_filename: Optional[str]
    year: int

class NTLMonthly(BaseModel):
    id: int
    cell_id: str
    ntl_min: Optional[float]
    ntl_max: Optional[float]
    ntl_mean: Optional[float]
    ntl_median: Optional[float]
    ntl_sum: Optional[float]
    pixel_count: Optional[float]
    raster_filename: Optional[str]
    year: int
    month: int
    date: date