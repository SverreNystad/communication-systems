import json

import paho.mqtt.client as mqtt
from stmpy import Driver, Machine

from broker import MQTT_BROKER, MQTT_PORT, Command, Topic


class AppUI:
    def __init__(self):
        self.stm = None
        self.mqtt_client = None

    def send(self, event):
        self.mqtt_client.publish(Topic.USER_CMD, event)

    def show_welcome(self):
        print("\n== Welcome ==")
        print("1. Login as User")
        print("2. Login as Admin")
        print("0. Exit")
        choice = input("Select: ")
        match choice:
            case "1":
                self.send(Command.LOGIN_USER)
            case "2":
                self.send(Command.LOGIN_ADMIN)
            case "0":
                print("Goodbye!")
                exit()
            case _:
                print("Invalid choice.")
                self.stm.send("restart")

    def show_user_menu(self):
        print("\n== User Menu ==")
        print("1. Rent scooter")
        print("2. End ride")
        print("3. Logout")
        choice = input("Select: ")
        if choice == "1":
            self.send(Command.RECEIVED_OPEN_REQUEST)
            self.stm.send("restart")
        elif choice == "2":
            self.send(Command.RECEIVED_CLOSE_REQUEST)
            self.stm.send("restart")
        elif choice == "3":
            self.send(Command.LOGOUT)
        else:
            print("Invalid choice.")
            self.stm.send("restart")

    def show_admin_menu(self):
        print("\n== Admin Menu ==")
        print("1. Request scooter info")
        print("2. Deactivate scooter")
        print("3. Activate scooter")
        print("4. Logout")
        choice = input("Select: ")
        if choice == "1":
            self.send(Command.REQUEST_INFO)
        elif choice == "2":
            self.send(Command.EVT_DEACTIVATE)
        elif choice == "3":
            self.send(Command.EVT_ACTIVATE)
        elif choice == "4":
            self.send(Command.LOGOUT)
        else:
            print("Invalid choice.")
            self.stm.send("restart")

    def show_scooter_info(self, info):
        print("\n== Scooter Information ==")
        for k, v in info.items():
            print(f"{k.replace('_', ' ').title()}: {v}")
        self.stm.send("restart")


def create_machine(app: AppUI):
    states = [
        {"name": "Welcome", "entry": "show_welcome"},
        {"name": "UserMenu", "entry": "show_user_menu"},
        {"name": "AdminMenu", "entry": "show_admin_menu"},
    ]
    transitions = [
        {"source": "initial", "target": "Welcome"},
        {"trigger": Command.LOGIN_USER, "source": "Welcome", "target": "UserMenu"},
        {"trigger": Command.LOGIN_ADMIN, "source": "Welcome", "target": "AdminMenu"},
        {"trigger": Command.LOGOUT, "source": "UserMenu", "target": "Welcome"},
        {"trigger": Command.LOGOUT, "source": "AdminMenu", "target": "Welcome"},
        {"trigger": "restart", "source": "UserMenu", "target": "UserMenu"},
        {"trigger": "restart", "source": "AdminMenu", "target": "AdminMenu"},
        {"trigger": "restart", "source": "Welcome", "target": "Welcome"},
    ]
    return Machine(name="app_ui", states=states, transitions=transitions, obj=app)


def on_connect(client, userdata, flags, rc):
    print("✅ Connected to MQTT broker.")
    client.subscribe(Topic.USER_ACK)
    client.subscribe(Topic.SCOOTER_INFO)
    client.subscribe(Topic.SCOOTER_STATE)


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    print(f"📩 MQTT message received on {topic}: {payload}")
    if topic == Topic.USER_ACK:
        if payload == Command.LOGIN_ADMIN:
            userdata.stm.send(Command.LOGIN_ADMIN)
        elif payload == Command.LOGIN_USER:
            userdata.stm.send(Command.LOGIN_USER)
        elif payload == Command.LOGOUT:
            userdata.stm.send(Command.LOGOUT)
        elif payload == "payment_failed":
            print("❌ Payment failed. Please try again.")
    elif topic == Topic.SCOOTER_INFO:
        info = json.loads(payload)
        userdata.show_scooter_info(info)

    elif topic == Topic.SCOOTER_STATE:
        # only two states come from scooter_service: "running" (unlocked) or "locked"
        if payload == "running":
            print("🟢 Scooter rented successfully! Enjoy your ride.")
        elif payload == "locked":
            print("🔒 Scooter returned successfully. Thanks for riding!")
        else:
            print(f"Scooter now in state: {payload}")
        userdata.stm.send("restart")


if __name__ == "__main__":
    app = AppUI()
    mqtt_client = mqtt.Client(client_id="app", userdata=app, protocol=mqtt.MQTTv311)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    app.mqtt_client = mqtt_client

    machine = create_machine(app)
    app.stm = machine
    driver = Driver()
    driver.add_machine(machine)
    driver.start()

    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    mqtt_client.loop_start()
