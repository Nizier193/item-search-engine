from pathlib import Path
from benchmark.benchmark import run_dataset

metrics = run_dataset(
    Path("datasets/fold_3/queries.jsonl"), 
    top_k=5, 
    threshold=0.2
)
print(metrics)