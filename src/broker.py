from enum import StrEnum


MQTT_BROKER = "localhost"
MQTT_PORT = 1883


class Topic(StrEnum):
    SCOOTER_CMD = "server/scooter/cmd"
    USER_ACK = "user/ack"
    SCOOTER_INFO = "scooter/info"
    SERVER_CMD = "server/cmd"
    SERVER_ACK = "server/ack"


class Command(StrEnum):
    LOGIN_ADMIN = "evt_login_admin"
    LOGIN_USER = "evt_login_user"
    LOGIN = "evt_login"
    LOGOUT = "evt_logout"
    RECEIVED_OPEN_REQUEST = "evt_recieved_open_request"
    RECEIVED_CLOSE_REQUEST = "evt_recieved_close_request"
    ACK_OPEN_REQUEST = "ack_open_request"
    ACK_CLOSE_REQUEST = "evt_ack_close_request"
    UNLOCK_SCOOTER = "send_evt_unlock"
    LOCK_SCOOTER = "send_evt_lock"


"""
evt_login_admin
evt_login_user
evt_login
evt_logout
evt_recieved_open_request
evt_recieved_close_request
ack_open_request
evt_ack_close_request
"""
