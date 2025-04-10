from stmpy import Machine, Driver
import paho.mqtt.client as mqtt

class AppUI:

    def __init__(self):
        self.stm = None
        self.mqtt_client = None

    def send(self, event):
        self.mqtt_client.publish("user/command", event)

    def show_welcome(self):
        print("\n== Welcome ==")
        print("1. Login as User")
        print("2. Login as Admin")
        print("0. Exit")
        choice = input("Select: ")
        if choice == "1":
            self.send("evt_login_user")
            self.stm.send("evt_login_user")
        elif choice == "2":
            self.send("evt_login_admin")
            self.stm.send("evt_login_admin")
        elif choice == "0":
            print("Goodbye!")
            exit()
        else:
            print("Invalid choice.")
            self.stm.send("restart")

    def show_user_menu(self):
        print("\n== User Menu ==")
        print("1. Rent scooter")
        print("2. End ride")
        print("3. Logout")
        choice = input("Select: ")
        if choice == "1":
            self.send("evt_recieved_open_request")
        elif choice == "2":
            self.send("evt_recieved_close_request")
        elif choice == "3":
            self.send("evt_logout")
            self.stm.send("evt_logout")
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
            self.send("evt_request_info")
        elif choice == "2":
            self.send("evt_deactivate")
        elif choice == "3":
            self.send("evt_activate")
        elif choice == "4":
            self.send("evt_logout")
            self.stm.send("evt_logout")
        else:
            print("Invalid choice.")
        self.stm.send("restart")

# -----------------------
# STMPY Machine
# -----------------------

def create_machine(app: AppUI):
    states = [
        {"name": "Welcome", "entry": "show_welcome"},
        {"name": "UserMenu", "entry": "show_user_menu"},
        {"name": "AdminMenu", "entry": "show_admin_menu"},
    ]

    transitions = [
        {"source": "initial", "target": "Welcome"},
        {"trigger": "evt_login_user", "source": "Welcome", "target": "UserMenu"},
        {"trigger": "evt_login_admin", "source": "Welcome", "target": "AdminMenu"},
        {"trigger": "evt_logout", "source": "UserMenu", "target": "Welcome"},
        {"trigger": "evt_logout", "source": "AdminMenu", "target": "Welcome"},
        {"trigger": "restart", "source": "UserMenu", "target": "UserMenu"},
        {"trigger": "restart", "source": "AdminMenu", "target": "AdminMenu"},
        {"trigger": "restart", "source": "Welcome", "target": "Welcome"},
    ]

    return Machine(name="app_ui", states=states, transitions=transitions, obj=app)

# -----------------------
# MQTT Setup
# -----------------------

def on_connect(client, userdata, flags, rc):
    print("✅ Connected to MQTT broker.")

# -----------------------
# App Entry
# -----------------------

app = AppUI()

mqtt_client = mqtt.Client(client_id="", userdata=app, protocol=mqtt.MQTTv311)
mqtt_client.on_connect = on_connect
app.mqtt_client = mqtt_client

machine = create_machine(app)
app.stm = machine

driver = Driver()
driver.add_machine(machine)
driver.start()

mqtt_client.connect("localhost", 1883)
mqtt_client.loop_start()

# Start by triggering the initial view
app.stm.send("restart")
