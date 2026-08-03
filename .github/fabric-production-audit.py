#!/usr/bin/env python3
"""Reject known no-op CubicChunks runtime implementations before publishing Fabric 26.2."""

from __future__ import annotations

from pathlib import Path

ROOT = Path("src/main/java")

FORBIDDEN = {
    "io/github/opencubicchunks/cubicchunks/mixin/core/common/world/level/chunk/storage/MixinChunkStorage.java": (
        "return false; // TODO (P2) should be dasm'd once IOWorker is done",
        "return CompletableFuture.completedFuture(Optional.empty());",
        "// TODO (P2) loading/unloading",
    ),
}


def main() -> int:
    failures: list[str] = []
    for relative, markers in FORBIDDEN.items():
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"missing required runtime source: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker in text:
                failures.append(f"unfinished runtime implementation in {path}: {marker}")

    if failures:
        print("Fabric 26.2 production audit failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Fabric 26.2 production audit passed: no known no-op storage implementations remain.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
