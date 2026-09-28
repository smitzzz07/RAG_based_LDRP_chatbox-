from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parent


def run(script):
    print("\n" + "=" * 70)
    print(f"RUNNING: {script}")
    print("=" * 70)

    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "rag" / script)],
        cwd=PROJECT_ROOT,
    )

    if result.returncode != 0:
        raise SystemExit(
            f"\n❌ {script} failed with exit code {result.returncode}"
        )


def main():
    print("=" * 70)
    print("       LDRP RAG - BUILD COMPLETE KNOWLEDGE BASE")
    print("=" * 70)

    # All PDFs currently present in data/raw/ are processed.
    run("loader.py")
    run("chunker.py")

    # website_chunks.json is reused if it already exists.
    run("combine_chunks.py")
    run("embeddings.py")
    run("vector_store.py")

    print("\n" + "=" * 70)
    print("✅ COMPLETE KNOWLEDGE BASE BUILD FINISHED")
    print("=" * 70)
    print("You can now restart the FastAPI backend.")
    print()


if __name__ == "__main__":
    main()
