# Data Generator
This repository automatically runs the [Data Generator](https://minecraft.wiki/w/Tutorial:Running_the_data_generator) for every available server version and publishes the resulting dumps to dedicated branches.

A GitHub Actions workflow executes the generator on a schedule (via `cron`), using the official Mojang server JAR for each version.  
The generated data is then committed to a corresponding branch named after the version.


## How It Works

1. A GitHub Actions workflow runs on a schedule (`cron`) or manually.
2. For each known version:
   - The workflow downloads the official Mojang server JAR.
   - It runs the Data Generator included in that version of the Minecraft server.
   - It commits the generated dump to the branch for that version.
3. Branches are updated only when a change in the generated data is detected.

---

## 📝 Notes on Licensing

The generated data originates from the official Mojang server JAR.  
While the generator output is not explicitly licensed by Mojang, it is derivative of Minecraft’s game data.  

Because of that, **it is unclear whether a custom open-source license should be applied**.  
For now, the repository **does not apply an additional license** to avoid implying permissions that may not exist.

If you intend to use the data, please ensure you comply with Mojang’s guidelines and EULA.


### Manifest

The `manifest.py` script fetches the official Minecraft version manifest from Mojang's API and outputs version information in Java properties format. It provides three key pieces of data:

- **release**: The latest stable Minecraft release version (e.g., `26.2`)
- **snapshot**: The latest Minecraft snapshot version (e.g., `26.3-snapshot-6`)
- **versions**: A comma-separated list of all available Minecraft versions, ordered from oldest to newest (e.g., `rd-132211,...,1.7.10,...,26.3-snapshot-6`)

**Usage:**
```bash
python manifest.py
```

**Output example:**
```
release=26.2
snapshot=26.3-snapshot-6
versions=rd-132211,c0.0.11a,c0.0.11a_01,c0.0.12,c0.0.12_02,...,1.7.10,...,26.3-snapshot-6
```

The script makes an HTTP request to `https://launchermeta.mojang.com/mc/game/version_manifest.json`, parses the JSON response, and extracts the relevant version information. It handles errors gracefully and exits with appropriate status codes.

### Download

The `download.py` script downloads the official Minecraft server JAR file for a specified version from Mojang's servers and saves it as `server.jar` in a destination directory.

**Usage:**
```bash
python3 download.py <version> <destination>
```

**Example:**
```bash
python3 download.py 1.8.9 ./servers/
# Output: Successfully saved to: servers/server.jar
```

The script:
1. Fetches the version manifest to find the specified version
2. Loads the version-specific metadata from Mojang
3. Extracts the server JAR download URL
4. Downloads the JAR file in chunks
5. Saves it as `server.jar` in the destination directory (creating it if necessary)

**Arguments:**
- `<version>`: The Minecraft version ID (e.g., `1.8.9`, `1.20.1`, `26.2`)
- `<destination>`: The directory where `server.jar` will be saved

**Exit codes:**
- `0`: Success
- `1`: Failure (invalid version, network error, etc.)

### Generate

The `run_generator.sh` script executes the Minecraft data generator to extract game data from a server JAR file. This is useful for analyzing blocks, items, recipes, and other Minecraft game data.

**Usage:**
```bash
./run_generator.sh <path-to-server.jar>
```

**Example:**
```bash
./run_generator.sh ./server.jar
# Generates data and outputs to the current directory
```

The script:
1. Validates that a server JAR file is provided and exists
2. Attempts to run the data generator using the classpath method (`net.minecraft.data.Main --all`)
3. Falls back to the bundled launcher method if the first attempt fails
4. Generates data files from the server JAR (blocks, items, recipes, etc.)

**Arguments:**
- `<path-to-server.jar>`: Path to the Minecraft server JAR file (e.g., `./server.jar`, `./servers/1.20.1/server.jar`)

**Exit codes:**
- `0`: Success — data generator ran successfully
- `1`: Failure — JAR file not found or data generation failed

**Typical Workflow:**
```bash
# 1. Get available versions
python3 manifest.py | grep "^release=" | cut -d= -f2

# 2. Download a server JAR
python3 download.py 1.20.1 ./build/

# 3. Generate data from the JAR
./run_generator.sh ./build/server.jar
```

**Notes:**
- Requires Java to be installed and available in PATH
- The script uses `set -o errexit` for safety (exits on first error)
- Data output is written to the current working directory
- Different Minecraft versions may have different data generator classes, so the script tries two methods