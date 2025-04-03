from stmpy import Machine
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

