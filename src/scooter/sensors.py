from dataclasses import dataclass
from sense_hat import SenseHat

sense = SenseHat()
sense.clear()


@dataclass
class ScooterInformation:
    temperature: float
    pressure: float
    humidity: float
    pitch: float
    roll: float
    yaw: float
    acceleration_x: float
    acceleration_y: float
    acceleration_z: float


def get_scooter_info() -> ScooterInformation:
    """
    Get the scooter information from the Sense HAT.
    """
    # Retrieve the acceleration data
    # The x, y, and z values are in Gs
    acceleration = sense.get_accelerometer_raw()
    x = acceleration["x"]
    y = acceleration["y"]
    z = acceleration["z"]

    x = round(x, 0)
    y = round(y, 0)
    z = round(z, 0)

    # Retrieve pitch roll yaw
    o = sense.get_orientation()
    pitch = o["pitch"]
    roll = o["roll"]
    yaw = o["yaw"]
    t = sense.get_temperature()

    # Get the temperature, pressure, and humidity
    p = sense.get_pressure()
    h = sense.get_humidity()

    # Round the values to one decimal place
    t = round(t, 1)
    p = round(p, 1)
    h = round(h, 1)

    scooter_info = ScooterInformation(
        temperature=t,
        pressure=p,
        humidity=h,
        pitch=pitch,
        roll=roll,
        yaw=yaw,
        acceleration_x=x,
        acceleration_y=y,
        acceleration_z=z,
    )
    return scooter_info
