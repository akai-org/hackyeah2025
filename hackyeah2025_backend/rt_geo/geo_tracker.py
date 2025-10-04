# listen to registered fleets and update goespatial data of objects in redis
from redis.asyncio import Redis
from rt_geo.models import GeoLocation, VehicleLocation
import math


class GeoTracker:
    """
    Track vehicle location
    """

    def __init__(self):
        self.redis = Redis(host="redis", port=6379, db=0)

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

        search_width = width_km
        search_height = height_km
        locations = self.redis.geosearch(
            "vehicles",
            longitude=location.longitude,
            latitude=location.latitude,
            width=search_width,
            height=search_height,
            withcoord=True,
        )

        return [
            VehicleLocation(vehicle_id=vid, latitude=lat, longitude=lon)
            for vid, (lon, lat) in locations.docs()
        ]
