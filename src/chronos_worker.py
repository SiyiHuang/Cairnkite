"""Run the pinned Chronos-2 checkpoint without network access."""

import json
from pathlib import Path
import sys

import numpy as np
from chronos import Chronos2Pipeline


def main() -> None:
    checkpoint, output = map(Path, sys.argv[1:])
    request = json.load(sys.stdin)
    pipeline = Chronos2Pipeline.from_pretrained(str(checkpoint), device_map="cpu", local_files_only=True)
    targets = request["targets"]
    task = {"target": np.asarray(list(targets.values()), dtype=np.float64)}
    for key in ("past_covariates", "future_covariates"):
        if request[key]:
            task[key] = {name: np.asarray(values, dtype=np.float64) for name, values in request[key].items()}
    levels = [0.1, 0.5, 0.9]
    quantiles, _ = pipeline.predict_quantiles([task], prediction_length=request["horizon"], quantile_levels=levels)
    forecast = dict(zip(targets, quantiles[0].tolist(), strict=True))
    result = {"backend": "chronos_2_cpu", "quantile_levels": levels, "forecast": forecast,
              "baseline_last_observation": {name: values[-1] for name, values in targets.items()}}
    output.write_text(json.dumps(result, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
