from collections import defaultdict
from dataclasses import dataclass, field


@dataclass(frozen=True, order=True)
class Edge:
    source: str
    destination: str
    label: str = ""
    emphasized: bool = False

    def __str__(self) -> str:
        return self.render(base_module="")

    def render(self, base_module: str) -> str:
        return f'"{DotGraph.render_module(self.source, base_module)}" ->  "{DotGraph.render_module(self.destination, base_module)}"{self._render_attrs()}'

    def _render_attrs(self) -> str:
        attrs: dict[str, str] = {}
        if self.label:
            attrs["label"] = self.label
        if self.emphasized:
            attrs["style"] = "dashed"
        if attrs:
            joined_attrs = ", ".join([f'{key}="{value}"' for key, value in attrs.items()])
            return f" [{joined_attrs}]"
        else:
            return ""


@dataclass
class DotGraph:
    """
    A directed graph that can be rendered in DOT format.

    https://en.wikipedia.org/wiki/DOT_(graph_description_language)
    """

    title: str
    concentrate: bool = True
    depth: int = 1
    nodes: set[str] = field(default_factory=set)
    edges: set[Edge] = field(default_factory=set)

    def add_node(self, name: str) -> None:
        self.nodes.add(name)

    def add_edge(self, edge: Edge) -> None:
        self.edges.add(edge)

    def render(self) -> str:
        # concentrate=true means that we merge the lines together.
        indent = "    "
        lines = ["digraph {", f"{indent}node [fontname=helvetica]"]
        if self.concentrate:
            lines.append(f"{indent}concentrate=true")
        lines.extend(self._render_with_clusters(indent))
        for edge in sorted(self.edges):
            lines.append(f"{indent}{edge.render(self.title)}")
        lines.append("}")
        return "\n".join(lines) + "\n"

    def _render_with_clusters(self, indent: str) -> list[str]:
        """Render nodes with subgraph clusters (grouping nodes by immediate parent)."""
        parent_to_children: dict[str, set[str]] = defaultdict(set)
        for node in self.nodes:
            parent = node.rsplit(".", 1)[0]
            parent_to_children[parent].add(node)
        clustered_parents = {p: c for p, c in parent_to_children.items() if len(c) >= 1}
        standalone_nodes = {
            node
            for parent, children in parent_to_children.items()
            if parent not in clustered_parents
            for node in children
        }
        lines: list[str] = []
        # Render clusters: never create a root box; output base's children directly
        for child in sorted(parent_to_children.get(self.title, set())):
            if child in clustered_parents:
                self._render_cluster(
                    child,
                    indent,
                    indent,
                    clustered_parents,
                    lines,
                )
            elif self.title in clustered_parents:
                # Base has a cluster but we skip the root box; output child as top-level node
                lines.append(f'{indent}"{self.render_module(child, self.title)}"')
        for node in sorted(standalone_nodes):
            lines.append(f'{indent}"{self.render_module(node, self.title)}"')
        return lines

    def _render_cluster(
        self,
        parent: str,
        indent: str,
        current_indent: str,
        clustered_parents: dict[str, set[str]],
        lines: list[str],
    ) -> None:
        """Recursively render a cluster for parent and its nested clusters."""
        if parent not in clustered_parents:
            return
        children = clustered_parents[parent]
        cluster_id = "cluster_" + parent.replace(".", "_")
        label = self.render_module(parent, self.title) if parent != self.title else ""
        lines.append(f"{current_indent}subgraph {cluster_id} {{")
        lines.append(f'{current_indent}{indent}label="{label}"')
        nested_indent = current_indent + indent
        # Include the parent node in the box when it exists in the graph
        if parent in self.nodes:
            lines.append(f'{nested_indent}"{self.render_module(parent, self.title)}"')
        for node in sorted(children):
            if node in clustered_parents:
                lines.append(f'{nested_indent}"{self.render_module(node, self.title)}"')
                self._render_cluster(
                    node,
                    indent,
                    nested_indent,
                    clustered_parents,
                    lines,
                )
            else:
                lines.append(f'{nested_indent}"{self.render_module(node, self.title)}"')
        lines.append(f"{current_indent}}}")

    @staticmethod
    def render_module(module: str, base_module: str = "") -> str:
        # Render as relative module by stripping the base module prefix.
        if base_module and module.startswith(base_module + "."):
            relative = module[len(base_module) :]
            return relative  # Already starts with "."
        else:
            # Fallback: show as relative with just the last component.
            return f".{module.split('.')[-1]}"
