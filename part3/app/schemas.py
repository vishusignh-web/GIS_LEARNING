from typing import Any, List, Optional, Tuple

from pydantic import BaseModel, Field, model_validator


class ParcelQuery(BaseModel):
    block_number: Optional[str] = Field(None, max_length=20, pattern=r"^[A-Za-z0-9\- ]+$",
                                        examples=["11"])
    zoning: Optional[str] = Field(None, max_length=10, pattern=r"^[A-Za-z0-9]+$", examples=["R1"])
    include_geometry: bool = False
    page_size: int = Field(100, ge=1, le=1000, description="Records requested per upstream page")


class Envelope(BaseModel):
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    @model_validator(mode="after")
    def check_order(self):
        if self.xmin >= self.xmax or self.ymin >= self.ymax:
            raise ValueError("Envelope min values must be smaller than max values")
        return self


class GeometryQuery(BaseModel):
    wkid: int = Field(4326, description="Spatial reference of the supplied geometry")
    envelope: Optional[Envelope] = None
    ring: Optional[List[Tuple[float, float]]] = Field(None, description="Closed polygon ring of (x, y)")
    include_geometry: bool = False
    page_size: int = Field(100, ge=1, le=1000)

    @model_validator(mode="after")
    def check_geometry(self):
        if (self.envelope is None) == (self.ring is None):
            raise ValueError("Provide exactly one of 'envelope' or 'ring'")
        if self.ring is not None:
            r = self.ring
            if len(r) < 4:
                raise ValueError("A ring needs at least 4 points")
            if r[0] != r[-1]:
                raise ValueError("Ring is not closed (first and last vertex must match)")
        return self


class NearbyRequest(BaseModel):
    x: float = Field(..., ge=-180, le=180)
    y: float = Field(..., ge=-90, le=90)
    distance_m: float = Field(500, gt=0, le=5000)


class ParcelResult(BaseModel):
    count: int
    features: List[dict[str, Any]]


class ErrorResponse(BaseModel):
    error: str
    detail: str
