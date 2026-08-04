#!/usr/bin/env python3
"""Apply deterministic Minecraft 26.2 runtime and packaging adaptations."""

import runpy

scripts = (
    (".github/fabric-packaging26.py", "__fabric_packaging26__"),
    (".github/fabric-run-classpath26.py", "__fabric_run_classpath26__"),
    (".github/fabric-level26-runtime.py", "__fabric_level26_runtime__"),
    (".github/fabric-serverlevel26-runtime.py", "__fabric_serverlevel26_runtime__"),
    (".github/fabric-serverlevel-spawn26.py", "__fabric_serverlevel_spawn26__"),
    (".github/fabric-chunkholder26-runtime.py", "__fabric_chunkholder26_runtime__"),
    (".github/fabric-prepare-spawn26.py", "__fabric_prepare_spawn26__"),
    (".github/fabric-accesswidener26.py", "__fabric_accesswidener26__"),
)
for script, name in scripts:
    runpy.run_path(script, run_name=name)
print("Applied Minecraft 26.2 runtime and packaging adaptations")
