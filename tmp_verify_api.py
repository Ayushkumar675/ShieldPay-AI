import urllib.request
import json
import socket
import time

def wait_for_server(host, port, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(1)
    return False

def run_test():
    print("Waiting for server...")
    if not wait_for_server("localhost", 8000):
        print("Server not reachable.")
        return

    print("Testing Disruption...")
    try:
        url = "http://localhost:8000/api/v1/simulation/simulate-disruption"
        data = {"type": "weather", "city": "Delhi", "severity": 0.8}
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode('utf-8'), 
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req) as response:
            print(f"Disruption Status: {response.status}")
            data = json.loads(response.read().decode())
            print(json.dumps(data, indent=2))
            if "stats" in data:
                print("Stats found: PASS")
            else:
                print("Stats found: FAIL")
    except urllib.error.HTTPError as e:
        print(f"Disruption Failed: {e.code}")
        print(e.read().decode())
    except Exception as e:
        print(f"Disruption Failed: {e}")

    print("\nTesting Fraud...")
    try:
        url = "http://localhost:8000/api/v1/simulation/simulate-fraud-cluster?city=Delhi"
        req = urllib.request.Request(url, method='POST')
        with urllib.request.urlopen(req) as response:
            print(f"Fraud Status: {response.status}")
            print(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Fraud Failed: {e.code}")
        print(e.read().decode())
    except Exception as e:
        print(f"Fraud Failed: {e}")

if __name__ == "__main__":
    run_test()