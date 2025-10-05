from pydantic import BaseModel


class GeoLocation(BaseModel):
    latitude: float
    longitude: float


class VehicleLocation(BaseModel):
    vehicle_id: str
    location: GeoLocation


class UserData(BaseModel):
    user_id: str
    location: str
    zoom: int
    width: int
    height: int
