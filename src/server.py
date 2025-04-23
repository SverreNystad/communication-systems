from enum import StrEnum
from stmpy import Machine, Driver
import paho.mqtt.client as mqtt
import random

from broker import MQTT_BROKER, MQTT_PORT, Command


class AccessLevel(StrEnum):
    ADMIN = "admin"
    USER = "user"


class State(StrEnum):
    IDLE = "Idle"
    ADMIN = "Admin"
    USER = "User"
    SCOOTER_RUNNING = "ScooterRunning"


class ServerApp:

    def __init__(self):
        self.stm = None
        self.mqtt_client = None
        self.user_type: AccessLevel = None

    def payment_accepted(self):
        """Randomly decide if the payment is accepted.
        Returns the next state (ScooterRunning or Idle)."""
        result = random.choice([True, False])
        print(f"💳 Payment check: {'accepted' if result else 'rejected'}")
        return State.SCOOTER_RUNNING if result else State.IDLE

    # ------------------------
    # Entry/Exit actions
    # ------------------------

    def send_evt_unlock(self):
        print("🟢 Sending unlock command to scooter.")
        self.mqtt_client.publish("server/scooter/cmd", "evt_unlock")

    def send_evt_lock(self):
        print("🔒 Sending lock command to scooter.")
        self.mqtt_client.publish("server/scooter/cmd", "evt_park_scooter")

    def login_branch(self):
        print("🔑 Login branch triggered.")
        match self.user_type:
            case AccessLevel.ADMIN:
                print("🔑 Admin login.")
                return State.ADMIN
            case AccessLevel.USER:
                print("🔑 User login.")
                return State.USER
            case _:
                print("⚠️ Unknown user type.")
                return State.IDLE


# ------------------------
# STMPY Machine Setup
# ------------------------


def create_machine(server: ServerApp):
    states = [
        {"name": State.IDLE},
        {"name": State.ADMIN},
        {"name": State.USER},
        {
            "name": State.SCOOTER_RUNNING,
            "entry": Command.UNLOCK_SCOOTER,
            "exit": Command.LOCK_SCOOTER,
        },
    ]

    transitions = [
        {"source": "initial", "target": State.IDLE},
        {
            "trigger": Command.LOGIN,
            "source": State.IDLE,
            "function": server.login_branch,
        },
        # Logout
        {"trigger": "evt_logout", "source": State.ADMIN, "target": State.IDLE},
        {"trigger": "evt_logout", "source": State.USER, "target": State.IDLE},
        # User requests to open scooter and scooter acks
        {
            "trigger": "ack_open_request",
            "source": State.USER,
            "target": State.SCOOTER_RUNNING,
        },
        # User ends ride
        {
            "trigger": "evt_ack_close_request",
            "source": State.SCOOTER_RUNNING,
            "target": State.IDLE,
        },
    ]

    return Machine(name="server", states=states, transitions=transitions, obj=server)


# ------------------------
# MQTT Setup
# ------------------------


def on_connect(client, userdata, flags, rc):
    print("✅ Server connected to MQTT broker.")
    client.subscribe("user/command")  # User interface publishes here
    client.subscribe("scooter/state")
    client.subscribe("scooter/ack")  # Scooter publishes here


def on_message(client, userdata, msg):
    payload: str = msg.payload.decode()
    print(f"📩 MQTT message received: {payload}")

    # User interface
    if payload == "evt_login_admin":
        userdata.user_type = "admin"
        userdata.stm.send("evt_login")
        userdata.send_acknowledge("evt_login_admin")
    elif payload == "evt_login_user":
        userdata.user_type = "user"
        userdata.stm.send("evt_login")
        userdata.send_acknowledge("evt_login_user")
    elif payload == "evt_logout":
        userdata.user_type = None
        userdata.stm.send("evt_logout")
        userdata.send_acknowledge("evt_logout")
    # elif payload == "evt_request_info": # We haven't covered this case yet

    # Scooter
    elif payload == "evt_recieved_open_request":
        if userdata.payment_accepted():
            userdata.send_evt_unlock()
        else:
            print("❌ Payment rejected.")
    elif payload == "evt_ack_open_request":  # ACK
        userdata.stm.send("evt_ack_open_request")
    elif payload == "evt_recieved_close_request":
        userdata.send_evt_lock()
    elif payload == "evt_ack_close_request":  # ACK
        userdata.stm.send("evt_ack_close_request")
    else:
        print("⚠️ Unknown command.")


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

    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    mqtt_client.loop_forever()
