from stmpy import Machine

class ScooterRental:

    def __init__(self, mqtt_client):
        self.payment_success = False
        self.mqtt_client = mqtt_client

    def on_locked(self):
        self.mqtt_client.publish("scooter/state", "locked")

    def on_unlocked(self):
        self.mqtt_client.publish("scooter/state", "unlocked")

    def payment_check(self):
        return "Unlocked" if self.payment_success else "Locked"

def create_machine(rental_obj):
    transitions = [
        {"source": "initial", "target": "Locked"},
        {"trigger": "select_scooter", "source": "Locked", "function": rental_obj.payment_check}
    ]

    states = [
        {"name": "Locked", "entry": "on_locked"},
        {"name": "Unlocked", "entry": "on_unlocked"}
    ]

    return Machine(name="scooter", obj=rental_obj, states=states, transitions=transitions)

