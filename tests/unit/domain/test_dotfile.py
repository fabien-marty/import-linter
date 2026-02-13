from importlinter.domain.dotfile import DotGraph, Edge


class TestDotGraph:
    def test_render_empty_graph(self):
        dot = DotGraph(title="mypackage")
        rendered = dot.render()
        assert "digraph" in rendered
        assert "concentrate=true" in rendered

    def test_concentrate_false(self):
        dot = DotGraph(title="mypackage", concentrate=False)
        rendered = dot.render()
        assert "concentrate=true" not in rendered

    def test_render_with_nodes_and_edges(self):
        dot = DotGraph(title="mypackage.foo")
        dot.add_node("mypackage.foo.bar")
        dot.add_node("mypackage.foo.baz")
        dot.add_edge(Edge(source="mypackage.foo.bar", destination="mypackage.foo.baz"))

        rendered = dot.render()

        # No root box; .bar and .baz at top level
        assert "subgraph cluster_mypackage_foo" not in rendered
        assert '".bar"' in rendered
        assert '".baz"' in rendered

    def test_render_with_depth_2(self):
        dot = DotGraph(title="mypackage.foo", depth=2)
        dot.add_node("mypackage.foo.blue")
        dot.add_node("mypackage.foo.green")
        dot.add_node("mypackage.foo.blue.alpha")
        dot.add_edge(Edge(source="mypackage.foo.blue.alpha", destination="mypackage.foo.green"))

        rendered = dot.render()

        # No root box; .blue, .green, .blue.alpha at top level
        assert "subgraph cluster_mypackage_foo" not in rendered
        assert '".blue"' in rendered
        assert '".green"' in rendered
        assert '".blue.alpha"' in rendered

    def test_render_with_depth_2_and_clusters(self):
        """Nested clusters: .blue/.green in outer cluster, .blue.alpha/.blue.beta in inner cluster."""
        dot = DotGraph(title="mypackage.foo", depth=2)
        dot.add_node("mypackage.foo.blue")
        dot.add_node("mypackage.foo.green")
        dot.add_node("mypackage.foo.blue.alpha")
        dot.add_node("mypackage.foo.blue.beta")
        dot.add_node("mypackage.foo.green.gamma")
        dot.add_edge(
            Edge(source="mypackage.foo.blue.alpha", destination="mypackage.foo.green.gamma")
        )

        rendered = dot.render()

        assert "subgraph cluster_mypackage_foo" in rendered
        assert "subgraph cluster_mypackage_foo_blue" in rendered
        assert 'label=".blue"' in rendered
        # .green.gamma is standalone (single sibling under .green)
        assert '".green.gamma"' in rendered
        assert '".blue"' in rendered
        assert '".green"' in rendered
        assert '".blue.alpha"' in rendered
        assert '".blue.beta"' in rendered

    def test_parent_node_in_cluster_with_children(self):
        """Parent node .foo is included in the box with .foo.bar and .foo.baz."""
        dot = DotGraph(title="mypackage", depth=2)
        dot.add_node("mypackage.foo")
        dot.add_node("mypackage.foo.bar")
        dot.add_node("mypackage.foo.baz")
        dot.add_edge(Edge(source="mypackage.foo.bar", destination="mypackage.foo.baz"))

        rendered = dot.render()

        # Cluster contains .foo (parent) and its children .foo.bar, .foo.baz
        assert "subgraph cluster_mypackage_foo" in rendered
        assert '".foo"' in rendered
        assert '".foo.bar"' in rendered
        assert '".foo.baz"' in rendered
        # All three must be inside the same cluster (between subgraph and closing })
        cluster_start = rendered.find("subgraph cluster_mypackage_foo")
        cluster_end = rendered.find("}", cluster_start)
        cluster_content = rendered[cluster_start:cluster_end]
        assert '".foo"' in cluster_content
        assert '".foo.bar"' in cluster_content
        assert '".foo.baz"' in cluster_content


class TestRenderModule:
    def test_render_module_with_base_module(self):
        assert DotGraph.render_module("mypackage.foo.bar", "mypackage.foo") == ".bar"

    def test_render_module_with_nested_base_module(self):
        assert DotGraph.render_module("mypackage.foo.blue.alpha", "mypackage.foo") == ".blue.alpha"

    def test_render_module_without_base_module(self):
        assert DotGraph.render_module("mypackage.foo.bar") == ".bar"

    def test_render_module_fallback_when_no_prefix_match(self):
        assert DotGraph.render_module("other.bar", "mypackage.foo") == ".bar"


class TestEdge:
    def test_render_with_base_module(self):
        edge = Edge(source="mypackage.foo.bar", destination="mypackage.foo.baz")
        rendered = edge.render("mypackage.foo")
        assert rendered == '".bar" ->  ".baz"'

    def test_render_with_depth_2_modules(self):
        edge = Edge(source="mypackage.foo.blue.alpha", destination="mypackage.foo.green")
        rendered = edge.render("mypackage.foo")
        assert rendered == '".blue.alpha" ->  ".green"'
