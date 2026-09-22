"""Класс DBManager для аналитических запросов к БД PostgreSQL."""

from typing import Any, Optional

import psycopg
from psycopg import Connection as PgConnection

import config


class DBManager:
    """Класс для аналитических запросов к БД PostgreSQL.

    Предоставляет методы для получения сводной информации о странах
    и воздушных судах, хранящихся в таблицах countries и aeroplanes.
    Использует psycopg2 для подключения к БД.
    """

    def __init__(self, db_config: Optional[dict[str, Any]] = None) -> None:
        """Инициализирует менеджер и устанавливает соединение с БД.

        Args:
            db_config: Словарь с параметрами подключения.
                       Если None — берётся из config.DB_CONFIG.
        """
        self.db_config = db_config or config.DB_CONFIG
        self.conn: Optional[PgConnection] = None

    def connect(self) -> None:
        """Устанавливает соединение с PostgreSQL."""
        self.conn = psycopg.connect(**self.db_config)
        print("[DBManager] Соединение установлено")

    def disconnect(self) -> None:
        """Закрывает соединение с БД."""
        if self.conn and not self.conn.closed:
            self.conn.close()
            print("[DBManager] Соединение закрыто")

    def get_countries_and_aeroplanes_count(self) -> list[dict[str, Any]]:
        """Получает список всех стран и количество самолётов в их воздушных пространствах.

        Использует LEFT JOIN, чтобы включить страны без самолётов.

        Returns:
            Список словарей с ключами 'name' и 'aeroplanes_count'.
        """
        query = """
            SELECT c.name,
                   COUNT(a.id) AS aeroplanes_count
            FROM countries c
            LEFT JOIN aeroplanes a ON a.country_id = c.id
            GROUP BY c.name
            ORDER BY aeroplanes_count DESC;
        """
        return self._execute_query(query)

    def get_all_aeroplanes(self) -> list[dict[str, Any]]:
        """Получает список всех воздушных судов с информацией о стране.

        Returns:
            Список словарей с полями самолёта и названием страны.
        """
        query = """
            SELECT a.icao24,
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
                   c.name AS country_name
            FROM aeroplanes a
            LEFT JOIN countries c ON a.country_id = c.id;
        """
        return self._execute_query(query)

    def get_avg_speed(self) -> Optional[float]:
        """Получает среднюю скорость по всем самолётам.

        Учитывает только суда с положительной скоростью (исключая
        нулевую скорость и None), так как нулевая скорость означает
        стоянку на земле и искажает среднее.

        Returns:
            Средняя скорость в м/с, или None если данных нет.
        """
        query = """
            SELECT AVG(velocity)
            FROM aeroplanes
            WHERE velocity IS NOT NULL AND velocity > 0;
        """
        result = self._execute_query(query)
        if result and result[0].get("avg") is not None:
            return float(result[0]["avg"])
        return None

    def get_aeroplanes_with_higher_speed(self) -> list[dict[str, Any]]:
        """Получает список всех самолётов, скорость которых выше средней.

        Returns:
            Список словарей с полями icao24, callsign, velocity.
        """
        query = """
            SELECT icao24,
                   callsign,
                   velocity
            FROM aeroplanes
            WHERE velocity > (
                SELECT AVG(velocity)
                FROM aeroplanes
                WHERE velocity IS NOT NULL AND velocity > 0
            )
            ORDER BY velocity DESC;
        """
        return self._execute_query(query)

    def get_aeroplanes_with_keyword(self, keyword: str) -> list[dict[str, Any]]:
        """Получает список самолётов, в позывном которых содержатся переданные символы.

        Поиск регистронезависимый (ILIKE).

        Args:
            keyword: Строка для поиска в позывном (например, 'ACA' для Air Canada).

        Returns:
            Список словарей с полями icao24, callsign, origin_country.
        """
        query = """
            SELECT icao24,
                   callsign,
                   origin_country
            FROM aeroplanes
            WHERE callsign ILIKE %s;
        """
        return self._execute_query(query, params=(f"%{keyword}%",))

    def _execute_query(
        self, query: str, params: Optional[tuple] = None
    ) -> list[dict[str, Any]]:
        """Выполняет SQL-запрос и возвращает результат как список словарей.

        Args:
            query: SQL-запрос с плейсхолдерами (%s).
            params: Кортеж параметров для подстановки (опционально).

        Returns:
            Список словарей, где ключи — имена колонок.
        """
        if not self.conn:
            raise RuntimeError("Соединение с БД не установлено")

        with self.conn.cursor() as cursor:
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

        return [dict(zip(columns, row)) for row in rows]
