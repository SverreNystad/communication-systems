from stmpy import Machine, Driver

class ScooterParking:
    def __init__(self, mqtt_client, allowed_parking_area):
        self.stm = self.create_state_machine()
        self.mqtt_client = mqtt_client
        self.allowed_parking_area = allowed_parking_area


    def get_location_data(self):
        return
    

    def check_parking(self):
        return 'parking_valid' if self.get_location_data() in self.allowed_parking_area else 'parking_invalid'
    

    def confirm_and_notify(self):
        self.mqtt_client.publish('scooter/state', 'Parking valid --> Scooter locked')
    

    def notify_invalid(self):
        self.mqtt_client.publish('scooter/state', 'Parking invalid!')
    

    def provide_info(self):
        return
    

    def create_state_machine(self):
        t0 = {'source': 'initial', 'target': 'locked'}
        t1 = {'trigger': 'unlock', 'source': 'locked', 'target': 'running'}
        t2 = {'trigger': 'end_ride', 'source': 'running', 'target': 'check_parking', 'function' : self.check_parking()}
        t3 = {'trigger': 'parking_valid', 'source': 'check_parking', 'target': 'locked', 'function': self.confirm_and_notify()}
        t4 = {'trigger': 'parking_invalid', 'source': 'check_parking', 'target': 'running', 'function': self.notify_invalid()}
        t5 = {'trigger': 'request_info', 'source': 'locked', 'target': 'locked', 'function': self.provide_info()}

        states = [
            {'name': 'locked'},
            {'name': 'running'},
            {'name': 'check_parking'}
        ]

        return Machine(name='scooter', transitions=[t0, t1, t2, t3, t4, t5], states=states, obj=self)