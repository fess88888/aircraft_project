# Учебный проект "Курсовая работа 3"
## Контекст
Проект получает данные о самолётах в воздушном пространстве нескольких стран
через открытый API [OpenSky Network](https://opensky-network.org/) и
географические координаты стран через [Nominatim](https://nominatim.openstreetmap.org/),
затем загружает всё в PostgreSQL.
## Установка
Клонируйте репозиторий
```
git clone git@github.com:fess88888/aircraft_project
```
## Структура проекта
| Файл | Описание |
|---|---|
| `config.py` | Конфигурация: параметры БД, URL API, список 12 стран |
| `models.py` | Dataclass-модели `Country` и `Aircraft` |
| `api_clients.py` | Абстрактный `APIClient` + `NominatimClient` + `OpenSkyClient` |
| `database.py` | `DatabaseManager`: создание таблиц, вставка данных |
| `db_manager.py` | `DBManager`: аналитические запросы к БД |
| `main.py` | Точка входа, оркестрация всех модулей |

## Запуск
```bash
# 1. Создать базу данных
psql -U postgres -c "CREATE DATABASE "DATABASE_NAME";" Пример: aircraft_db

# 2. Запустить проект
python main.py