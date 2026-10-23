
from app import RouteApp

app = RouteApp()

try:
    print("1. CREATE — создание корпуса")
    created = app.create_building(
        "TEST01",
        "Тестовый корпус",
        "Тестовый адрес",
        2
    )
    print(created)

    print("\n2. READ — чтение корпуса")
    print(app.get_building("TEST01"))

    print("\n3. UPDATE — изменение корпуса")
    updated = app.update_building(
        "TEST01",
        name="Обновлённый тестовый корпус",
        floors=3
    )
    print(updated)

    print("\n4. CREATE — создание связи")
    print("Создано направленных связей:",
          app.create_connection("TEST01", "B01", 100, 2))

    print("\n5. READ — соседи тестового корпуса")
    print(app.neighbors("TEST01"))

    print("\n6. UPDATE — изменение связи")
    print("Обновлено связей:",
          app.update_connection("TEST01", "B01", distance=150))

    print("\n7. DELETE — удаление связи")
    print("Удалено связей:",
          app.delete_connection("TEST01", "B01", bidirectional=True))

    print("\n8. DELETE — удаление тестового корпуса")
    print("Удалён:", app.delete_building("TEST01"))

finally:
    app.close()
