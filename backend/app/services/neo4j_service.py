from collections import deque
from threading import RLock


class Neo4jService:
    """In-memory graph adapter with the same responsibility as a graph service."""

    def __init__(self) -> None:
        self._nodes: dict[str, dict[str, str]] = {}
        self._edges: list[dict[str, object]] = []
        self._lock = RLock()

    def upsert_asset_node(
        self,
        *,
        asset_id: str,
        title: str,
        organisation_id: str,
    ) -> None:
        with self._lock:
            self._nodes[asset_id] = {
                "id": asset_id,
                "label": title,
                "kind": "asset",
                "organisation_id": organisation_id,
            }

    def link_assets(
        self,
        *,
        source_asset_id: str,
        target_asset_id: str,
        relation: str,
        score: float | None = None,
    ) -> None:
        with self._lock:
            edge = {
                "source": source_asset_id,
                "target": target_asset_id,
                "relation": relation,
                "score": score,
            }
            if edge not in self._edges:
                self._edges.append(edge)

    def get_propagation(self, asset_id: str) -> dict[str, object]:
        with self._lock:
            nodes = dict(self._nodes)
            edges = list(self._edges)

        if asset_id not in nodes:
            return {"asset_id": asset_id, "nodes": [], "edges": []}

        adjacency: dict[str, set[str]] = {}
        for edge in edges:
            source = str(edge["source"])
            target = str(edge["target"])
            adjacency.setdefault(source, set()).add(target)
            adjacency.setdefault(target, set()).add(source)

        visited: set[str] = set()
        queue: deque[str] = deque([asset_id])
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            for neighbor in adjacency.get(current, set()):
                if neighbor not in visited:
                    queue.append(neighbor)

        filtered_nodes = [
            {
                "id": node["id"],
                "label": node["label"],
                "kind": node["kind"],
            }
            for node_id, node in nodes.items()
            if node_id in visited
        ]
        filtered_edges = [
            edge
            for edge in edges
            if edge["source"] in visited and edge["target"] in visited
        ]
        return {"asset_id": asset_id, "nodes": filtered_nodes, "edges": filtered_edges}

