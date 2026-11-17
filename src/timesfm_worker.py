"""Run the pinned TimesFM 3.0 checkpoint through Google's MLX backend."""

import json
from pathlib import Path
import sys

import numpy as np
from timesfm3.mlx import TimesFM3Forecaster


def main() -> None:
    checkpoint, output = map(Path, sys.argv[1:])
    request = json.load(sys.stdin)
    targets = request["targets"]
    past = request["past_covariates"]
    future = request["future_covariates"]
    history = [values for name, values in past.items() if name not in future]
    known = [past[name] + values for name, values in future.items()]

    forecaster = TimesFM3Forecaster.from_pretrained(str(checkpoint), local_files_only=True)
    result = forecaster.predict(
        np.asarray(list(targets.values()), dtype=np.float32),
        horizon=request["horizon"],
        past_only_covariates=np.asarray(history, dtype=np.float32) if history else None,
        past_future_covariates=np.asarray(known, dtype=np.float32) if known else None,
        return_quantiles=True,
    )
    quantiles = result.quantiles[..., [0, 4, 8]]
    forecast = dict(zip(targets, quantiles.tolist(), strict=True))
    output.write_text(json.dumps({
        "backend": "timesfm_3_mlx",
        "quantile_levels": [0.1, 0.5, 0.9],
        "forecast": forecast,
        "baseline_last_observation": {name: values[-1] for name, values in targets.items()},
    }, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
