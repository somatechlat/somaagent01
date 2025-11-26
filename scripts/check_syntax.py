import ast

filename = "services/common/redis_client.py"
try:
    with open(filename, "r") as f:
        source = f.read()
    ast.parse(source)
    print("Syntax OK")
except SyntaxError as e:
    print(f"Syntax Error: {e}")
    print(f"Line {e.lineno}: {e.text}")
    # Print surrounding lines
    lines = source.splitlines()
    start = max(0, e.lineno - 5)
    end = min(len(lines), e.lineno + 5)
    for i in range(start, end):
        print(f"{i+1}: {lines[i]}")
except Exception as e:
    print(f"Error: {e}")
