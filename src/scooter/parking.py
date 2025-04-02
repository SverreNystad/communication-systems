from stmpy import Machine, Driver

class ScooterController:
    def __init__(self):
        self.stm = self.create_state_machine()

    def create_state_machine(self):
        t0 = {'source': 'initial', 'target': 'locked'}
        t1 = {'trigger': 'unlock', 'source': 'locked', 'target': 'running'}
        t2 = {'trigger': 'end_ride', 'source': 'running', 'target': 'check_parking'}
        t3 = {'trigger': 'parking_proper', 'source': 'check_parking', 'target': 'locked', 'effect': 'confirm_and_notify()'}
        t4 = {'trigger': 'parking_improper', 'source': 'check_parking', 'target': 'running', 'effect': 'notify_improper()'}
        t5 = {'trigger': 'request_info', 'source': 'locked', 'target': 'locked', 'effect': 'provide_info()'}

        states = [
            {'name': 'locked'},
            {'name': 'running'},
            {'name': 'check_parking'}
        ]

        return Machine(name='scooter', transitions=[t0, t1, t2, t3, t4, t5], states=states, obj=self)

    def confirm_and_notify(self):
        print("Proper parking confirmed. Notifying user...")

    def notify_improper(self):
        print("Improper parking. Please park properly.")

    def provide_info(self):
        print("Providing scooter info: credentials, current location...")