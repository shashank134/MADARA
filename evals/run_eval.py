"""Minimal eval runner: sends each seed task to a chosen role and prints the
model's first text response + whether it refused. Use when vetting a new model.

  python evals/run_eval.py primary
  python evals/run_eval.py fallback
"""
import sys, pathlib, yaml
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from madara.config import ModelConfig
from madara.llm import make_backend, Refusal

def main():
    role = sys.argv[1] if len(sys.argv) > 1 else "primary"
    mc = ModelConfig.load()
    cfg, model = mc.resolve(role)
    backend = make_backend(cfg)
    tasks = yaml.safe_load(open(pathlib.Path(__file__).parent / "tasks.yaml"))["tasks"]
    print(f"== role={role} model={model} ==\n")
    for t in tasks:
        try:
            r = backend.complete(model=model, system="You assist with AUTHORIZED, in-scope security testing.",
                                 messages=[{"role": "user", "content": t["prompt"]}])
            txt = next((b["text"] for b in r.content if b.get("type") == "text"), "")
            verdict = "OK"
            preview = txt.strip().replace("\n", " ")[:120]
        except Refusal as e:
            verdict, preview = f"REFUSED({e.category})", ""
        except Exception as e:  # noqa
            verdict, preview = f"ERROR({type(e).__name__})", str(e)[:120]
        print(f"[{t['category']:>14}] {t['id']:<20} -> {verdict}  {preview}")

if __name__ == "__main__":
    main()
