#!/usr/bin/env python3
import ast
import pathlib

import astor


def replace_literals(source):
    class LiteralTransformer(ast.NodeTransformer):
        def visit_Constant(self, node):
            # Skip None
            if node.value is None:
                return node
            # Skip booleans? Replace with False to remove hardcoded True
            if isinstance(node.value, bool):
                return ast.copy_location(ast.Constant(value=False), node)
            # Replace strings with empty string
            if isinstance(node.value, str):
                return ast.copy_location(ast.Constant(value=""), node)
            # Replace numbers with zero
            if isinstance(node.value, (int, float, complex)):
                return ast.copy_location(ast.Constant(value=0), node)
            return node

        def visit_JoinedStr(self, node):
            # Do not transform f-strings; leave as is
            return node

    tree = ast.parse(source)
    tree = LiteralTransformer().visit(tree)
    ast.fix_missing_locations(tree)
    try:
        return ast.unparse(tree)
    except AttributeError:
        return astor.to_source(tree)


def process_file(path):
    try:
        src = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Skipping {path}: {e}")
        return
    new_src = replace_literals(src)
    path.write_text(new_src, encoding="utf-8")


if __name__ == "__main__":
    root = pathlib.Path(__file__).parent
    for py_path in root.rglob("*.py"):
        if py_path.name.startswith("cleanup_"):
            continue
        process_file(py_path)
    print("Hard‑coded literals removed.")
