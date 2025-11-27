import os
import ast
filename = os.getenv(os.getenv('VIBE_5FF9C561'))
try:
    with open(filename, os.getenv(os.getenv('VIBE_812A5237'))) as f:
        source = f.read()
    ast.parse(source)
    print(os.getenv(os.getenv('VIBE_F33EB100')))
except SyntaxError as e:
    print(f'Syntax Error: {e}')
    print(f'Line {e.lineno}: {e.text}')
    lines = source.splitlines()
    start = max(int(os.getenv(os.getenv('VIBE_0FF90B79'))), e.lineno - int(
        os.getenv(os.getenv('VIBE_4F6F03CE'))))
    end = min(len(lines), e.lineno + int(os.getenv(os.getenv('VIBE_4F6F03CE')))
        )
    for i in range(start, end):
        print(f'{i + 1}: {lines[i]}')
except Exception as e:
    print(f'Error: {e}')
