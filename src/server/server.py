from enum import StrEnum
from stmpy import Machine, Driver
import paho.mqtt.client as mqtt
import random


class AccessLevel(StrEnum):
    ADMIN = "admin"
    USER = "user"


class ServerApp:

    def __init__(self):
        self.stm = None
        self.mqtt_client = None
        self.user_type = None  # "admin", "user", or None

    # ------------------------
    # Choice guard functions
    # ------------------------

    def is_admin(self):
        return self.user_type == "admin"

    def is_user(self):
        return self.user_type == "user"

    def payment_accepted(self):  # It is stuck on the payment? Not in the correct state?
        result = random.choice([True, False])
        print(f"💳 Payment check: {'accepted' if result else 'rejected'}")
        return "ScooterRunning" if result else "Idle"

    # ------------------------
    # Entry/Exit actions
    # ------------------------

    def send_evt_unlock(self):
        print("🟢 Sending unlock command to scooter.")
        self.mqtt_client.publish("server/scooter/cmd", "evt_unlock")

    def send_evt_lock(self):
        print("🔒 Sending lock command to scooter.")
        self.mqtt_client.publish("server/scooter/cmd", "evt_park_scooter")


# ------------------------
# STMPY Machine Setup
# ------------------------


def create_machine(server: ServerApp):
    states = [
        {"name": "Idle"},
        {"name": "Admin"},
        {"name": "User"},
        {"name": "ScooterRunning", "entry": "send_evt_unlock", "exit": "send_evt_lock"},
    ]

    transitions = [
        {"source": "initial", "target": "Idle"},
        # Login branching
        {"trigger": "evt_login", "source": "Idle", "function": "login_branch"},
        # Logout
        {"trigger": "evt_logout", "source": "Admin", "target": "Idle"},
        {"trigger": "evt_logout", "source": "User", "target": "Idle"},
        # User requests to open scooter
        {
            "trigger": "evt_recieved_open_request",
            "source": "User",
            "function": "payment_accepted",
        },
        # User ends ride
        {
            "trigger": "evt_recieved_close_request",
            "source": "ScooterRunning",
            "target": "Idle",
        },
    ]

    return Machine(name="server", states=states, transitions=transitions, obj=server)


# This function wraps the login logic into a choice
def login_branch(self):
    if self.is_admin():
        return "Admin"
    elif self.is_user():
        return "User"
    else:
        return "Idle"


# Inject dynamic function
ServerApp.login_branch = login_branch

# ------------------------
# MQTT Setup
# ------------------------


def on_connect(client, userdata, flags, rc):
    print("✅ Server connected to MQTT broker.")
    client.subscribe("user/command")  # User interface publishes here
    client.subscribe("scooter/state")


def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"📩 MQTT message received: {payload}")

    if payload == "evt_login_admin":
        userdata.user_type = "admin"
        userdata.stm.send("evt_login")
    elif payload == "evt_login_user":
        userdata.user_type = "user"
        userdata.stm.send("evt_login")
    elif payload == "evt_logout":
        userdata.user_type = None
        userdata.stm.send("evt_logout")
    elif payload == "evt_recieved_open_request":
        userdata.stm.send("evt_recieved_open_request")
    elif payload == "evt_recieved_close_request":
        userdata.stm.send("evt_recieved_close_request")
    else:
        print("⚠️ Unknown command.")


# ------------------------
# App Entry
# ------------------------
if __name__ == "__main__":

    server = ServerApp()

    mqtt_client = mqtt.Client(client_id="", userdata=server, protocol=mqtt.MQTTv311)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    server.mqtt_client = mqtt_client

    machine = create_machine(server)
    server.stm = machine

    driver = Driver()
    driver.add_machine(machine)
    driver.start()

    mqtt_client.connect("localhost", 1883)
    mqtt_client.loop_forever()
