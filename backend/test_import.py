import sys
import os
sys.path.append(os.getcwd())
try:
    from app.api import claims
    print("Import successful")
    print(dir(claims))
    print(f"Router found: {hasattr(claims, 'router')}")
except Exception as e:
    print(f"Import failed: {e}")
