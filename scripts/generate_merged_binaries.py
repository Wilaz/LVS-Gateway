#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys


def parse_output(line):
  parts = line.split()
  if (
      "esptool" in parts[0]
      or parts[0].endswith("python")
      or parts[0].endswith("python3")
  ):
    try:
      chip_idx = parts.index("--chip")
      parts = parts[chip_idx:]
    except ValueError:
      pass

  parser = argparse.ArgumentParser(allow_abbrev=False)
  parser.add_argument("--chip", type=str, help="Chip name")
  parser.add_argument("--port", type=str, help="Port")
  parser.add_argument("--baud", type=int, help="Baud rate")
  parser.add_argument("--flash_mode", type=str, help="Flash mode", default="dio")
  parser.add_argument("--flash_freq", type=str, help="Flash frequency", default="40m")
  parser.add_argument("--flash_size", type=str, help="Flash size", default="4MB")

  args, unrecognized = parser.parse_known_args(parts)

  binary_files = {}
  i = 0
  while i < len(unrecognized) - 1:
    if unrecognized[i].startswith("0x"):
      offset, bin_path = unrecognized[i], unrecognized[i + 1]
      binary_files[offset] = bin_path
      i += 2
    else:
      i += 1

  if not args.chip:
    return None

  os.makedirs("web/firmware", exist_ok=True)
  github_build_number = os.environ.get("GITHUB_RUN_NUMBER", "0")
  output_filename = f"web/firmware/{args.chip.lower()}-b{github_build_number}.bin"

  python_exec = sys.executable
  new_command = (
      f"{python_exec} -m esptool --chip {args.chip} merge_bin"
      f" -o {output_filename}"
      f" --flash_mode {args.flash_mode}"
      f" --flash_freq {args.flash_freq}"
      f" --flash_size {args.flash_size}"
  )

  for offset, bin_path in binary_files.items():
    new_command += f' {offset} "{bin_path}"'

  return new_command


def generate_merge_firmware_command(pio_env=None):
  command = ["pio", "run"]
  if pio_env:
    command.extend(["-e", pio_env])
  command.extend(["-v", "-t", "upload", "--upload-port", "/dev/null"])

  print(f"Running PlatformIO for environment: {pio_env or 'default'}...")
  try:
    completed_process = subprocess.run(
        command, capture_output=True, text=True, check=True
    )
  except subprocess.CalledProcessError as e:
    print(f"Error running pio for {pio_env}: {e}", file=sys.stderr)
    return

  relevant_lines = [
      line
      for line in completed_process.stdout.splitlines()
      if "write_flash" in line and ("esptool" in line or ".py" in line)
  ]

  for line in relevant_lines:
    merge_cmd = parse_output(line)
    if merge_cmd:
      print(f"Executing: {merge_cmd}")
      subprocess.run(merge_cmd, shell=True, check=True)


if __name__ == "__main__":
  if len(sys.argv) > 1:
    for env in sys.argv[1:]:
      generate_merge_firmware_command(env)
  else:
    generate_merge_firmware_command()