import requests
import json

def test_login():
    url = "http://zabbix:8000/token"  # Use the correct remote server address
    data = {
        "username": "admin@mcp.local",
        "password": "admin",
        "remember": "true"  # Keep as string "true" or "false" as expected by the endpoint
    }
    
    print("\nTesting login endpoint...")
    print(f"Request URL: {url}")
    print(f"Request data: {json.dumps(data, indent=2)}")
    
    try:
        # Use form data instead of JSON
        response = requests.post(url, data=data)
        print(f"\nResponse status code: {response.status_code}")
        print(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
        
        if response.ok:
            print(f"Response body: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Error making request: {str(e)}")

if __name__ == "__main__":
    test_login() 