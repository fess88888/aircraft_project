"""Точка входа: оркестрация получения данных и загрузки в БД."""

from src.api_clients import NominatimClient, OpenSkyClient
from src.database import DatabaseManager
from src.db_manager import DBManager

import config


def match_aircraft_to_countries(
    aircrafts: list, countries: list
) -> list:
    """Сопоставляет самолёты со странами по попаданию координат в bounding box.

    Args:
        aircrafts: Список объектов Aircraft.
        countries: Список объектов Country с заполненными id.

    Returns:
        Список объектов Aircraft, у которых country_id заполнен
        (только те, что попали в воздушное пространство отслеживаемых стран).
    """
    matched: list = []

    for aircraft in aircrafts:
        if aircraft.latitude is None or aircraft.longitude is None:
            continue

        for country in countries:
            if (
                country.bbox_south <= aircraft.latitude <= country.bbox_north
                and country.bbox_west <= aircraft.longitude <= country.bbox_east
            ):
                aircraft.country_id = country.id
                matched.append(aircraft)
                break

    return matched


def main() -> None:
    """Основная функция: получение данных из API и загрузка в БД."""
    print("=" * 60)
    print("  Проект: Отслеживание самолётов через OpenSky API")
    print("=" * 60)

    # Получение координат стран через Nominatim
    print("\n[1/5] Получение координат стран (Nominatim) ...")
    nominatim = NominatimClient()
    countries = nominatim.fetch_all(config.COUNTRIES)
    print(f"  Получено стран: {len(countries)}")

    # Получение данных о самолётах через OpenSky
    print("\n[2/5] Получение данных о самолётах (OpenSky) ...")
    opensky = OpenSkyClient()
    all_aircrafts = opensky.fetch()
    print(f"  Получено воздушных судов всего: {len(all_aircrafts)}")

    # Запись стран в БД
    print("\n[3/5] Запись стран в БД ...")
    db = DatabaseManager()
    db.connect()
    db.create_tables()
    db.clear_tables()

    for country in countries:
        country.id = db.insert_country(country)
        print(f"  Добавлена страна: {country.name} (id={country.id})")

    # Сопоставление и запись самолётов
    print("\n[4/5] Сопоставление самолётов со странами ...")
    matched_aircrafts = match_aircraft_to_countries(all_aircrafts, countries)
    print(f"  Сопоставлено судов со странами: {len(matched_aircrafts)}")

    print("  Запись самолётов в БД ...")
    inserted = db.insert_aeroplanes(matched_aircrafts)
    print(f"  Записано судов в БД: {inserted}")

    db.disconnect()

    # Демонстрация работы DBManager
    print("\n[5/5] Демонстрация работы DBManager ...")
    manager = DBManager()
    manager.connect()

    # Страны и количество самолётов
    print("\n--- Страны и количество самолётов ---")
    counts = manager.get_countries_and_aeroplanes_count()
    for row in counts:
        print(f"  {row['name']}: {row['aeroplanes_count']} судов")

    # Все воздушные суда (первые 10 для демонстрации)
    print("\n--- Все воздушные суда (первые 10) ---")
    all_planes = manager.get_all_aeroplanes()
    for plane in all_planes[:10]:
        print(
            f"  {plane['icao24']} | {plane['callsign']} | "
            f"скорость: {plane['velocity']} | страна: {plane['country_name']}"
        )
    print(f"  ...всего записей: {len(all_planes)}")

    # Средняя скорость
    print("\n--- Средняя скорость ---")
    avg_speed = manager.get_avg_speed()
    if avg_speed is not None:
        print(f"  Средняя скорость: {avg_speed:.2f} м/с ({avg_speed * 3.6:.2f} км/ч)")
    else:
        print("  Нет данных для расчёта средней скорости")

    # Самолёты выше средней скорости (первые 10)
    print("\n--- Самолёты со скоростью выше средней (первые 10) ---")
    fast_planes = manager.get_aeroplanes_with_higher_speed()
    for plane in fast_planes[:10]:
        print(f"  {plane['icao24']} | {plane['callsign']} | скорость: {plane['velocity']} м/с")
    print(f"  ...всего таких судов: {len(fast_planes)}")

    # Поиск по ключевому слову в позывном
    print("\n--- Поиск по позывному 'ACA' (Air Canada) ---")
    keyword_planes = manager.get_aeroplanes_with_keyword("ACA")
    for plane in keyword_planes:
        print(
            f"  {plane['icao24']} | {plane['callsign']} | "
            f"страна: {plane['origin_country']}"
        )
    print(f"  ...найдено судов: {len(keyword_planes)}")

    manager.disconnect()
    print("\nГотово! ✈️")


if __name__ == "__main__":
    main()
