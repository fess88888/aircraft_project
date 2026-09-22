"""Управление схемой БД PostgreSQL и вставкой данных."""

from typing import Optional, Any

import psycopg
from psycopg import Connection as PgConnection

import config
from src.models import Aircraft, Country


class DatabaseManager:
    """Управляет созданием таблиц и записью данных в PostgreSQL.

    Отвечает за DDL-операции (создание/очистка таблиц) и DML-операции
    (вставка стран и самолётов). Не выполняет аналитические запросы —
    для этого предназначен класс DBManager.
    """

    def __init__(self, db_config: dict[str, Any] | None = None) -> None:
        """Инициализирует менеджер и устанавливает соединение с БД.

        Args:
            db_config: Словарь с параметрами подключения.
                       Если None — берётся из config.DB_CONFIG.
        """
        self.db_config = db_config or config.DB_CONFIG
        self.conn: Optional[PgConnection] = None

    def connect(self) -> None:
        """Устанавливает соединение с PostgreSQL, обходя баг кодировки на Windows."""
        import os

        for key in list(os.environ.keys()):
            if key.upper().startswith("PG"):
                del os.environ[key]

        os.environ["PGPASSFILE"] = "nul"
        os.environ["PGSERVICEFILE"] = "nul"
        os.environ["PGCLIENTENCODING"] = "UTF8"

        dsn = (
            f"host=127.0.0.1 "
            f"port={self.db_config['port']} "
            f"dbname={self.db_config['dbname']} "
            f"user={self.db_config['user']} "
            f"password={self.db_config['password']}"
        )

        self.conn = psycopg.connect(dsn)
        self.conn.autocommit = False
        print("[БД] Соединение установлено")

    def disconnect(self) -> None:
        """Закрывает соединение с БД."""
        if self.conn and not self.conn.closed:
            self.conn.close()
            print("[БД] Соединение закрыто")

    def create_tables(self) -> None:
        """Создаёт таблицы countries и aeroplanes, если они не существуют.

        Схема:
        - countries: справочник стран с координатами и bounding box
        - aeroplanes: данные о воздушных судах с FK на countries
        """
        if not self.conn:
            raise RuntimeError("Соединение с БД не установлено")

        with self.conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS countries (
                    id          SERIAL PRIMARY KEY,
                    name        VARCHAR(100) NOT NULL UNIQUE,
                    latitude    FLOAT NOT NULL,
                    longitude   FLOAT NOT NULL,
                    bbox_south  FLOAT NOT NULL,
                    bbox_north  FLOAT NOT NULL,
                    bbox_west   FLOAT NOT NULL,
                    bbox_east   FLOAT NOT NULL
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aeroplanes (
                    id              SERIAL PRIMARY KEY,
                    icao24          VARCHAR(20),
                    callsign        VARCHAR(50),
                    origin_country  VARCHAR(100),
                    longitude       FLOAT,
                    latitude        FLOAT,
                    baro_altitude   FLOAT,
                    on_ground       BOOLEAN,
                    velocity        FLOAT,
                    true_track      FLOAT,
                    vertical_rate   FLOAT,
                    geo_altitude    FLOAT,
                    squawk          VARCHAR(10),
                    country_id      INTEGER REFERENCES countries(id)
                );
            """)

            self.conn.commit()
            print("[БД] Таблицы созданы/проверены")

    def clear_tables(self) -> None:
        """Очищает обе таблицы (сначала aeroplanes из-за FK)."""
        if not self.conn:
            raise RuntimeError("Соединение с БД не установлено")

        with self.conn.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE aeroplanes RESTART IDENTITY CASCADE;")
            cursor.execute("TRUNCATE TABLE countries RESTART IDENTITY CASCADE;")
            self.conn.commit()
            print("[БД] Таблицы очищены")

    def insert_country(self, country: Country) -> int:
        """Вставляет страну в таблицу countries и возвращает её id.

        Args:
            country: Объект Country для вставки.

        Returns:
            id вставленной записи.
        """
        if not self.conn:
            raise RuntimeError("Соединение с БД не установлено")

        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO countries
                    (name, latitude, longitude,
                     bbox_south, bbox_north, bbox_west, bbox_east)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    country.name,
                    country.latitude,
                    country.longitude,
                    country.bbox_south,
                    country.bbox_north,
                    country.bbox_west,
                    country.bbox_east,
                ),
            )
            country_id = cursor.fetchone()[0]
            self.conn.commit()
            return country_id

    def insert_aeroplanes(self, aircrafts: list[Aircraft]) -> int:
        """Массово вставляет список воздушных судов в таблицу aeroplanes.

        Args:
            aircrafts: Список объектов Aircraft.

        Returns:
            Количество вставленных записей.
        """
        if not self.conn:
            raise RuntimeError("Соединение с БД не установлено")
        if not aircrafts:
            return 0

        rows = [
            (
                a.icao24,
                a.callsign,
                a.origin_country,
                a.longitude,
                a.latitude,
                a.baro_altitude,
                a.on_ground,
                a.velocity,
                a.true_track,
                a.vertical_rate,
                a.geo_altitude,
                a.squawk,
                a.country_id,
            )
            for a in aircrafts
        ]

        with self.conn.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO aeroplanes
                    (icao24, callsign, origin_country, longitude, latitude,
                     baro_altitude, on_ground, velocity, true_track,
                     vertical_rate, geo_altitude, squawk, country_id)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """,
                rows,
            )
            self.conn.commit()
            return len(rows)
