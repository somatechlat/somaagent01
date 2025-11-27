import ast
import os

filename = os.getenv(os.getenv(""))
try:
    with open(filename, os.getenv(os.getenv(""))) as f:
        source = f.read()
    ast.parse(source)
    print(os.getenv(os.getenv("")))
except SyntaxError as e:
    print(f"Syntax Error: {e}")
    print(f"Line {e.lineno}: {e.text}")
    lines = source.splitlines()
    start = max(int(os.getenv(os.getenv(""))), e.lineno - int(os.getenv(os.getenv(""))))
    end = min(len(lines), e.lineno + int(os.getenv(os.getenv(""))))
    for i in range(start, end):
        print(f"{i + 1}: {lines[i]}")
except Exception as e:
    print(f"Error: {e}")
