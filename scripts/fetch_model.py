"""Download and verify pinned model snapshots during installation only."""
import fcntl
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from huggingface_hub import hf_hub_download, snapshot_download

MODELS = {
    "layout": (
        "PaddlePaddle/PP-DocLayoutV3", "241f8bdfc77a7c7bee915a5057aaee58c235a8d3",
        "70bd316b0582769ec968829fd1feb1a6a58b7c941b938327e551b6b12b45c137",
    ),
    "paddle": (
        "PaddlePaddle/PaddleOCR-VL-1.6", "132c45f52c0a26ed5a6b2f6bd8e3985794cc27dd",
        "85a479d506a11e724e7285d395c551be69f41dbc16b6342d3cacfb189aed71db",
    ),
    "moss": (
        "vanch007/mlx-MOSS-Transcribe-Diarize-8bit", "7210aef739be6b9e068fba9b1d60369ec053655b",
        "a7ed3c83a357347472ea35f7266c916c15a59b6700c5f4e861db532743fe7c86",
    ),
    "minicpm": (
        "nativ-community/MiniCPM-OCR-1.0-8bit", "4196fbbad59fd7a87647abf8cd36be25ad9c5c8f",
        "6d24a2e8b03d400638b841fe6038f35db3493095b9aeeb7028e5ed7dca24a187",
    ),
    "jev": (
        "nativ-community/MiniCPM-OCR-Jev-8bit", "fa1b463e56835d5d6b68253d8cd13f2f1cd54975",
        "9514c6d84f11537990d05d90f2e69431e5eb0fc81dbd116c3adb1632b15734af",
    ),
    "qwen-asr": (
        "moona3k/mlx-qwen3-asr-0.6b-8bit", "83ce2a8ef9a382d2ba2209aab383bc51fff366f5",
        "940d73134ef51218d923cce36a58f23e2286b16313a35e3b273937041069f844",
    ),
    "qwen-large": (
        "moona3k/mlx-qwen3-asr-1.7b-8bit", "22c8abe6a6772122dda5905967d7496d1d3e8dd2",
        "eba2bdb1ec74f5df99345f9f81492ba551f6b072eedfef564b353ef0dde90bb8",
    ),
    "qwen-align": (
        "Qwen/Qwen3-ForcedAligner-0.6B", "c7cbfc2048c462b0d63a45797104fc9db3ad62b7",
        "47831d0e82f96b20e9034dba01a075ee06436654719f6a68289e49f1b65ce0e7",
    ),
    "hy-mt": (
        "mlx-community/Hy-MT2-1.8B-8bit", "f54bb3b8885363fd8b83d63d50b50a12a138321f",
        "48fc521875c36d09d6d631bd74cf57304a8e8c1191fa08316437759690f3c9b7",
    ),
    "privacy": (
        "openai/privacy-filter", "7ffa9a043d54d1be65afb281eddf0ffbe629385b",
        "9c262cbe68a0c8a50590a648ef8341a2b7d3be1fa11dfb79893fe0b03ce57b5c",
    ),
    "gliner": (
        "fastino/gliner2.5-multi-v1", "7b005274e82da37dcf1f5fd9d6a2ef413c6a004c",
        "c1ff4ec0bc00031c15530b8f3c33d3677f27949e6a0cb52e1247a6224b6c5395",
    ),
    "chronos": (
        "amazon/chronos-2", "29ec3766d36d6f73f0696f85560a422f50e8498c",
        "ddcda3c7508bf2528087723e98a20707cc04b7f370ae275a9fd88078ddba4f42",
    ),
    "kokoro": (
        "mlx-community/Kokoro-82M-bf16", "a71e4d38b236d968966a2002c4c895dbd12b1c3c",
        "4e9ecdf03b8b6cf906070390237feda473dc13327cb8d56a43deaa374c02acd8",
    ),
    "sam-audio": (
        "mlx-community/sam-audio-small", "4ca84acc5c47f64bb2acee448f835dfac65ed318",
        "ae851c17699821e4a7a7c6b0aae44be61c190ceb3c9a603b2a2e5b327d2509f8",
    ),
    "sam3": (
        "mlx-community/sam3-bf16", "dfe573c3171dbcfda8399c650d9135afa7e94592",
        "09badb342d2fa10e617a78116dfe8e39d3f35ede1a8881e49f3be4609a384e14",
    ),
    "timesfm": (
        "google/timesfm-3.0-pytorch", "43046b85ec22d584a13f8098c2ed39c889e129c2",
        "a7592b0a8432baee54483254e5647856911ce69e09d09a9bb65904b2d98f17da",
    ),
    "jina-code-05": (
        "jinaai/jina-code-embeddings-0.5b-mlx", "62add943d3052062c67b0d73b42ce9c671b9051f",
        "23b4ea15302a07120c52e33f864d99f6d6ed09a26e6bc599179ea7dc36e4e4a9",
    ),
    "qwen-reranker": (
        "Qwen/Qwen3-VL-Reranker-2B", "4bd860ac4f15ad1897a214615cccc700f8f71818",
        "466ec01961061e9d7f804b4fb1625fb6f406106cd1567e026096d4736fa9d5b9",
    ),
    "qwen-reranker-4bit": (
        "mlx-community/Qwen3-VL-Reranker-2B-4bit", "374a7dc08e7c3b553c8b2730a425e53c7a926510",
        "2b2159b9bd0330c13d68307ae015f01c23d800a27db84eb4ef8fd97a03aceb0e",
    ),
    "smolvla": (
        "lerobot/smolvla_base", "5e8d12a6e2975b0e5e5fce7c8caf47c371d257b6",
        "7cd549ac2351fb069c0ddb3c34ad2d09cfc92b56a15dccdfc2e41467aaca01eb",
    ),
    "smolvlm-config": (
        "HuggingFaceTB/SmolVLM2-500M-Video-Instruct", "4cde9d208e19519c36917aa170fffc7e381aa0ad",
        "ea6bc1237e96247f6258de3e202e2e62b93d6f386dc47e7b36b5588bf3a15e17",
    ),
    "swiftvr": (
        "H-oliday/SwiftVR", "a0b09461bd89847712dd91dbb4c63541b4693936",
        "f7ade5b8f7f4ff8b4e26a581772ebe5bcfb6a619ece2dd3483c5395c2d7e1a31",
    ),
    "clef-flash-4bit": (
        "mlx-community/clef-flash-4bit", "b5adbe2c3a95200d4bf04a0727c8ec457157d5e1",
        "39894f085d844004c8e5c2394e45b5ab66bce4637ecdf23d92bf7c85cb66238f",
    ),
    "seedvr2-3b-8bit": (
        "AbstractFramework/seedvr2-3b-8bit", "6e6b162d1e96c873ad93645508bbc4636814c0c7",
        "a68bb0bf17470d417678b16dd51ec8a6410b7c533886aefeda47aedfe0235145",
    ),
}

kind, location = sys.argv[1:]
repo, revision, expected = MODELS[kind]
dest = Path(location)
allowed = {
    "privacy": ["original/*"],
    "gliner": ["config.json", "encoder_config/*", "model.safetensors", "tokenizer.json", "tokenizer_config.json"],
    "chronos": ["config.json", "model.safetensors"],
    "kokoro": ["config.json", "kokoro-v1_0.safetensors", "voices/af_heart.safetensors", "voices/zf_xiaobei.safetensors"],
    "jina-code-05": ["config.json", "model.py", "model.safetensors", "tokenizer.json", "tokenizer_config.json"],
    "qwen-reranker": ["*.json", "model.safetensors", "merges.txt", "*.jinja"],
    "qwen-reranker-4bit": ["*.json", "model.safetensors", "merges.txt", "*.jinja"],
    "smolvla": ["*.json", "*.safetensors"],
    "smolvlm-config": ["*.json", "merges.txt"],
    "swiftvr": ["transformer/config.json", "transformer/diffusion_pytorch_model.safetensors",
                "reae.safetensors", "prompt_embedding.safetensors"],
    "clef-flash-4bit": ["*.json", "*.jinja", "*.safetensors", "clef_mlx.py"],
}
if kind != "seedvr2-3b-8bit":
    snapshot_download(
        repo_id=repo, revision=revision, local_dir=dest, token=False,
        allow_patterns=allowed.get(kind),
        ignore_patterns=[".eval_results/*", ".gitattributes", "*.md"],
    )
filename = {
    "layout": "inference.pdiparams",
    "qwen-asr": "weights.safetensors",
    "qwen-large": "weights.safetensors",
    "privacy": "original/model.safetensors",
    "kokoro": "kokoro-v1_0.safetensors",
    "smolvlm-config": "config.json",
    "swiftvr": "transformer/diffusion_pytorch_model.safetensors",
    "clef-flash-4bit": "model-00001-of-00002.safetensors",
    "seedvr2-3b-8bit": "transformer/0.safetensors",
}.get(kind, "model.safetensors")
digests = {filename: expected}
if kind == "kokoro":
    digests.update({
        "voices/af_heart.safetensors": "2c1c733b0e6576c810e268d3e440c21dea4e0f0131a3ba4cfc98d7fe6136d094",
        "voices/zf_xiaobei.safetensors": "cbda378bbe266c735aa13c94c20b6224f2f8d0e16cf3abe612a4e6d93ebeab51",
    })
elif kind == "sam3":
    digests["tokenizer.json"] = "6d9109cc838977f3ca94a379eec36aecc7c807e1785cd729660ca2fc0171fb35"
elif kind == "jina-code-05":
    digests["model.py"] = "ad9f3815e65243c6a93ceeae76f0e26cd41a3bd5eb8eb27086f44f8031e34082"
elif kind in {"qwen-reranker", "qwen-reranker-4bit"}:
    template = "additional_chat_templates/reranker.jinja"
    if kind == "qwen-reranker-4bit":
        original, upstream_revision, _ = MODELS["qwen-reranker"]
        hf_hub_download(repo_id=original, filename=template, revision=upstream_revision, local_dir=dest, token=False)
    digests[template] = "47c758cb74d7f1e20e22483949a5ba4c8c1f4515126ad173da1c63211f472aa7"
elif kind == "smolvla":
    processor_digest = "490ab239d96e263687c0b2e386a0afbc235a2eceb9857c36ed32f2f162a3e7c8"
    digests["policy_postprocessor_step_0_unnormalizer_processor.safetensors"] = processor_digest
    digests["policy_preprocessor_step_5_normalizer_processor.safetensors"] = processor_digest
elif kind == "smolvlm-config":
    digests["tokenizer.json"] = "5ece781dc8d2b2f3e2f289ca0ae50b17cfc27dd27bfe7971bb8241e0b964331a"
    digests["processor_config.json"] = "f3ad45028447b3562b4752be0d5916d6806c1ef589091a469608dcf0faa1737c"
elif kind == "swiftvr":
    digests.update({
        "transformer/config.json": "dc00d9866e72cf77db6b531aaa33be4dc7148fef9338442bd0ae9181f7075e9b",
        "reae.safetensors": "c915205d1833677b6887e2fdf675499d3fc781af0c644c99330f7d22fd855514",
        "prompt_embedding.safetensors": "cc4cf7b9aa9def4026bb5952b8aaec846ffc83eee43cafff0d3796b7e9fdf922",
    })
elif kind == "clef-flash-4bit":
    digests.update({
        "clef_mlx.py": "852223c944819a32fad5cf798d9d1dff30419820eaf5ad1f10cb9698afec97d5",
        "joint_head.safetensors": "19cdcec8c81dc9212be320fff47462ab342fbc1278be4368fb3da71241cf5ba0",
        "model-00002-of-00002.safetensors": "40258d3d4f7225a0acbb45f4d34693465b98c8e2c0a4b0a512e536750379fcf3",
        "tokenizer.json": "a5cd9732badce41de57e6efce8302930ded1c1188c5f81feb2bd6c24c4a1941f",
    })
elif kind == "seedvr2-3b-8bit":
    digests.update({
        "transformer/1.safetensors": "85eae079a8138a63062cb05e03c5d45831aeeabb6332f23a1cc07691cc24f75f",
        "vae/0.safetensors": "74b7f7b71d22220f7e09a6602420d82a8fa72cbdbe4a170226ddb270cc65af42",
        "transformer/model.safetensors.index.json": "9970e8b948bac87337d1a47fb3be6a498c9382a214e248bf95dfb1e505518241",
        "vae/model.safetensors.index.json": "2351931fcdad11321d1a151ea0230eff1c6a7c12c62ade4544a3e02d7a8051bf",
    })
    # Use the pinned HTTPS files directly. The Xet reconstruction failed on
    # the first install, but the same immutable revision worked over HTTPS.
    dest.mkdir(parents=True, exist_ok=True)
    with (dest / ".download.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        for filename, digest in digests.items():
            target = dest / filename
            if target.is_file():
                continue
            target.parent.mkdir(exist_ok=True)
            partial = target.with_suffix(target.suffix + ".partial")
            subprocess.run([
                "/usr/bin/curl", "-fsSL", "--retry", "3", "--continue-at", "-",
                f"https://huggingface.co/{repo}/resolve/{revision}/{filename}", "-o", str(partial),
            ], check=True)
            with partial.open("rb") as weights:
                verified = hashlib.file_digest(weights, "sha256").hexdigest() == digest
            if not verified:
                partial.unlink()
                (dest / ".verified").unlink(missing_ok=True)
                raise SystemExit(f"Unexpected digest for {filename} from {repo}@{revision}")
            partial.replace(target)
for filename, digest in digests.items():
    with (dest / filename).open("rb") as weights:
        if hashlib.file_digest(weights, "sha256").hexdigest() != digest:
            (dest / ".verified").unlink(missing_ok=True)
            raise SystemExit(f"Unexpected digest for {filename} from {repo}@{revision}")
with tempfile.NamedTemporaryFile(mode="w", dir=dest, prefix=".verify-", delete=False) as marker:
    marker.write(f"{repo}@{revision}\n")
try:
    os.replace(marker.name, dest / ".verified")
finally:
    Path(marker.name).unlink(missing_ok=True)
