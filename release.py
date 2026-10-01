#!/usr/bin/env python3

import json
import os
import subprocess
import sys

# Map your PlatformIO environments to ESP Web Tools chip families
CHIP_MAP = {
    "esp32dev": "ESP32",
    "esp32s2": "ESP32-S2",
    "esp32s3": "ESP32-S3",
    "esp32c3": "ESP32-C3",
    "esp32c6": "ESP32-C6",
}


def build_and_merge(pio_env, chip_family, builds):
    print(f"\n--- Building PlatformIO Environment: {pio_env} ---")
    result = subprocess.run(
        [
            "pio",
            "run",
            "-e",
            pio_env,
            "-v",
            "-t",
            "upload",
            "--upload-port",
            "/dev/null",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Error building {pio_env}", file=sys.stderr)
        return

    # Locate the esptool write_flash command in the verbose output
    for line in result.stdout.splitlines():
        if "write_flash" in line and ("esptool" in line or ".py" in line):
            parts = line.split()
            if "--chip" in parts:
                parts = parts[parts.index("--chip") :]

            chip = (
                parts[parts.index("--chip") + 1] if "--chip" in parts else chip_family
            )
            flash_mode = (
                parts[parts.index("--flash_mode") + 1]
                if "--flash_mode" in parts
                else "dio"
            )
            flash_freq = (
                parts[parts.index("--flash_freq") + 1]
                if "--flash_freq" in parts
                else "40m"
            )
            flash_size = (
                parts[parts.index("--flash_size") + 1]
                if "--flash_size" in parts
                else "4MB"
            )

            # Extract offset and binary file paths
            binary_files = {}
            i = 0
            while i < len(parts) - 1:
                if parts[i].startswith("0x"):
                    binary_files[parts[i]] = parts[i + 1]
                    i += 2
                else:
                    i += 1

            os.makedirs("web/firmware", exist_ok=True)
            build_num = os.environ.get("GITHUB_RUN_NUMBER", "0")
            bin_filename = f"{chip.lower()}-b{build_num}.bin"
            output_path = os.path.join("web/firmware", bin_filename)

            # Run esptool merge_bin
            merge_cmd = [
                sys.executable,
                "-m",
                "esptool",
                "--chip",
                chip,
                "merge_bin",
                "-o",
                output_path,
                "--flash_mode",
                flash_mode,
                "--flash_freq",
                flash_freq,
                "--flash_size",
                flash_size,
            ]
            for offset, path in binary_files.items():
                merge_cmd.extend([offset, path])

            print(f"Merging into {bin_filename}...")
            subprocess.run(merge_cmd, check=True)

            # Register build for manifest.json
            builds.append(
                {
                    "chipFamily": chip_family,
                    "parts": [{"path": bin_filename, "offset": 0}],
                }
            )
            break


def main():
    envs = sys.argv[1:] if len(sys.argv) > 1 else list(CHIP_MAP.keys())
    builds = []

    for env in envs:
        chip_family = CHIP_MAP.get(env, "ESP32")
        build_and_merge(env, chip_family, builds)

    github_repo = os.environ.get("GITHUB_REPOSITORY", "user/repo")
    build_num = os.environ.get("GITHUB_RUN_NUMBER", "0")

    manifest = {
        "name": github_repo,
        "version": f"0.0.{build_num}",
        "funding_url": f"https://github.com/{github_repo}/contributors",
        "builds": builds,
    }

    manifest_path = "web/firmware/manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest successfully created at {manifest_path}")


if __name__ == "__main__":
    main()
