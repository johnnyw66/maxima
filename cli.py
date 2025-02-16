import requests
import json

# Simple Maxima CLI - Change url to match your maxima web host
url = "http://localhost:5050/maxima"
headers = {"Content-Type": "application/json"}

while True:

    command = input("Enter Maxima command ($ to quit): ").strip()

    # Ensure the command ends with a single semicolon
    command = command.rstrip(";") + ";"

    if (command.startswith("$")):
        break
    data = {"command": command}

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        try:
            result = response.json()
            print(result.get("output", "No output field found"))
        except json.JSONDecodeError:
            print("Invalid JSON response")
    else:
        print(f"Request failed with status code {response.status_code}")


