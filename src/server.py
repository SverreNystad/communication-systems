import random
from enum import StrEnum

import paho.mqtt.client as mqtt
from stmpy import Driver, Machine

from broker import MQTT_BROKER, MQTT_PORT, Command, Topic


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
        self.mqtt_client.publish(Topic.SCOOTER_CMD, Command.UNLOCK_SCOOTER)

    def send_evt_lock(self):
        print("🔒 Sending lock command to scooter.")
        self.mqtt_client.publish(Topic.SCOOTER_CMD, Command.LOCK_SCOOTER)

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

    def send_acknowledge(self, acktype: str):
        print(f"📩 Acknowledging {acktype} to user.")
        self.mqtt_client.publish(Topic.USER_ACK, acktype)


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
        {"trigger": Command.LOGOUT, "source": State.ADMIN, "target": State.IDLE},
        {"trigger": Command.LOGOUT, "source": State.USER, "target": State.IDLE},
        # User requests to open scooter and scooter acks
        {
            "trigger": Command.ACK_OPEN_REQUEST,
            "source": State.USER,
            "target": State.SCOOTER_RUNNING,
        },
        # User ends ride
        {
            "trigger": Command.ACK_CLOSE_REQUEST,
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
    client.subscribe(Topic.USER_CMD)
    client.subscribe(Topic.SCOOTER_STATE)
    client.subscribe(Topic.SCOOTER_ACK)


def on_message(client, userdata, msg):
    payload: str = msg.payload.decode()
    print(f"📩 MQTT message received: {payload}")

    # User interface
    if payload == Command.LOGIN_ADMIN:
        userdata.user_type = AccessLevel.ADMIN
        userdata.stm.send(Command.LOGIN)
        userdata.send_acknowledge(Command.LOGIN_ADMIN)
    elif payload == Command.LOGIN_USER:
        userdata.user_type = AccessLevel.USER
        userdata.stm.send(Command.LOGIN)
        userdata.send_acknowledge(Command.LOGIN_USER)
    elif payload == Command.LOGOUT:
        userdata.user_type = None
        userdata.stm.send(Command.LOGOUT)
        userdata.send_acknowledge(Command.LOGOUT)

    # Scooter
    elif payload == Command.RECEIVED_OPEN_REQUEST:
        if userdata.payment_accepted():
            userdata.send_evt_unlock()
        else:
            print("❌ Payment rejected.")
            userdata.send_acknowledge("payment_failed")
    elif payload == Command.ACK_OPEN_REQUEST:
        userdata.stm.send(Command.ACK_OPEN_REQUEST)
    elif payload == Command.RECEIVED_CLOSE_REQUEST:
        userdata.send_evt_lock()
    elif payload == Command.ACK_CLOSE_REQUEST:
        userdata.stm.send(Command.ACK_CLOSE_REQUEST)
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
