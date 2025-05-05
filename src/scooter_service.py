import json
import random
from dataclasses import asdict, dataclass

import paho.mqtt.client as mqtt
from sense_hat import SenseHat
from stmpy import Driver, Machine

from broker import MQTT_BROKER, MQTT_PORT, Command, Topic


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


class ScooterManager:
    # Define color map for different states (RGB)
    COLORS = {
        "running": (0, 255, 0),  # green
        "locked": (255, 0, 0),  # red
        "maintenance": (255, 255, 0),  # yellow
        "parking_valid": (0, 0, 255),  # blue
        "parking_invalid": (255, 0, 0),  # red
    }

    def __init__(self):
        self.mqtt_client = None
        self.stm = None
        self.sense = SenseHat()

    def open_scooter(self):
        msg = "🟢 Scooter unlocked and ride started."
        col = self.COLORS["running"]
        print(msg)
        self.sense.show_message(msg, scroll_speed=0.05, text_colour=col, back_colour=(0, 0, 0))
        self.publish_state("running")

    def close_scooter(self):
        msg = "🔒 Scooter locked and idle."
        col = self.COLORS["locked"]
        print(msg)
        self.sense.show_message(msg, scroll_speed=0.05, text_colour=col, back_colour=(0, 0, 0))
        self.publish_state("locked")

    def deactivate_scooter(self):
        msg = "⚠️ Scooter deactivated for maintenance."
        col = self.COLORS["maintenance"]
        print(msg)
        self.sense.show_message(msg, scroll_speed=0.05, text_colour=col, back_colour=(0, 0, 0))
        self.publish_state("maintenance")

    def is_parking_valid(self):
        valid = random.choice([True, False])
        key = "parking_valid" if valid else "parking_invalid"
        msg = f"🅿️ Parking check: {'valid' if valid else 'invalid'}"
        col = self.COLORS[key]
        print(f"{msg}")
        self.sense.show_message(msg, scroll_speed=0.05, text_colour=col, back_colour=(0, 0, 0))
        return "Locked" if valid else "Running"

    def publish_state(self, state: str):
        if self.mqtt_client:
            self.mqtt_client.publish(Topic.SCOOTER_STATE, state)

    def get_scooter_info(self) -> ScooterInformation:
        # Sensor retrieval omitted for brevity
        """
        Get the scooter information from the Sense HAT.
        """
        # Retrieve the acceleration data
        # The x, y, and z values are in Gs
        acceleration = self.sense.get_accelerometer_raw()
        x = acceleration["x"]
        y = acceleration["y"]
        z = acceleration["z"]

        x = round(x, 0)
        y = round(y, 0)
        z = round(z, 0)

        # Retrieve pitch roll yaw
        o = self.sense.get_orientation()
        pitch = o["pitch"]
        roll = o["roll"]
        yaw = o["yaw"]
        t = self.sense.get_temperature()

        # Get the temperature, pressure, and humidity
        p = self.sense.get_pressure()
        h = self.sense.get_humidity()

        # Round the values to one decimal place
        t = round(t, 1)
        p = round(p, 1)
        h = round(h, 1)

        return ScooterInformation(
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

    def send_acknowledge(self, acktype: str):
        print("📩 Sending acknowledgment to server.")
        self.mqtt_client.publish(Topic.SCOOTER_ACK, acktype)


def create_machine(scooter: ScooterManager):
    states = [
        {"name": "Locked", "entry": "close_scooter"},
        {"name": "Running", "entry": "open_scooter"},
        {"name": "Maintenance", "entry": "deactivate_scooter"},
    ]

    transitions = [
        {"source": "initial", "target": "Locked"},
        {"trigger": Command.REQUEST_INFO, "source": "Locked", "target": "Locked"},
        {"trigger": "evt_deactivate", "source": "Locked", "target": "Maintenance"},
        {"trigger": "evt_activate", "source": "Maintenance", "target": "Locked"},
        {"trigger": "evt_unlock", "source": "Locked", "target": "Running"},
        {"trigger": "evt_unlock", "source": "Running", "target": "Running"},
        {"trigger": "evt_park_scooter", "source": "Running", "function": scooter.is_parking_valid},
    ]

    return Machine(name="scooter", states=states, transitions=transitions, obj=scooter)


def on_connect(client, userdata, flags, rc):
    print("✅ Scooter connected to MQTT broker.")
    client.subscribe(Topic.SCOOTER_CMD)


def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"📩 MQTT message received: {payload}")

    if payload == Command.UNLOCK_SCOOTER:
        userdata.stm.send("evt_unlock")
        userdata.send_acknowledge(Command.ACK_OPEN_REQUEST)
    elif payload == Command.LOCK_SCOOTER:
        userdata.stm.send("evt_park_scooter")
        userdata.send_acknowledge(Command.ACK_CLOSE_REQUEST)
    elif payload == Command.REQUEST_INFO:
        info = userdata.get_scooter_info()
        info_json = json.dumps(asdict(info))
        userdata.mqtt_client.publish(Topic.SCOOTER_INFO, info_json)
    # Admin maintenance commands
    elif payload == Command.EVT_DEACTIVATE:
        print("⚠️ Admin requested maintenance mode.")
        userdata.stm.send("evt_deactivate")

    elif payload == Command.EVT_ACTIVATE:
        print("✅ Admin re-activated scooter.")
        userdata.stm.send("evt_activate")

    else:
        print("⚠️ Unknown scooter command.")


if __name__ == "__main__":
    scooter = ScooterManager()
    mqtt_client = mqtt.Client(client_id="", userdata=scooter, protocol=mqtt.MQTTv311)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    scooter.mqtt_client = mqtt_client

    machine = create_machine(scooter)
    scooter.stm = machine
    driver = Driver()
    driver.add_machine(machine)
    driver.start()

    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    mqtt_client.loop_forever()
