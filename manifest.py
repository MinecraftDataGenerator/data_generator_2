#!/usr/bin/env python3
"""
Minecraft Version Manifest Loader

Fetches the official Minecraft version manifest from Mojang and outputs
version information in Java property format.
"""

import requests
import sys


def fetch_manifest() -> dict:
    """
    Fetches the Minecraft version manifest from the official Mojang API.

    Returns:
        dict: The parsed JSON manifest containing version information.

    Raises:
        requests.exceptions.RequestException: If the HTTP request fails.
        ValueError: If the response is not valid JSON.
    """
    url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def extract_latest_versions(manifest: dict) -> tuple[str, str]:
    """
    Extracts the latest release and snapshot versions from the manifest.

    Args:
        manifest (dict): The version manifest dictionary.

    Returns:
        tuple: A tuple of (latest_release, latest_snapshot).
    """
    latest = manifest.get("latest", {})
    release = latest.get("release", "unknown")
    snapshot = latest.get("snapshot", "unknown")
    return release, snapshot


def extract_all_versions(manifest: dict) -> list[str]:
    """
    Extracts all version IDs from the manifest in order (oldest to newest).

    Args:
        manifest (dict): The version manifest dictionary.

    Returns:
        list: A list of version IDs sorted from oldest to newest.
    """
    versions = manifest.get("versions", [])
    return [v["id"] for v in versions]


def print_properties(release: str, snapshot: str, versions: list[str]) -> None:
    """
    Prints version information in Java properties format.

    Args:
        release (str): The latest release version.
        snapshot (str): The latest snapshot version.
        versions (list): All version IDs from oldest to newest.
    """
    print(f"release={release}")
    print(f"snapshot={snapshot}")
    print(f"versions={','.join(versions[::-1])}")


def main() -> int:
    """
    Main entry point for the manifest loader.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    try:
        manifest = fetch_manifest()
        release, snapshot = extract_latest_versions(manifest)
        versions = extract_all_versions(manifest)
        print_properties(release, snapshot, versions)
        return 0
    except requests.exceptions.RequestException as e:
        print(f"Error fetching manifest: {e}", file=sys.stderr)
        return 1
    except (ValueError, KeyError) as e:
        print(f"Error parsing manifest: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
