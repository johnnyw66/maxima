# Maxima Docker Container

Running Maxima inside a Docker container is a convenient alternative to installing it directly via Homebrew or MacPorts on macOS. This approach ensures Maxima runs in a controlled environment without conflicting with system dependencies. A prebuilt Maxima image can be found on Docker Hub, or you can create a custom image using the provided `Dockerfile`, which installs Maxima from a package manager like APT (for Debian-based images) or compiles it from source. Running Maxima in a container allows for easy version management, sandboxed execution, and cross-platform compatibility without modifying the host system.

## *** UPDATE *** Now you can run Maxima on your Raspberry Pi
After cloning the directory using the instructions below  - simply copy **Dockerfile.RPI** over the existing **Dockerfile**.
With the new Dockerfile in place - you then run the one off **docker build** command.

## Running Maxima in a Docker Container with 2D Plotting Support

Instead of building Maxima via Homebrew or MacPorts, you can use Docker for a streamlined installation.

### Setup

Ensure you have Docker installed on your system, then clone this repository:

```sh
git clone git@github.com:johnnyw66/maxima.git  
```

Alternatively, you can download the repository as a ZIP file using the **Download Zip** option. Extract the files and navigate into the created `maxima` directory:

```sh
cd maxima
```

### Building the Docker Image

Run the following command to build the Maxima container:

```sh
docker build -t maxima-web .
```

> **Note:** The period (`.`) at the end of this command is required.

This one-time setup may take a while as it downloads dependencies and builds the container.

### Running Maxima

Once the container is built, you can run Maxima in the command-line interface (CLI) using:

```sh
docker run -v $(pwd):/app -it maxima-web maxima
```

### Running Maxima with 2D Plotting

To enable 2D graph plotting, use the following command:

```sh
docker run -p 5050:5000 -v $(pwd):/app -it maxima-web
```

Plots will be timestamped and saved in the **static/plots** directory, which is created automatically when you run the plotting version.

### Accessing the Plotting Web Interface

Once the container is running with 2D plotting enabled, you can access the web interface by opening a browser and navigating to:

```
http://localhost:5050
```

This interface allows you to generate and view plots dynamically. Ensure that port 5050 is not blocked by your firewall or in use by another application.

![Maxima Web Service](/images/web01.png)

![Maxima Web Service](/images/web02.png)

### Simple CLI (cli.py)

Once you have a local **maxima** webservice running you can run maxima commands by running the Python script **cli.py**

```sh
python3 cli.py
```

The script assumes you are running a local **maxima-web** Docker container (change the **url** variable in the script to match your host).

![Maxima CLI Screenshot example](/images/cli.png)

```sh
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

```



