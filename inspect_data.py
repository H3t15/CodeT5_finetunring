#!/usr/bin/env python3
"""Inspect MegaVul dataset structure"""

import json
import sys

def inspect_dataset():
    try:
        with open('Data/raw/megavul_simple.json', 'r') as f:
            print("Reading first 3 records...")
            for i in range(3):
                line = f.readline()
                if not line:
                    break
                try:
                    record = json.loads(line.strip())
                    print(f"\n=== Record {i} ===")
                    print(f"Type: {type(record)}")
                    
                    if isinstance(record, dict):
                        print(f"Keys: {list(record.keys())}")
                        for key, value in record.items():
                            if isinstance(value, str):
                                print(f"{key}: {value[:150]}...")
                            else:
                                print(f"{key}: {value}")
                    elif isinstance(record, list):
                        print(f"List length: {len(record)}")
                        if len(record) > 0 and isinstance(record[0], dict):
                            print(f"First item keys: {list(record[0].keys())}")
                            for j, item in enumerate(record[:2]):
                                print(f"\n  Item {j} keys: {list(item.keys())}")
                                for key, value in item.items():
                                    if isinstance(value, str):
                                        print(f"    {key}: {value[:100]}...")
                                    else:
                                        print(f"    {key}: {str(value)[:100]}")
                except Exception as e:
                    import traceback
                    print(f"Error parsing line {i}: {e}")
                    traceback.print_exc()
                    
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    inspect_dataset()
