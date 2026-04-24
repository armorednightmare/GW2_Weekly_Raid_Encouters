import requests
import json

res = requests.get('https://killproof.me/api/clear/257ex')
data = res.json()
for key, value in data.items():
    print(f"Category: {key}")
    if isinstance(value, list):
        for item in value:
            for boss, status in item.items():
                print(f"  - {boss}: {status}")
    else:
        print(f"  - {value}")
