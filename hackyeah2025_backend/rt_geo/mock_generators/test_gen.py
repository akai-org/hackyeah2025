from rt_geo.models import GeoLocation, VehicleLocation, UserData
from redis.asyncio import Redis
import websockets
import asyncio
import requests

BACKEND_IP = "localhost"
BACKEND_PORT = 8001


class BaseTransitMock:
    def __init__(self):
        self.redis = Redis(host="redis", port=6379, db=0)
        self.transmit_interval = 0.5  # seconds

    async def mock_vehicle(
        self,
        vehicle_id: str,
        route: list[GeoLocation],
    ):
        async with websockets.connect(
            f"ws://{BACKEND_IP}:{BACKEND_PORT}/ws/vehicles/{vehicle_id}"
        ) as ws:
            for loc in route:
                await asyncio.sleep(self.transmit_interval)
                v_loc = VehicleLocation(
                    location=loc,
                    vehicle_id=vehicle_id,
                )
                print(f"Vehicle {vehicle_id} sending: {v_loc.model_dump_json()}")
                await ws.send(v_loc.model_dump_json())

    async def mock_user(
        self,
        user_id: str,
        location: str | list[str],
        zoom: int,
        width: int,
        height: int,
    ):
        if isinstance(location, str):
            while True:
                print("check")
                await asyncio.sleep(1)
                longitude, latitude = map(float, location.split(","))
                resp = requests.get(
                    f"http://{BACKEND_IP}:{BACKEND_PORT}/api/geo/vehicles/",
                    params={
                        "latitude": latitude,
                        "longitude": longitude,
                        "zoom": zoom,
                        "map_width": width,
                        "map_height": height,
                    },
                )
                print(f"{user_id} received: {resp.json()}")
        elif isinstance(location, list):
            for loc in location:
                print("check")
                longitude, latitude = map(float, location.split(","))
                await asyncio.sleep(self.transmit_interval)
                resp = requests.get(
                    f"http://{BACKEND_IP}:{BACKEND_PORT}/api/geo/vehicles/",
                    params={
                        "latitude": latitude,
                        "longitude": longitude,
                        "zoom": zoom,
                        "map_width": width,
                        "map_height": height,
                    },
                )
                print(f"User received: {resp.json()}")
        else:
            print("kurwa")


class TestMock(BaseTransitMock):
    def __init__(
        self, users: list[UserData], vehicles: list[tuple[str, list[GeoLocation]]]
    ):
        super().__init__()
        self.users = users
        self.vehicles = vehicles

    async def run(self):
        tasks = []

        for user in self.users:
            tasks.append(
                asyncio.create_task(
                    self.mock_user(
                        user_id=user.user_id,
                        location=user.location,
                        zoom=user.zoom,
                        width=user.width,
                        height=user.height,
                    )
                )
            )

        for vehicle_id, route in self.vehicles:
            tasks.append(
                asyncio.create_task(
                    self.mock_vehicle(
                        vehicle_id=vehicle_id,
                        route=route,
                    )
                )
            )

        print("running")
        await asyncio.gather(*tasks)


# Mock dev-test
test_users = [
    UserData(
        user_id="test_user",
        location="20.0,50.0",
        zoom=12,
        width=800,
        height=600,
    )
]

test_vehicles = [
    (
        "test_vehicle_1",
        [
            GeoLocation(latitude=50.0, longitude=20.0),
            GeoLocation(latitude=50.0, longitude=20.0),
            GeoLocation(latitude=50.0, longitude=20.0),
        ],
    )
]

if __name__ == "__main__":
    mock = TestMock(users=test_users, vehicles=test_vehicles)
    asyncio.run(mock.run())
