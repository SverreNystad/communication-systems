from stmpy import Machine, Driver
import paho.mqtt.client as mqtt
import random

from dataclasses import dataclass

from broker import MQTT_BROKER, MQTT_PORT

# from sense_hat import SenseHat


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

    def __init__(self):
        self.mqtt_client = None
        self.stm = None
        self.sense = None  # SenseHat()
        # self.sense.clear()

    def open_scooter(self):
        print("🟢 Scooter unlocked and ride started.")
        self.publish_state("running")

    def close_scooter(self):
        print("🔒 Scooter locked and idle.")
        self.publish_state("locked")

    def deactivate_scooter(self):
        print("⚠️ Scooter deactivated for maintenance.")
        self.publish_state("maintenance")

    def is_parking_valid(self):
        # Simulate valid/invalid parking
        result = random.choice([True, False])
        print(f"🅿️ Parking check: {'valid' if result else 'invalid'}")
        return "Locked" if result else "Running"

    def publish_state(self, state):
        if self.mqtt_client:
            self.mqtt_client.publish("scooter/state", state)

    def get_scooter_info(self) -> ScooterInformation:
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

    def send_acknowledge(self, acktype):
        print("📩 Sending acknowledgment to server.")
        self.mqtt_client.publish("scooter/ack", acktype)


def create_machine(scooter: ScooterManager):
    states = [
        {"name": "Locked", "entry": "close_scooter"},
        {"name": "Running", "entry": "open_scooter"},
        {"name": "Maintenance", "entry": "deactivate_scooter"},
    ]

    transitions = [
        {"source": "initial", "target": "Locked"},
        {"trigger": "evt_request_info", "source": "Locked", "target": "Locked"},
        {"trigger": "evt_deactivate", "source": "Locked", "target": "Maintenance"},
        {"trigger": "evt_activate", "source": "Maintenance", "target": "Locked"},
        {"trigger": "evt_unlock", "source": "Locked", "target": "Running"},
        {
            "trigger": "evt_park_scooter",
            "source": "Running",
            "function": scooter.is_parking_valid,
        },
    ]

    return Machine(name="scooter", states=states, transitions=transitions, obj=scooter)


# ------------------------
# MQTT Setup
# ------------------------


def on_connect(client, userdata, flags, rc):
    print("✅ Scooter connected to MQTT broker.")
    client.subscribe("server/scooter/cmd")


def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"📩 MQTT message received: {payload}")

    if payload == "evt_unlock":
        userdata.stm.send("evt_unlock")
        userdata.send_acknowledge("evt_ack_open_request")
    elif payload == "evt_park_scooter":
        userdata.stm.send("evt_park_scooter")
        userdata.send_acknowledge("evt_ack_close_request")
    elif payload == "evt_request_info":
        info = userdata.get_scooter_info()
        print("Scooter Info:", info)


if __name__ == "__main__":
    # -----------------------
    # Server Entry
    # -----------------------
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
