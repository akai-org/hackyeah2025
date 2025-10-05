# listen to registered fleets and update goespatial data of objects in redis
from redis import Redis
from rt_geo.models import GeoLocation, VehicleLocation
import math


class GeoTracker:
    """
    Track vehicle location
    """

    def __init__(self):
        self.redis = Redis()

    def get_latest_location(
        self, location: GeoLocation, zoom: int, map_width: int, map_height: int
    ) -> list[VehicleLocation]:
        """
        Get latest vehicle location from redis geospatial index
        Requested by users
        """
        # calculate lon, lat of bounding box from location and zoom

        meters_per_pixel = (
            156543.03392 * math.cos(math.radians(location.latitude)) / (2**zoom)
        )
        width_km = (map_width * meters_per_pixel) / 1000
        height_km = (map_height * meters_per_pixel) / 1000

        print(f"width_km: {width_km}, height_km: {height_km}")

        locations = self.redis.geosearch(
            "vehicles",
            longitude=location.longitude,
            latitude=location.latitude,
            width=width_km,
            height=height_km,
            unit="km",
            withcoord=True,
        )

        for member, coords in locations:
            decoded = [
                {
                    "vehicle_id": member.decode("utf-8")
                    if isinstance(member, bytes)
                    else member,
                    "longitude": coords[0],
                    "latitude": coords[1],
                }
            ]

        print(decoded)
        return decoded
