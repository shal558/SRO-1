# University Routes — вариант 19

Прототип поиска маршрутов между учебными корпусами на Python и Neo4j.

## Модель
- `(:Building {id, name, address, floors})` — учебный корпус.
- `(:Building)-[:CONNECTED_TO {distance, walking_time, accessible}]->(:Building)` — направленный переход.
- Для двустороннего прохода создаются две направленные связи.

## Требования
- Python 3.10+
- Neo4j Sandbox либо доступный Neo4j DBMS с Bolt-подключением.

## Запуск
1. Создайте или откройте Neo4j Sandbox.
2. В панели подключения скопируйте Bolt URI, username, password и database.
3. В корне проекта создайте `.env` на основе `.env.example` и заполните параметры. Не публикуйте `.env`.
4. Создайте виртуальное окружение:
   - Windows: `py -m venv .venv`
   - PowerShell: `.venv\\Scripts\\Activate.ps1`
   - CMD: `.venv\\Scripts\\activate.bat`
5. Установите зависимости: `python -m pip install -r requirements.txt`
6. Загрузите синтетические данные: `python seed.py`
7. Запустите демонстрацию: `python app.py`

`seed.py` создаёт 10 узлов и 30 направленных связей. Повторный запуск безопасно обновляет те же узлы и связи.

## Демонстрационные методы
- `create_building`, `get_building`, `list_buildings`
- `update_building`, `delete_building`
- `create_connection`, `update_connection`, `delete_connection`
- `neighbors`
- `shortest_hop_route` — минимум переходов
- `ranked_routes(metric="distance")` — сортировка простых маршрутов по расстоянию
- `ranked_routes(metric="walking_time")` — сортировка простых маршрутов по времени

## Примечание
`ranked_routes` перебирает простые пути с ограничением количества переходов и предназначен для небольшого учебного графа, не для крупных сетей.
