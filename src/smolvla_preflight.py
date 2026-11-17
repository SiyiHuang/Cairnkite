"""Inspect local prerequisites for a LeRobot SO-100 or SO-101 rollout."""

from importlib.metadata import version
import json
from pathlib import Path
import sys

import draccus
from draccus.utils import DraccusException
import rustypot  # Load the native motor driver without connecting to a port.
from lerobot.motors import MotorCalibration
from lerobot.scripts.lerobot_rollout import main as rollout_main
from serial.tools.list_ports import comports


JOINTS = ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper")
CHECKPOINT_FILES = ("config.json", "model.safetensors", "policy_preprocessor.json", "policy_postprocessor.json")


def checkpoint(directory):
    if directory is None:
        return {"status": "not_provided"}
    root = Path(directory)
    files = {name: (root / name).resolve() for name in CHECKPOINT_FILES}
    missing = [name for name, file in files.items()
               if not file.is_relative_to(root) or not file.is_file() or not file.stat().st_size]
    if missing:
        return {"status": "incomplete", "missing": missing}
    try:
        with files["config.json"].open("rb") as file:
            raw = file.read(256 * 1024 + 1)
        if len(raw) > 256 * 1024:
            raise ValueError("Oversize policy configuration.")
        config = json.loads(raw)
        cameras = sorted(name for name in config["input_features"] if name.startswith("observation.images."))
        six_axis = config["output_features"]["action"]["shape"] == [6]
        compatible = config["type"] == "smolvla" and six_axis and bool(cameras)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        compatible, cameras, six_axis = False, [], False
    return {"status": "matching_metadata" if compatible else "incompatible_metadata",
            "camera_features": cameras, "six_axis_action": six_axis}


def calibration(path):
    if path is None:
        return "not_provided"
    try:
        with Path(path).open("rb") as file:
            raw = file.read(64 * 1024 + 1)
        if len(raw) > 64 * 1024:
            raise ValueError("Oversize calibration file.")
        motors = draccus.decode(dict[str, MotorCalibration], json.loads(raw))
        compatible = all(motors[name].id == motor_id and motors[name].range_min < motors[name].range_max
                         for motor_id, name in enumerate(JOINTS, start=1))
    except (OSError, ValueError, KeyError, TypeError, DraccusException):
        compatible = False
    return "matching_metadata" if compatible else "incompatible_metadata"


def inspect(request):
    connected = comports()
    port = request["port"]
    return {
        "backend": "lerobot_rollout_preflight",
        "lerobot_version": version("lerobot"),
        "rollout_available": callable(rollout_main),
        "motor_driver_version": version("rustypot"),
        "usb_serial_ports": sorted(device.device for device in connected if device.vid is not None),
        "port_present": any(device.device == port for device in connected) if port else None,
        "checkpoint": checkpoint(request["policy_path"]),
        "calibration_status": calibration(request["calibration_path"]),
        "hardware_verified": False,
    }


if __name__ == "__main__":
    print(json.dumps(inspect(json.load(sys.stdin)), allow_nan=False))
