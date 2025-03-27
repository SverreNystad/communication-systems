from gpiozero import MotionSensor

gpio = 12
# out plugged into GPIO12
pir = MotionSensor(gpio)
while True:
    print("Continue scanning for humans...")
    pir.wait_for_motion()
    print("Moving human detected! Destroy human!")
    pir.wait_for_no_motion()
    print("Human deactivated...")
