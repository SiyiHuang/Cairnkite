"""Run the pinned Lean kernel on a scoped copy and inspect the proof's axioms."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
LEAN = ROOT / ".runtime/lean/bin/lean"
MATHLIB = ROOT / ".runtime/lean-mathlib"
STANDARD_AXIOMS = {"Classical.choice", "Quot.sound", "propext"}


def run_lean(temp, args, output="/dev/null", *, library="lean"):
    mathlib = library == "mathlib"
    path = ""
    if mathlib:
        path = os.pathsep.join(
            str((MATHLIB / entry).resolve())
            for entry in (MATHLIB / ".lean-path").read_text(encoding="utf-8").strip().split(os.pathsep)
            if entry
        )
    return subprocess.run([
        "/usr/bin/sandbox-exec", "-f", str(ROOT / "src/lean-check.sb"),
        "-D", f"LEAN_ROOT={LEAN.parents[1]}", "-D", f"LEAN_BINARY={LEAN}", "-D", f"PROOF_DIR={temp}",
        "-D", f"LEAN_MATHLIB={MATHLIB if mathlib else '/dev/null'}",
        "-D", f"PROOF_OUTPUT={output}", "-D", f"PROOF_TEMP={output}.tmp",
        str(LEAN), f"--root={temp}", "-t0", "-j1", "-M4096" if mathlib else "-M1024",
        "-T120000", *args,
    ], cwd=temp, env={"PATH": "/usr/bin:/bin", "LEAN_PATH": path, "LC_ALL": "C"},
       capture_output=True, text=True, timeout=17 if mathlib else 8, check=False)


def check(source, declaration, statement, library="lean"):
    if library not in {"lean", "mathlib"}:
        raise ValueError("Unknown Lean library.")
    if library == "mathlib" and not (MATHLIB / ".verified").is_file():
        raise ValueError("Run bin/install lean-mathlib to install the pinned Mathlib.")
    axioms = []
    matched = False
    audited = False
    diagnostics = []
    with tempfile.TemporaryDirectory(prefix="lean-proof-", dir=ROOT / ".runtime") as temp:
        path = Path(temp) / "Checked.lean"
        compiled = path.with_suffix(".olean")
        path.write_text(source, encoding="utf-8")
        result = run_lean(temp, ["-o", str(compiled), str(path)], compiled, library=library)
        diagnostics.extend([result.stdout, result.stderr])
        expected = ""
        signature_ok = True
        if result.returncode == 0 and statement is not None:
            signature = Path(temp) / "Expected.lean"
            expected = str(signature.with_suffix(".olean"))
            module = "Mathlib" if library == "mathlib" else "Lean"
            signature.write_text(f"import {module}\naxiom localToolkitStatement : {statement}\n", encoding="utf-8")
            comparison = run_lean(temp, ["-o", expected, str(signature)], expected, library=library)
            diagnostics.extend([comparison.stdout, comparison.stderr])
            signature_ok = comparison.returncode == 0
        if result.returncode == 0 and signature_ok:
            audit_source = Path(temp) / "LeanAudit.lean"
            audit_source.write_bytes((ROOT / "src/LeanAudit.lean").read_bytes())
            audit = run_lean(temp, ["--run", str(audit_source), str(compiled), declaration, expected, library],
                             library=library)
            if audit.returncode == 0:
                data = json.loads(audit.stdout)
                axioms = sorted(set(data["axioms"]))
                matched = data["statement_matches"]
                audited = True
                if statement is not None and not matched:
                    diagnostics.append("The proof's type does not match the expected proposition.")
            else:
                diagnostics.extend([audit.stdout, audit.stderr])
    accepted = audited and set(axioms) <= STANDARD_AXIOMS and (statement is None or matched)
    diagnostics = "\n".join(x.strip() for x in diagnostics if x.strip()).replace(f"{temp}/", "")
    return {"backend": "lean-4.9.0", "library": library, "declaration": declaration, "compiled": result.returncode == 0,
            "accepted": accepted, "axioms": axioms,
            "statement_checked": matched,
            "diagnostics": diagnostics.strip()[-4500:]}


if __name__ == "__main__":
    request = json.load(sys.stdin)
    print(json.dumps(check(request["source"], request["declaration"], request.get("statement"),
                           request.get("library", "lean")), ensure_ascii=False))
