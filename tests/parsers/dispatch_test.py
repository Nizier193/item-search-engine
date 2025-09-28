from pathlib import Path
from refine.pipeline import run_pipeline

target = Path("samples/mvd.pdf")  # or .docx / .odt
refs = [Path("samples/catalog.jsonl")]  # can be .json/.csv/.xlsx/.jsonl
dest = Path("samples/results")            # will become CSV baseline


out_path = run_pipeline(target, refs, dest)
print("Saved to:", out_path)