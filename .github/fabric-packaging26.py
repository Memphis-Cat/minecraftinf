#!/usr/bin/env python3
"""Package the linked CubicChunksCore classes inside the Fabric mod jar."""

from pathlib import Path

path = Path("build.gradle")
text = path.read_text(encoding="utf-8")

# Loom's include configuration only accepts module components with capabilities;
# CubicChunksCore-linked.jar is a deliberately transformed local file. Keep it
# as a normal implementation dependency for compile/run, and merge its classes
# into the mod jar before Loom remaps the finished archive.
text = text.replace("    include files(linkedCoreJar)\n", "")

snippet = """tasks.named('jar') {
    dependsOn requireLinkedCore
    from({ zipTree(linkedCoreJar) }) {
        exclude 'META-INF/**'
    }
    duplicatesStrategy = org.gradle.api.file.DuplicatesStrategy.EXCLUDE
}

"""
if "from({ zipTree(linkedCoreJar) })" not in text:
    marker = "def requireRawMinecraftClient = tasks.register('requireRawMinecraftClient') {\n"
    if marker not in text:
        raise SystemExit("Unable to insert CubicChunksCore jar packaging")
    text = text.replace(marker, snippet + marker, 1)

path.write_text(text, encoding="utf-8")
print("Configured CubicChunksCore classes for direct Fabric jar packaging")
