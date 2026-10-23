"""University building route demo backed by Neo4j."""
import os
from typing import Any

from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError

load_dotenv()


class RouteApp:
    def __init__(self, uri: str | None = None, username: str | None = None,
                 password: str | None = None, database: str | None = None):
        self.uri = uri or os.getenv("NEO4J_URI", "")
        self.username = username or os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "")
        self.database = database or os.getenv("NEO4J_DATABASE", "neo4j")
        if not self.uri or not self.password:
            raise ValueError(
                "Neo4j settings are missing. Copy .env.example to .env and set "
                "NEO4J_URI, NEO4J_USERNAME and NEO4J_PASSWORD."
            )
        self.driver = GraphDatabase.driver(
            self.uri, auth=(self.username, self.password)
        )

    def close(self) -> None:
        self.driver.close()

    def verify_connection(self) -> str:
        self.driver.verify_connectivity()
        return "Connection to Neo4j: OK"

    def create_constraints(self) -> None:
        with self.driver.session(database=self.database) as session:
            session.run("""
                CREATE CONSTRAINT building_id_unique IF NOT EXISTS
                FOR (b:Building) REQUIRE b.id IS UNIQUE
            """).consume()

    def create_building(self, building_id: str, name: str,
                        address: str = "University campus", floors: int = 1) -> dict[str, Any] | None:
        if floors < 1:
            raise ValueError("floors must be at least 1")
        with self.driver.session(database=self.database) as session:
            record = session.run("""
                MERGE (b:Building {id: $id})
                SET b.name = $name, b.address = $address, b.floors = $floors
                RETURN b {.*} AS building
            """, id=building_id, name=name, address=address, floors=floors).single()
            return dict(record["building"]) if record else None

    def get_building(self, building_id: str) -> dict[str, Any] | None:
        with self.driver.session(database=self.database) as session:
            record = session.run("""
                MATCH (b:Building {id: $id})
                RETURN b {.*} AS building
            """, id=building_id).single()
            return dict(record["building"]) if record else None

    def list_buildings(self) -> list[dict[str, Any]]:
        with self.driver.session(database=self.database) as session:
            records = session.run("""
                MATCH (b:Building)
                RETURN b {.*} AS building
                ORDER BY b.id
            """)
            return [dict(r["building"]) for r in records]

    def update_building(self, building_id: str, name: str | None = None,
                        address: str | None = None, floors: int | None = None) -> dict[str, Any] | None:
        if floors is not None and floors < 1:
            raise ValueError("floors must be at least 1")
        with self.driver.session(database=self.database) as session:
            record = session.run("""
                MATCH (b:Building {id: $id})
                SET b.name = coalesce($name, b.name),
                    b.address = coalesce($address, b.address),
                    b.floors = coalesce($floors, b.floors)
                RETURN b {.*} AS building
            """, id=building_id, name=name, address=address, floors=floors).single()
            return dict(record["building"]) if record else None

    def delete_building(self, building_id: str) -> bool:
        with self.driver.session(database=self.database) as session:
            record = session.run("""
                MATCH (b:Building {id: $id})
                WITH b, count(b) AS found
                DETACH DELETE b
                RETURN found
            """, id=building_id).single()
            return bool(record and record["found"])

    def create_connection(self, from_id: str, to_id: str, distance: int,
                          walking_time: int, accessible: bool = True,
                          bidirectional: bool = True) -> int:
        if from_id == to_id:
            raise ValueError("A building cannot be connected to itself")
        if distance <= 0 or walking_time <= 0:
            raise ValueError("distance and walking_time must be positive")
        with self.driver.session(database=self.database) as session:
            result = session.run("""
                MATCH (a:Building {id: $from_id})
                MATCH (b:Building {id: $to_id})
                MERGE (a)-[r:CONNECTED_TO]->(b)
                SET r.distance = $distance,
                    r.walking_time = $walking_time,
                    r.accessible = $accessible
                WITH a, b
                FOREACH (_ IN CASE WHEN $bidirectional THEN [1] ELSE [] END |
                    MERGE (b)-[r2:CONNECTED_TO]->(a)
                    SET r2.distance = $distance,
                        r2.walking_time = $walking_time,
                        r2.accessible = $accessible
                )
                RETURN CASE WHEN $bidirectional THEN 2 ELSE 1 END AS created
            """, from_id=from_id, to_id=to_id, distance=distance,
                walking_time=walking_time, accessible=accessible,
                bidirectional=bidirectional).single()
            if result is None:
                raise ValueError("Both building IDs must exist before connecting them")
            return result["created"]

    def update_connection(self, from_id: str, to_id: str, distance: int | None = None,
                          walking_time: int | None = None,
                          accessible: bool | None = None) -> int:
        if distance is not None and distance <= 0:
            raise ValueError("distance must be positive")
        if walking_time is not None and walking_time <= 0:
            raise ValueError("walking_time must be positive")
        with self.driver.session(database=self.database) as session:
            result = session.run("""
                MATCH (a:Building {id: $from_id})-[r:CONNECTED_TO]->(b:Building {id: $to_id})
                SET r.distance = coalesce($distance, r.distance),
                    r.walking_time = coalesce($walking_time, r.walking_time),
                    r.accessible = coalesce($accessible, r.accessible)
                RETURN count(r) AS updated
            """, from_id=from_id, to_id=to_id, distance=distance,
                walking_time=walking_time, accessible=accessible).single()
            return result["updated"] if result else 0

    def delete_connection(self, from_id: str, to_id: str,
                          bidirectional: bool = False) -> int:
        with self.driver.session(database=self.database) as session:
            if bidirectional:
                result = session.run("""
                    MATCH (a:Building {id: $from_id})-[r:CONNECTED_TO]-(b:Building {id: $to_id})
                    WITH collect(r) AS rels
                    FOREACH (rel IN rels | DELETE rel)
                    RETURN size(rels) AS deleted
                """, from_id=from_id, to_id=to_id).single()
            else:
                result = session.run("""
                    MATCH (:Building {id: $from_id})-[r:CONNECTED_TO]->(:Building {id: $to_id})
                    DELETE r
                    RETURN count(r) AS deleted
                """, from_id=from_id, to_id=to_id).single()
            return result["deleted"] if result else 0

    def neighbors(self, building_id: str) -> list[dict[str, Any]]:
        with self.driver.session(database=self.database) as session:
            records = session.run("""
                MATCH (b:Building {id: $id})-[r:CONNECTED_TO]->(neighbor:Building)
                RETURN neighbor.id AS id, neighbor.name AS name,
                       r.distance AS distance, r.walking_time AS walking_time,
                       r.accessible AS accessible
                ORDER BY distance
            """, id=building_id)
            return [dict(r) for r in records]

    def shortest_hop_route(self, from_id: str, to_id: str, max_hops: int = 9) -> dict[str, Any] | None:
        if not 1 <= max_hops <= 20:
            raise ValueError("max_hops must be between 1 and 20")
        with self.driver.session(database=self.database) as session:
            record = session.run("""
                MATCH (start:Building {id: $from_id})
                MATCH (finish:Building {id: $to_id})
                MATCH p = shortestPath((start)-[:CONNECTED_TO*..20]-(finish))
                WHERE length(p) <= $max_hops
                RETURN [n IN nodes(p) | n.name] AS route,
                       length(p) AS hops,
                       reduce(total = 0, r IN relationships(p) | total + r.distance) AS distance,
                       reduce(total = 0, r IN relationships(p) | total + r.walking_time) AS time
            """, from_id=from_id, to_id=to_id, max_hops=max_hops).single()
            return dict(record) if record else None

    def ranked_routes(self, from_id: str, to_id: str, metric: str = "distance",
                      limit: int = 5, max_hops: int = 9) -> list[dict[str, Any]]:
        if metric not in {"distance", "walking_time"}:
            raise ValueError("metric must be 'distance' or 'walking_time'")
        if not 1 <= max_hops <= 12:
            raise ValueError("max_hops must be between 1 and 12")
        if not 1 <= limit <= 20:
            raise ValueError("limit must be between 1 and 20")
        order_field = "total_distance" if metric == "distance" else "total_time"
        query = f"""
            MATCH (start:Building {{id: $from_id}})
            MATCH (finish:Building {{id: $to_id}})
            MATCH p = (start)-[:CONNECTED_TO*1..{max_hops}]-(finish)
            WHERE all(n IN nodes(p) WHERE single(m IN nodes(p) WHERE m = n))
            WITH p,
                 reduce(total = 0, r IN relationships(p) | total + r.distance) AS total_distance,
                 reduce(total = 0, r IN relationships(p) | total + r.walking_time) AS total_time
            RETURN [n IN nodes(p) | n.id] AS route,
                   total_distance AS distance,
                   total_time AS time,
                   length(p) AS hops
            ORDER BY {order_field} ASC
            LIMIT $limit
        """
        with self.driver.session(database=self.database) as session:
            return [dict(r) for r in session.run(
                query, from_id=from_id, to_id=to_id, limit=limit
            )]


def main() -> None:
    app = RouteApp()
    try:
        print(app.verify_connection())
        app.create_constraints()
        print("\nУчебные корпуса:")
        for b in app.list_buildings():
            print(f'{b["id"]}: {b["name"]} ({b["floors"]} этажей)')
        print("\nМаршрут B01 -> B10 по числу переходов:")
        print(app.shortest_hop_route("B01", "B10"))
        print("\nПять маршрутов по расстоянию:")
        for route in app.ranked_routes("B01", "B10", metric="distance"):
            print(route)
    finally:
        app.close()


if __name__ == "__main__":
    try:
        main()
    except (ValueError, Neo4jError) as exc:
        raise SystemExit(f"Ошибка: {exc}") from exc
