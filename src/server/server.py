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

    def payment_accepted(self):  
        result = random.choice([True, False])
        print(f"💳 Payment check: {'accepted' if result else 'rejected'}")
        return result

    # ------------------------
    # Entry/Exit actions
    # ------------------------

    def send_evt_unlock(self):
        print("🟢 Sending unlock command to scooter.")
        self.mqtt_client.publish("server/scooter/cmd", "evt_unlock")

    def send_evt_lock(self):
        print("🔒 Sending lock command to scooter.")
        self.mqtt_client.publish("server/scooter/cmd", "evt_park_scooter")

    def login_branch(self) -> str:
        print("🔑 Login branch triggered.")
        if self.is_admin():
            return "Admin"
        elif self.is_user():
            return "User"
        else:
            return "Idle"
        
    def send_acknowledge(self, acktype):
        print("📩 Sending acknowledgment to user.")
        self.mqtt_client.publish("user/ack", acktype)


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
        # {"trigger": "evt_login", "source": "Idle", "function": "login_branch"},
        {
            "trigger": "evt_login",
            "source": "Idle",
            "function": server.login_branch,
        },
        # Logout
        {"trigger": "evt_logout", "source": "Admin", "target": "Idle"},
        {"trigger": "evt_logout", "source": "User", "target": "Idle"},
        # User requests to open scooter and scooter acks
        {"trigger": "ack_open_request", "source": "User", "target": "ScooterRunning"},
        # User ends ride
        {"trigger": "evt_ack_close_request","source": "ScooterRunning","target": "Idle"},
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
    payload = msg.payload.decode()
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
    #elif payload == "evt_request_info": # We haven't covered this case yet 

    #Scooter
    elif payload == "evt_recieved_open_request":
        if userdata.payment_accepted():
            userdata.send_evt_unlock()
        else:
            print("❌ Payment rejected.")
    elif payload == "evt_ack_open_request": #ACK
        userdata.stm.send("evt_ack_open_request")
    elif payload == "evt_recieved_close_request":
        userdata.send_evt_lock()
    elif payload == "evt_ack_close_request": #ACK
        userdata.stm.send("evt_ack_close_request")
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
