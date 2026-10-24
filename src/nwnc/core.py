
from . import APP_NAME, VERSION

HOST = "0.0.0.0"
PORT = 5000


def get_app_info():
    return {
        "name": APP_NAME,
        "version": VERSION,
    }
