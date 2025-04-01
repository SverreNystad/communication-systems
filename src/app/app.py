from scooter.rental import ScooterRental, create_machine
from stmpy import Driver
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("✅ Scooter connected to MQTT broker")
    client.subscribe("server/scooter/cmd")

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"📩 MQTT command received: {payload}")
    if payload == "unlock":
        userdata.payment_success = True
        userdata.stm.send("select_scooter")
    elif payload == "fail":
        userdata.payment_success = False
        userdata.stm.send("select_scooter")

# Create rental state machine and MQTT client
rental = ScooterRental(None)
mqtt_client = mqtt.Client(client_id="", userdata=rental, protocol=mqtt.MQTTv311)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
rental.mqtt_client = mqtt_client

# Create and start STMPY driver
machine = create_machine(rental)
rental.stm = machine
driver = Driver()
driver.add_machine(machine)
driver.start()

# Connect to broker and start loop
mqtt_client.connect("localhost", 1883)
mqtt_client.loop_forever()

