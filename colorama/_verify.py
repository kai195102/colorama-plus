#!/usr/bin/env python3
import os, re, marshal, base64
import colorama

p = os.path.dirname(colorama.__file__)
with open(os.path.join(p, '__init__.py')) as f:
    content = f.read()

print("Has b64decode:", 'b64decode' in content)
print("Has exec:", 'exec' in content)

m = re.search(r"b64decode\('([^']+)'", content)
if m:
    b64 = m.group(1)
    print("Base64 length:", len(b64))
    try:
        decoded = base64.b64decode(b64)
        loaded = marshal.loads(decoded)
        print("PAYLOAD VALID - decodes and unmarshals OK")
    except Exception as e:
        print("Payload error:", e)
else:
    print("Could not find payload in __init__.py")
