from . import rental_service
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    client.subscribe("user/rent_scooter")

def on_message(client, userdata, msg):
    scooter_id = msg.payload.decode()
    print(f"Received rent request for scooter ID: {scooter_id}")
    success = rental_service.simulate_payment()

    print(f"Payment {'success' if success else 'fail'}")
    if success:
        client.publish("server/scooter/cmd", "unlock")
        client.publish("user/rent_status", "success")
    else:
        client.publish("server/scooter/cmd", "fail")
        client.publish("user/rent_status", "fail")

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect("localhost", 1883)
mqtt_client.loop_forever()

