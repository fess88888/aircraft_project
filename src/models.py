"""Dataclass-модели данных: Country и Aircraft."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Country:
    """Модель страны с географическими координатами и bounding box.

    Attributes:
        name: Название страны.
        latitude: Широта центра страны (из Nominatim).
        longitude: Долгота центра страны (из Nominatim).
        bbox_south: Южная граница bounding box.
        bbox_north: Северная граница bounding box.
        bbox_west: Западная граница bounding box.
        bbox_east: Восточная граница bounding box.
    """

    name: str
    latitude: float
    longitude: float
    bbox_south: float
    bbox_north: float
    bbox_west: float
    bbox_east: float
    id: Optional[int] = None


@dataclass
class Aircraft:
    """Модель воздушного судна из OpenSky API.

    Attributes:
        icao24: Уникальный ICAO24-адрес трансондера.
        callsign: Позывной судна (может быть None).
        origin_country: Страна регистрации.
        longitude: Долгота.
        latitude: Широта.
        baro_altitude: Барометрическая высота (метры).
        on_ground: Находится ли на земле.
        velocity: Скорость (м/с).
        true_track: Истинный курс (градусы).
        vertical_rate: Вертикальная скорость (м/с).
        geo_altitude: Геометрическая высота (метры).
        squawk: Код squawk.
        country_id: FK на countries(id), если судно сопоставлено со страной.
        id: PK в БД (назначается при вставке).
    """

    icao24: str
    callsign: Optional[str]
    origin_country: str
    longitude: Optional[float]
    latitude: Optional[float]
    baro_altitude: Optional[float]
    on_ground: bool
    velocity: Optional[float]
    true_track: Optional[float]
    vertical_rate: Optional[float]
    geo_altitude: Optional[float]
    squawk: Optional[str]
    country_id: Optional[int] = None
    id: Optional[int] = None
