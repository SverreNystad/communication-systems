from enum import StrEnum

MQTT_BROKER = "10.22.128.63"  # "localhost"
MQTT_PORT = 1883


class Topic(StrEnum):
    USER_CMD = "user/command"
    USER_ACK = "user/ack"
    SCOOTER_CMD = "server/scooter/cmd"
    SCOOTER_STATE = "scooter/state"
    SCOOTER_ACK = "scooter/ack"
    SCOOTER_INFO = "scooter/info"
    SERVER_CMD = "server/cmd"
    SERVER_ACK = "server/ack"


class Command(StrEnum):
    LOGIN_ADMIN = "evt_login_admin"
    LOGIN_USER = "evt_login_user"
    LOGIN = "evt_login"
    LOGOUT = "evt_logout"
    RECEIVED_OPEN_REQUEST = "evt_received_open_request"
    RECEIVED_CLOSE_REQUEST = "evt_received_close_request"
    ACK_OPEN_REQUEST = "ack_open_request"
    ACK_CLOSE_REQUEST = "evt_ack_close_request"
    UNLOCK_SCOOTER = "send_evt_unlock"
    LOCK_SCOOTER = "send_evt_lock"
    REQUEST_INFO = "evt_request_info"
