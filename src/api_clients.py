"""Клиенты для внешних API: Nominatim (геокодинг) и OpenSky (самолёты)."""

import time
from abc import ABC, abstractmethod
from typing import Any, Optional

import requests

import config
from src.models import Aircraft, Country


class APIClient(ABC):
    """Абстрактный базовый класс для клиентов внешних API.

    Реализует общий механизм HTTP-запросов и обработки ошибок.
    Конкретные клиенты наследуются от него и реализуют метод fetch().
    """

    def __init__(self, base_url: str) -> None:
        """Инициализирует клиент с базовым URL.

        Args:
            base_url: Базовый URL API.
        """
        self.base_url = base_url

    def _get(self, params: dict[str, Any]) -> dict | list:
        """Выполняет GET-запрос и возвращает распарсенный JSON.

        Args:
            params: Словарь параметров запроса.

        Returns:
            Распарсенный JSON-ответ (dict или list).

        Raises:
            RuntimeError: Если HTTP-запрос завершился ошибкой.
        """
        headers = {"User-Agent": config.USER_AGENT}
        try:
            response = requests.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=config.REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise RuntimeError(f"Ошибка запроса к {self.base_url}: {exc}") from exc

    @abstractmethod
    def fetch(self, *args: Any, **kwargs: Any) -> Any:
        """Абстрактный метод получения данных от API."""
        ...


class NominatimClient(APIClient):
    """Клиент Nominatim API для получения географических координат стран.

    Nominatim требует User-Agent и задержку 1 секунда между запросами.
    """

    def __init__(self) -> None:
        """Инициализирует клиент с URL Nominatim из конфигурации."""
        super().__init__(config.NOMINATIM_URL)

    def fetch(self, country_name: str) -> Optional[Country]:
        """Получает координаты и bounding box страны по её названию.

        Args:
            country_name: Название страны на английском.

        Returns:
            Объект Country с координатами, или None если страна не найдена.
        """
        params = {
            "q": country_name,
            "format": "json",
            "limit": 1,
        }
        data = self._get(params)

        if not data:
            print(f"  [!] Nominatim: страна '{country_name}' не найдена")
            return None

        item = data[0]
        bbox = item["boundingbox"]  # [south, north, west, east]

        country = Country(
            name=country_name,
            latitude=float(item["lat"]),
            longitude=float(item["lon"]),
            bbox_south=float(bbox[0]),
            bbox_north=float(bbox[1]),
            bbox_west=float(bbox[2]),
            bbox_east=float(bbox[3]),
        )
        return country

    def fetch_all(self, country_names: list[str]) -> list[Country]:
        """Получает координаты для списка стран с увеличенной задержкой и retry-логикой."""
        countries: list[Country] = []

        # Увеличиваем задержку до 3 секунд — это сильно снижает риск блокировки
        delay = 3.0
        max_retries = 3

        for name in country_names:
            print(f"  Получение координат: {name} ...")
            country = None

            for attempt in range(1, max_retries + 1):
                try:
                    country = self.fetch(name)
                    if country:
                        countries.append(country)
                    break  # Успех — выходим из цикла попыток
                except RuntimeError as e:
                    print(f"    Попытка {attempt}/{max_retries} не удалась: {e}")
                    if attempt == max_retries:
                        print(f"    Пропускаем страну {name} из-за постоянных ошибок.")
                    else:
                        # Увеличиваем задержку для следующей попытки (экспоненциальная задержка)
                        time.sleep(delay * attempt)

            # Фиксированная пауза между странами
            time.sleep(delay)

        return countries


class OpenSkyClient(APIClient):
    """Клиент OpenSky API для получения данных о самолётах в воздухе."""

    def __init__(self) -> None:
        """Инициализирует клиент с URL OpenSky из конфигурации."""
        super().__init__(config.OPENSKY_URL)

    def fetch(self, *args: Any, **kwargs: Any) -> list[Aircraft]:
        """Получает список всех воздушных судов из OpenSky API.

        Returns:
            Список объектов Aircraft.
        """
        data = self._get({})
        states = data.get("states")
        if not states:
            print("  [!] OpenSky: нет данных о самолётах")
            return []

        aircrafts: list[Aircraft] = []
        for state in states:
            aircraft = self._parse_state(state)
            aircrafts.append(aircraft)
        return aircrafts

    @staticmethod
    def _parse_state(state: list) -> Aircraft:
        """Преобразует массив состояния судна из OpenSky в объект Aircraft.

        Порядок полей в массиве OpenSky:
        0: icao24, 1: callsign, 2: origin_country, 3: time_position,
        4: last_contact, 5: longitude, 6: latitude, 7: baro_altitude,
        8: on_ground, 9: velocity, 10: true_track, 11: vertical_rate,
        12: sensors, 13: geo_altitude, 14: squawk, 15: spi, 16: position_source

        Args:
            state: Массив значений из ответа OpenSky.

        Returns:
            Объект Aircraft.
        """
        return Aircraft(
            icao24=state[0] or "",
            callsign=state[1].strip() if state[1] else None,
            origin_country=state[2] or "",
            longitude=state[5],
            latitude=state[6],
            baro_altitude=state[7],
            on_ground=bool(state[8]),
            velocity=state[9],
            true_track=state[10],
            vertical_rate=state[11],
            geo_altitude=state[13],
            squawk=state[14],
            country_id=None,
        )
