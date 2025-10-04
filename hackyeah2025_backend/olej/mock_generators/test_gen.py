from olej.models import GeoLocation, VehicleLocation, UserData
from redis.asyncio import Redis
from loguru import logger
import websockets
import asyncio
import requests

BACKEND_IP = "localhost"
BACKEND_PORT = 8001


class BaseTransitMock:
    def __init__(self):
        self.redis = Redis(host="redis", port=6379, db=0)
        self.transmit_interval = 2  # seconds

    async def mock_vehicle(
        self, vehicle_id: str, route: list[GeoLocation], start_sync: asyncio.Event
    ):
        await start_sync.wait()
        async with websockets.connect(
            f"ws://{BACKEND_IP}:{BACKEND_PORT}/ws/vehicles/{vehicle_id}"
        ) as ws:
            for loc in route:
                await asyncio.sleep(self.transmit_interval)
                v_loc = VehicleLocation(
                    latitude=loc.latitude,
                    longitude=loc.longitude,
                    vehicle_id=vehicle_id,
                )
                await ws.send(v_loc.model_dump_json())

    async def mock_user(
        self,
        user_id: str,
        location: GeoLocation | list[GeoLocation],
        zoom: int,
        width: int,
        height: int,
        start_sync: asyncio.Event,
    ):
        await start_sync.wait()

        if isinstance(location, GeoLocation):
            while True:
                await asyncio.sleep(1)
                resp = requests.get(
                    f"http://{BACKEND_IP}:{BACKEND_PORT}/api/geo/vehicles/",
                    params={
                        "latitude": location.latitude,
                        "longitude": location.longitude,
                        "zoom": zoom,
                        "map_width": width,
                        "map_height": height,
                    },
                )
                logger.info(f"{user_id} received: {resp.json()}")
        elif isinstance(location, list):
            for loc in location:
                await asyncio.sleep(self.transmit_interval)
                resp = requests.get(
                    f"http://{BACKEND_IP}:{BACKEND_PORT}/api/geo/vehicles/",
                    params={
                        "latitude": loc.latitude,
                        "longitude": loc.longitude,
                        "zoom": zoom,
                        "map_width": width,
                        "map_height": height,
                    },
                )
                logger.info(f"User received: {resp.json()}")


class TestMock(BaseTransitMock):
    def __init__(
        self, users: list[UserData], vehicles: list[tuple[str, list[GeoLocation]]]
    ):
        super().__init__()
        self.users = users
        self.vehicles = vehicles

    async def run(self):
        tasks = []

        start_sync = asyncio.Event()

        for user in self.users:
            tasks.append(
                self.mock_user(
                    user_id=user.user_id,
                    location=user.location,
                    zoom=user.zoom,
                    width=user.width,
                    height=user.height,
                    start_sync=start_sync,
                )
            )

        for vehicle_id, route in self.vehicles:
            tasks.append(
                self.mock_vehicle(
                    vehicle_id=vehicle_id,
                    route=route,
                    start_sync=start_sync,
                )
            )

        start_sync.set()
        await asyncio.gather(*tasks)


# Mock dev-test
test_users = [
    UserData(
        user_id="test_user",
        location=GeoLocation(latitude=20.0, longitude=50.0),
        zoom=12,
        width=800,
        height=600,
    )
]

test_vehicles = [
    (
        "test_vehicle_1",
        [
            GeoLocation(latitude=20.0, longitude=50.0),
            GeoLocation(latitude=20.1, longitude=50.1),
            GeoLocation(latitude=20.2, longitude=50.2),
        ],
    )
]

if __name__ == "__main__":
    mock = TestMock(users=test_users, vehicles=test_vehicles)
    asyncio.run(mock.run())
