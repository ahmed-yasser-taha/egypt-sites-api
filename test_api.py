import requests

BASE_URL = "http://localhost:8000"

# Test get all sites
response = requests.get(f"{BASE_URL}/sites?limit=5")
print("GET /sites:")
print(response.json())
print()

# Test get specific site
response = requests.get(f"{BASE_URL}/site/1")
print("GET /site/1:")
print(response.json())
