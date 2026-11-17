"""Replay the pinned SmolVLA action policy using recorded observations."""
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageOps
import torch
from lerobot.policies.factory import make_pre_post_processors
from lerobot.policies.smolvla.configuration_smolvla import SmolVLAConfig
from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
import lerobot.policies.smolvla.processor_smolvla  # register the checkpoint's processor steps


def read_statistics(path):
    stats = json.loads(Path(path).read_text(encoding="utf-8"))
    result = {}
    for key in ("observation.state", "action"):
        values = {field: np.asarray(stats[key][field], dtype=np.float64) for field in ("mean", "std")}
        if any(array.shape != (6,) or not np.isfinite(array).all() for array in values.values()):
            raise ValueError(f"{key} calibration requires six finite means and standard deviations.")
        if np.any(values["std"] <= 0):
            raise ValueError(f"{key} calibration requires positive standard deviations.")
        result[key] = {name: array.tolist() for name, array in values.items()}
    return result


def camera_tensor(path):
    with Image.open(path) as image:
        if image.width * image.height > 12_000_000:
            raise ValueError("Use recorded camera frames of at most 12 megapixels.")
        pixels = np.array(ImageOps.exif_transpose(image).convert("RGB"))
    return torch.from_numpy(pixels).permute(2, 0, 1)


def predict(models, request):
    torch.set_num_threads(2)
    device = request["device"]
    if device == "mps" and not torch.backends.mps.is_available():
        raise ValueError("PyTorch MPS is unavailable. Use device=cpu.")
    policy_dir = models / "smolvla"
    backbone = models / "smolvlm-config"
    config = SmolVLAConfig.from_pretrained(policy_dir, local_files_only=True, cli_overrides=[f"--device={device}"])
    config.vlm_model_name = str(backbone)
    # Strict loading takes the VLM tensors from the full policy checkpoint.
    config.load_vlm_weights = False
    pre_overrides = {"tokenizer_processor": {"tokenizer_name": str(backbone)},
                     "device_processor": {"device": device}}
    post_overrides = {}
    if statistics := request.get("statistics_path"):
        stats = read_statistics(statistics)
        pre_overrides["normalizer_processor"] = {"stats": stats}
        post_overrides["unnormalizer_processor"] = {"stats": stats}
    pre, post = make_pre_post_processors(
        config, pretrained_path=str(policy_dir), preprocessor_overrides=pre_overrides,
        postprocessor_overrides=post_overrides,
    )
    policy = SmolVLAPolicy.from_pretrained(policy_dir, config=config, local_files_only=True, strict=True)
    batch = {"observation.state": torch.tensor(request["state"], dtype=torch.float32), "task": request["instruction"]}
    batch.update({f"observation.images.{key}": camera_tensor(path) for key, path in request["camera_images"].items()})
    noise = torch.randn((1, config.chunk_size, config.max_action_dim),
                        generator=torch.Generator().manual_seed(request["seed"])).to(device)
    with torch.inference_mode():
        actions = post(policy.predict_action_chunk(pre(batch), noise=noise))[0].cpu()
    if actions.ndim != 2 or actions.shape[1] != 6 or not torch.isfinite(actions).all():
        raise ValueError("The policy returned an invalid action chunk.")
    return {"backend": "smolvla_base", "device": device, "mode": "recorded_observation_preview",
            "action_space": "dataset_units" if statistics else "normalized",
            "available_steps": len(actions), "actions": actions[:request["steps"]].tolist(),
            "seed": request["seed"]}


if __name__ == "__main__":
    model_root, output_path = map(Path, sys.argv[1:])
    output_path.write_text(json.dumps(predict(model_root, json.load(sys.stdin)), allow_nan=False), encoding="utf-8")
