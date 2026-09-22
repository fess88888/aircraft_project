import os

from dotenv import load_dotenv


"""Конфигурация проекта: параметры БД, URL API, список стран."""
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
DB_CONFIG = {
    "host": os.getenv("DATABASE_HOST"),
    "port": 5432,
    "dbname": os.getenv("DATABASE_NAME"),
    "user": os.getenv("DATABASE_USER"),
    "password": os.getenv("DATABASE_PASSWORD"),
}

print("DB_HOST:", os.getenv("DATABASE_HOST"))
print("DB_NAME:", os.getenv("DATABASE_NAME"))
print("DB_USER:", os.getenv("DATABASE_USER"))
print("DB_PASS:", os.getenv("DATABASE_PASSWORD"))

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OPENSKY_URL = "https://opensky-network.org/api/states/all"

USER_AGENT = "aircraft_project/1.0 (educational use)"

REQUEST_TIMEOUT = 30

NOMINATIM_DELAY = 1.0

COUNTRIES = [
    "Germany",
    "France",
    "Malta",
    "Spain",
    "Italy",
    "Turkey",
    "Canada",
    "China",
    "Japan",
    "Brazil",
    "Australia",
]
