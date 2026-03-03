#!/usr/bin/env python3
"""Check first line format"""

import json

with open('Data/raw/megavul_simple.json', 'rb') as f:
    # Read first 500 bytes
    first_bytes = f.read(500)
    print("First 500 bytes (raw):")
    print(first_bytes.decode('utf-8', errors='replace'))
    print("\n" + "="*50 + "\n")
    
    # Now read first line
    f.seek(0)
    first_line = f.readline()
    print(f"First line length: {len(first_line)} bytes")
    print(f"First 500 chars of line:\n{first_line[:500].decode('utf-8', errors='replace')}")
    
    # Try to parse it
    try:
        data = json.loads(first_line)
        print(f"\nParsed JSON type: {type(data)}")
        if isinstance(data, (list, dict)):
            if isinstance(data, list):
                print(f"List with {len(data)} items")
                if len(data) > 0:
                    print(f"First item type: {type(data[0])}")
                    if isinstance(data[0], dict):
                        print(f"First item keys: {list(data[0].keys())}")
                        first_item = data[0]
                        for k, v in list(first_item.items())[:3]:
                            if isinstance(v, str):
                                print(f"  {k}: {v[:80]}")
                            else:
                                print(f"  {k}: {str(v)[:80]}")
            else:
                print(f"Dict with keys: {list(data.keys())[:5]}")
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
