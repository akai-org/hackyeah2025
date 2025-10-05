from pydantic import BaseModel, model_validator


class GeoLocation(BaseModel):
    latitude: float
    longitude: float


class VehicleLocation(BaseModel):
    vehicle_id: str
    location: str


class UserData(BaseModel):
    user_id: str
    location: str
    zoom: int
    width: int
    height: int
