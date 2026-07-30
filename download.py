#!/usr/bin/env python3
"""
Minecraft Server JAR Downloader

Downloads the Minecraft server JAR for a specified version from Mojang's servers
and saves it to a destination directory.
"""

import requests
import sys
from pathlib import Path


MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
CHUNK_SIZE = 8192


def fetch_manifest() -> dict:
    """
    Fetches the Minecraft version manifest from the official Mojang API.

    Returns:
        dict: The parsed JSON manifest containing version information.

    Raises:
        requests.exceptions.RequestException: If the HTTP request fails.
        ValueError: If the response is not valid JSON.
    """
    response = requests.get(MANIFEST_URL, timeout=10)
    response.raise_for_status()
    return response.json()


def find_version_url(manifest: dict, version_id: str) -> str:
    """
    Finds the version JSON URL for a given version ID in the manifest.

    Args:
        manifest (dict): The version manifest dictionary.
        version_id (str): The version ID to search for (e.g., "1.8.9").

    Returns:
        str: The URL to the version's JSON file.

    Raises:
        ValueError: If the version ID is not found in the manifest.
    """
    versions = manifest.get("versions", [])
    for version in versions:
        if version.get("id") == version_id:
            return version.get("url")
    raise ValueError(f"Version '{version_id}' not found in manifest")


def fetch_version_data(version_url: str) -> dict:
    """
    Fetches the version-specific JSON data from Mojang's servers.

    Args:
        version_url (str): The URL to the version JSON file.

    Returns:
        dict: The parsed version JSON data.

    Raises:
        requests.exceptions.RequestException: If the HTTP request fails.
        ValueError: If the response is not valid JSON.
    """
    response = requests.get(version_url, timeout=10)
    response.raise_for_status()
    return response.json()


def get_server_download_url(version_data: dict) -> str:
    """
    Extracts the server JAR download URL from version data.

    Args:
        version_data (dict): The version-specific JSON data.

    Returns:
        str: The download URL for the server JAR.

    Raises:
        ValueError: If the server download URL is not found in version data.
    """
    downloads = version_data.get("downloads", {})
    server = downloads.get("server")
    if not server:
        raise ValueError("Server download URL not found for this version")
    return server.get("url")


def download_server_jar(download_url: str, destination: Path) -> None:
    """
    Downloads the server JAR file and saves it to the destination.

    Args:
        download_url (str): The URL to download the JAR from.
        destination (Path): The destination file path.

    Raises:
        requests.exceptions.RequestException: If the HTTP request fails.
        IOError: If the file cannot be written.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(download_url, timeout=30, stream=True)
    response.raise_for_status()

    with open(destination, "wb") as f:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                f.write(chunk)


def main() -> int:
    """
    Main entry point for the server downloader.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    if len(sys.argv) != 3:
        print("Usage: python3 download.py <version> <destination>", file=sys.stderr)
        print("Example: python3 download.py 1.8.9 ./servers/", file=sys.stderr)
        return 1

    version_id = sys.argv[1]
    destination_dir = sys.argv[2]

    try:
        destination_path = Path(destination_dir) / "server.jar"

        print(f"Fetching manifest...", file=sys.stderr)
        manifest = fetch_manifest()

        print(f"Looking up version '{version_id}'...", file=sys.stderr)
        version_url = find_version_url(manifest, version_id)

        print(f"Fetching version data...", file=sys.stderr)
        version_data = fetch_version_data(version_url)

        print(f"Extracting server download URL...", file=sys.stderr)
        server_url = get_server_download_url(version_data)

        print(f"Downloading server JAR...", file=sys.stderr)
        download_server_jar(server_url, destination_path)

        print(f"Successfully saved to: {destination_path}", file=sys.stderr)
        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}", file=sys.stderr)
        return 1
    except IOError as e:
        print(f"File error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
