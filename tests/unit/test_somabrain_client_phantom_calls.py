"""TG-01 — SomaBrainClient phantom-call gate (pure AST, no Django, no Vault).

Every attribute access on a binding that holds a ``SomaBrainClient`` must name
a member that actually exists on the class in
``admin/core/somabrain_client.py``. W1.5 killed phantom call sites
(``migrate_export``, ``remember``/``recall``/``forget``, ``wake``...) one by
one; this gate turns the *next* phantom into a test failure instead of a
runtime AttributeError swallowed by a broad ``except``.

How receivers are recognised (two passes over production sources):

1. Collect producers: functions whose return annotation mentions
   ``SomaBrainClient`` (e.g. ``get_somabrain_client``,
   ``_get_agent_soma_client``), class-method constructors
   (``SomaBrainClient.get``/``get_async``/``SomaBrainClient(...)``), and
   ``self.<attr> = <producer>`` holders (today: ``ToolExecutor.soma``).
2. Walk each file with a scope chain: a name is a client receiver when it is
   assigned from a producer, annotated as ``SomaBrainClient``, or — because
   the codebase uses these names exclusively for this type — literally named
   ``brain_client`` / ``soma_client``. Attribute chains containing a known
   holder (``worker.soma.close()``, ``_executor.soma.context_feedback``) are
   receivers too.

Pure source analysis: parses Python with ``ast``, never imports Django,
never reads settings, never talks to Vault.

Run (no Vault needed — bypasses the pytest.ini Django/Vault bootstrap):

    python3 -m pytest -c /dev/null --noconftest -p no:cacheprovider \\
        tests/unit/test_somabrain_client_phantom_calls.py -v

Run with the full stack up (Vault reachable), like the rest of the suite:

    pytest tests/unit/test_somabrain_client_phantom_calls.py -v
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# Production trees where a SomaBrainClient call site can appear.
SCAN_DIRS = ("admin", "services", "config", "scripts")
SKIP_PARTS = {"__pycache__", "migrations", "node_modules", ".venv", "secrets"}

# Receiver names that mean SomaBrainClient everywhere they appear in this
# codebase (callers pass them as `brain_client` / `soma_client` even when the
# callee parameter is typed `Any`). A name used for two different types would
# make this convention ambiguous — that rename is exactly what this gate
# should force through review.
CLIENT_NAME_CONVENTIONS = frozenset({"brain_client", "soma_client"})


def _source_files() -> list[Path]:
    files: list[Path] = []
    for rel in SCAN_DIRS:
        base = REPO / rel
        if not base.exists():
            continue
        files.extend(
            p for p in sorted(base.rglob("*.py")) if not SKIP_PARTS.intersection(p.parts)
        )
    return files


def _parse_all() -> dict[Path, ast.Module]:
    trees: dict[Path, ast.Module] = {}
    for path in _source_files():
        trees[path] = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return trees


def _client_class_methods() -> set[str]:
    """Method/property names defined on SomaBrainClient itself."""
    path = REPO / "admin" / "core" / "somabrain_client.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "SomaBrainClient":
            methods = {
                child.name
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            assert methods, "SomaBrainClient has no methods — analysis target moved"
            return methods
    raise AssertionError("class SomaBrainClient not found in admin/core/somabrain_client.py")


def _annotation_is_client(node: ast.expr | None) -> bool:
    if node is None:
        return False
    return "SomaBrainClient" in ast.unparse(node)


def _unwrap(node: ast.expr) -> ast.expr:
    while isinstance(node, ast.Await):
        node = node.value
    return node


def _chain_attrs(node: ast.Attribute) -> tuple[ast.expr, list[str]]:
    """Flatten ``a.b.c`` into (root_expr, ['c', 'b']) — outermost attr first."""
    attrs: list[str] = [node.attr]
    cur: ast.expr = node.value
    while isinstance(cur, ast.Attribute):
        attrs.append(cur.attr)
        cur = cur.value
    return cur, attrs


class _FileAnalysis:
    """One pass-2 walk of a single file."""

    def __init__(
        self,
        path: Path,
        tree: ast.Module,
        methods: set[str],
        producers: set[str],
        client_attrs: set[str],
        class_aliases: set[str],
    ) -> None:
        self.rel = path.relative_to(REPO).as_posix()
        self.tree = tree
        self.methods = methods
        self.producers = producers
        self.client_attrs = client_attrs
        self.class_aliases = class_aliases
        self.scopes: list[set[str]] = [set()]
        self.findings: list[str] = []
        self.checked: set[tuple[str, str]] = set()

    # -- bindings ----------------------------------------------------------

    def _resolve(self, name: str) -> bool:
        return any(name in scope for scope in self.scopes) or name in CLIENT_NAME_CONVENTIONS

    def _is_client_value(self, node: ast.expr) -> bool:
        node = _unwrap(node)
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                return func.id in self.producers
            if isinstance(func, ast.Attribute):
                root, _ = _chain_attrs(func)
                if isinstance(root, ast.Name) and root.id in self.class_aliases:
                    return True
        if isinstance(node, ast.Name):
            return self._resolve(node.id)
        if isinstance(node, ast.Attribute):
            _, attrs = _chain_attrs(node)
            # `soma = self.worker.soma` — the value itself lives in a
            # known client-holding attribute (the outermost attr).
            return attrs[0] in self.client_attrs
        return False

    # -- walk --------------------------------------------------------------

    def run(self) -> None:
        for stmt in self.tree.body:
            self.visit(stmt)

    def visit(self, node: ast.AST | None) -> None:
        if node is None:
            return
        method = getattr(self, f"visit_{type(node).__name__}", None)
        if method is not None:
            method(node)
            return
        self.generic_visit(node)

    def generic_visit(self, node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            self.visit(child)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._function(node)

    def _function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        for deco in node.decorator_list:
            self.visit(deco)
        for default in list(node.args.defaults) + [
            d for d in (node.args.kw_defaults or []) if d is not None
        ]:
            self.visit(default)
        # New scope: client-annotated params (and the two convention names)
        # bind inside the function body.
        self.scopes.append(set())
        for arg in list(node.args.args) + list(node.args.kwonlyargs):
            if _annotation_is_client(arg.annotation) or arg.arg in CLIENT_NAME_CONVENTIONS:
                self.scopes[-1].add(arg.arg)
        if node.args.vararg and (
            _annotation_is_client(node.args.vararg.annotation)
            or node.args.vararg.arg in CLIENT_NAME_CONVENTIONS
        ):
            self.scopes[-1].add(node.args.vararg.arg)
        if node.args.kwarg and (
            _annotation_is_client(node.args.kwarg.annotation)
            or node.args.kwarg.arg in CLIENT_NAME_CONVENTIONS
        ):
            self.scopes[-1].add(node.args.kwarg.arg)
        for stmt in node.body:
            self.visit(stmt)
        self.scopes.pop()

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self.scopes.append(set())
        self.visit(node.body)
        self.scopes.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for base in node.bases:
            self.visit(base)
        for stmt in node.body:
            self.visit(stmt)

    def _assign(self, targets: list[ast.expr], value: ast.expr | None) -> None:
        if value is not None:
            self.visit(value)
        is_client = value is not None and self._is_client_value(value)
        for target in targets:
            if isinstance(target, ast.Name):
                if is_client:
                    self.scopes[-1].add(target.id)
            elif isinstance(target, (ast.Tuple, ast.List)):
                if is_client:
                    for elt in target.elts:
                        if isinstance(elt, ast.Name):
                            self.scopes[-1].add(elt.id)
            elif isinstance(target, ast.Starred):
                self._assign([target.value], value)
            else:
                # Attribute / Subscript targets: no name binding.
                self.visit(target)

    def visit_Assign(self, node: ast.Assign) -> None:
        self._assign(node.targets, node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Name) and (
            _annotation_is_client(node.annotation)
            or node.target.id in CLIENT_NAME_CONVENTIONS
        ):
            self.scopes[-1].add(node.target.id)
        self._assign([node.target], node.value)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self.visit(node.value)
        self.visit(node.target)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        self._assign([node.target], node.value)

    def visit_For(self, node: ast.For) -> None:
        self.visit(node.iter)
        if isinstance(node.target, ast.Name) and self._is_client_value(node.iter):
            self.scopes[-1].add(node.target.id)
        else:
            self.visit(node.target)
        for stmt in node.body + node.orelse:
            self.visit(stmt)

    visit_AsyncFor = visit_For

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            self.visit(item.context_expr)
            if item.optional_vars is not None:
                self.visit(item.optional_vars)
        for stmt in node.body:
            self.visit(stmt)

    visit_AsyncWith = visit_With

    def visit_Import(self, node: ast.Import) -> None:
        pass  # module aliases are not client receivers

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        pass  # producer/class aliases handled in pass 1

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.generic_visit(node)
            return
        root, attrs = _chain_attrs(node)  # attrs: outermost first

        receiver = False
        check_attr: str | None = None
        if isinstance(root, ast.Name):
            if root.id in self.class_aliases:
                receiver = True
                check_attr = attrs[0]
            elif self._resolve(root.id):
                receiver = True
                # Member accessed on the client is the innermost attr.
                check_attr = attrs[-1]
        if not receiver:
            # Chain containing a known holder attr: `worker.soma.close()`,
            # `self._executor.soma.context_feedback(...)`.
            if any(a in self.client_attrs for a in attrs[1:]):
                receiver = True
                check_attr = attrs[0]
        if receiver and check_attr is not None and not check_attr.startswith("_"):
            self.checked.add((self.rel, check_attr))
            if check_attr not in self.methods:
                self.findings.append(
                    f"{self.rel}: `...{check_attr}` — SomaBrainClient has no member "
                    f"`{check_attr}`"
                )
        # Walk sub-expressions (call args, receiver sub-chains).
        self.generic_visit(node)


def _pass1(trees: dict[Path, ast.Module]) -> tuple[set[str], set[str], set[str]]:
    producers: set[str] = set()
    client_attrs: set[str] = set()
    class_aliases: set[str] = {"SomaBrainClient"}

    for tree in trees.values():
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if _annotation_is_client(node.returns):
                    producers.add(node.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module and "somabrain_client" in node.module:
                    for alias in node.names:
                        if alias.name == "SomaBrainClient":
                            class_aliases.add(alias.asname or alias.name)

    for tree in trees.values():
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if not (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    continue
                value = _unwrap(node.value)
                if not isinstance(value, ast.Call):
                    continue
                func = value.func
                if isinstance(func, ast.Name) and func.id in producers:
                    client_attrs.add(target.attr)
                elif (
                    isinstance(func, ast.Attribute)
                    and isinstance(func.value, ast.Name)
                    and func.value.id in class_aliases
                ):
                    client_attrs.add(target.attr)
    return producers, client_attrs, class_aliases


def _analyse() -> tuple[set[str], set[str], set[str], list[str], set[tuple[str, str]]]:
    methods = _client_class_methods()
    trees = _parse_all()
    producers, client_attrs, class_aliases = _pass1(trees)
    findings: list[str] = []
    checked: set[tuple[str, str]] = set()
    for path, tree in trees.items():
        analysis = _FileAnalysis(path, tree, methods, producers, client_attrs, class_aliases)
        analysis.run()
        findings.extend(analysis.findings)
        checked |= analysis.checked
    return methods, producers, client_attrs, findings, checked


class TestPhantomCallGate:
    """Fail if any client.X() names a member SomaBrainClient does not have."""

    def test_no_phantom_members(self):
        methods, _, _, findings, _ = _analyse()
        assert not findings, (
            "phantom SomaBrainClient call site(s) — the member does not exist on "
            f"the class (defined members: {sorted(methods)}):\n  "
            + "\n  ".join(findings)
        )

    def test_analysis_is_not_blind(self):
        """The gate must actually see the known real call sites.

        If a refactor renames the source trees, moves the client class, or
        breaks the binding analysis, this test fails instead of the gate
        silently passing on zero receivers.
        """
        methods, producers, client_attrs, _, checked = _analyse()
        assert "context_evaluate" in methods
        assert "get_somabrain_client" in producers
        assert "_get_agent_soma_client" in producers
        assert "soma" in client_attrs, "ToolExecutor.soma holder not detected"
        expected = {
            ("admin/core/chat_orchestrator.py", "context_evaluate"),
            ("admin/core/chat_orchestrator.py", "thread_next"),
            ("admin/agents/services/somabrain_integration.py", "act"),
            ("admin/somabrain/core_brain.py", "act"),
            ("admin/core/somabrain_connector.py", "ping"),
            ("services/gateway/consumers/chat.py", "update_neuromodulators"),
            ("services/tool_executor/result_publisher.py", "context_feedback"),
            ("services/conversation_worker/service.py", "close"),
        }
        missing = expected - checked
        assert not missing, f"analysis went blind — receivers not seen: {sorted(missing)}"

    def test_gate_catches_a_planted_phantom(self):
        """Meta: feed the analysis a synthetic phantom and demand it fails.

        Proves the gate is capable of failing — a green gate nobody has ever
        seen fail is not evidence of anything.
        """
        phantom = ast.parse(
            "def get_somabrain_client():\n"
            "    ...\n"
            "async def f():\n"
            "    client = get_somabrain_client()\n"
            "    return await client.migrate_export()\n"
        )
        analysis = _FileAnalysis(
            REPO / "__synthetic_phantom__.py",
            phantom,
            _client_class_methods(),
            {"get_somabrain_client"},
            set(),
            {"SomaBrainClient"},
        )
        analysis.run()
        assert analysis.findings, "gate failed to flag a planted phantom call"
        assert any("migrate_export" in f for f in analysis.findings)
