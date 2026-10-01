#!/usr/bin/env python3

import glob
import json
import os

# Map chip families to their expected search patterns or names
CHIP_MAPPINGS = {
    "ESP32": "esp32",
    "ESP32-S2": "esp32s2",
    "ESP32-S3": "esp32s3",
    "ESP32-C3": "esp32c3",
    "ESP32-C6": "esp32c6",
}


def generate_manifest():
  github_repo = os.environ.get("GITHUB_REPOSITORY", "user/repo")
  github_build_number = os.environ.get("GITHUB_RUN_NUMBER", "0")

  firmware_dir = "web/firmware"
  builds = []

  for chip_family, keyword in CHIP_MAPPINGS.items():
    # Find generated merged binary matching the chip keyword
    matches = glob.glob(os.path.join(firmware_dir, f"{keyword}-*.bin"))
    if matches:
      # Use just the filename since manifest.json sits in the same folder
      filename = os.path.basename(matches[0])
      builds.append({
          "chipFamily": chip_family,
          "parts": [{"path": filename, "offset": 0}],
      })

  manifest = {
      "name": github_repo,
      "version": f"0.0.{github_build_number}",
      "builds": builds,
  }

  output_path = os.path.join(firmware_dir, "manifest.json")
  with open(output_path, "w") as f:
    json.dump(manifest, f, indent=2)

  print(f"Manifest successfully written to {output_path}")


if __name__ == "__main__":
  generate_manifest()