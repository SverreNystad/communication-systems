from stmpy import Machine, Driver
import paho.mqtt.client as mqtt
import random

class ScooterRental:

    def __init__(self):
        self.mqtt_client = None
        self.stm = None

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

def create_machine(rental: ScooterRental):
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

        {"trigger": "evt_park_scooter", "source": "Running", "function": "is_parking_valid"},
    ]

    return Machine(name="scooter", states=states, transitions=transitions, obj=rental)



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
        scooter.stm.send("evt_login")


# -----------------------
# Server Entry
# -----------------------
scooter = ScooterRental()


mqtt_client = mqtt.Client(client_id="", userdata=scooter, protocol=mqtt.MQTTv311)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
scooter.mqtt_client = mqtt_client


machine = create_machine(scooter)
scooter.stm = machine

driver = Driver()
driver.add_machine(machine)
driver.start()