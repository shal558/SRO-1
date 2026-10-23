"""Load 10 synthetic buildings and 30 directed relationships into Neo4j."""
from app import RouteApp

BUILDINGS = [
    ("B01", "Главный корпус", 5),
    ("B02", "Корпус информационных технологий", 4),
    ("B03", "Корпус инженерии", 3),
    ("B04", "Корпус экономики", 4),
    ("B05", "Научный корпус", 6),
    ("B06", "Библиотека", 3),
    ("B07", "Спортивный корпус", 2),
    ("B08", "Корпус общественных наук", 4),
    ("B09", "Лабораторный корпус", 5),
    ("B10", "Студенческий центр", 2),
]

# 15 undirected links; each is stored in both directions = 30 relationships.
CONNECTIONS = [
    ("B01", "B02", 250, 4, True),
    ("B01", "B03", 400, 6, True),
    ("B02", "B03", 150, 2, True),
    ("B02", "B04", 350, 5, True),
    ("B03", "B05", 300, 4, True),
    ("B04", "B05", 200, 3, True),
    ("B04", "B06", 450, 7, True),
    ("B05", "B06", 180, 3, True),
    ("B05", "B07", 500, 7, True),
    ("B06", "B07", 220, 3, True),
    ("B06", "B08", 320, 5, True),
    ("B07", "B08", 280, 4, True),
    ("B08", "B09", 350, 5, True),
    ("B09", "B10", 200, 3, True),
    ("B01", "B10", 600, 8, True),
]


def seed() -> None:
    app = RouteApp()
    try:
        print(app.verify_connection())
        app.create_constraints()
        for building_id, name, floors in BUILDINGS:
            app.create_building(
                building_id, name,
                address="Университетская территория",
                floors=floors,
            )
        for a, b, distance, minutes, accessible in CONNECTIONS:
            app.create_connection(
                a, b, distance, minutes, accessible, bidirectional=True
            )

        with app.driver.session(database=app.database) as session:
            counts = session.run("""
                MATCH (b:Building)
                WITH count(b) AS buildings
                MATCH ()-[r:CONNECTED_TO]->()
                RETURN buildings, count(r) AS relationships
            """).single()
        print(f"Готово: {counts['buildings']} корпусов, "
              f"{counts['relationships']} направленных связей.")
        print("Повторный запуск обновляет узлы и связи, не создавая дубликаты.")
    finally:
        app.close()


if __name__ == "__main__":
    seed()
