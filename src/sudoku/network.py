from typing import Optional

class Graph:
    def __init__(self) -> None:
        self.graph = {}
        raise NotImplementedError("Graph type class not yet implemented")
    
    def add_edge(self, u, v) -> None:
        if u not in self.graph:
            self.graph[u] = set()
        if v not in self.graph:
            self.graph[v] = set()
        self.graph[u].add(v)
        self.graph[v].add(u)
        return

    def adjacent_nodes(self, node) -> Optional[Graph]:
        if node not in self.graph:
            return None
        return self.graph[node]
    
