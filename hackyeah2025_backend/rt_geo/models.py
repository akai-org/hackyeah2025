from pydantic import BaseModel


class GeoLocation(BaseModel):
    latitude: float
    longitude: float


class VehicleLocation(GeoLocation):
    vehicle_id: str


class UserData(BaseModel):
    user_id: str
    location: GeoLocation
    zoom: int
    width: int
    height: int
