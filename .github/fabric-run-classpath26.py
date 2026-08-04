#!/usr/bin/env python3
"""Use Mojang's complete Minecraft 26.2 jar for Loom development runs."""

from pathlib import Path

path = Path("build.gradle")
text = path.read_text(encoding="utf-8")

snippet = r'''// Loom's merged-deobf 26.2 artifact in this project is resources-only. The
// development launch tasks must use the same complete, access-widened Mojang jar
// as javac or Fabric Loader cannot discover the Minecraft game provider.
tasks.matching { it.name == 'runClient' || it.name == 'runServer' }.configureEach {
    dependsOn prepareMinecraftCompileHeaders
    doFirst {
        def widenedPath = widenedMinecraftClientJar.canonicalPath
        def filteredRuntimeClasspath = classpath.filter { candidate ->
            def normalized = candidate.canonicalPath.replace('\\', '/')
            candidate.canonicalPath != widenedPath &&
                    !(candidate.name.startsWith('minecraft-merged-deobf-') && normalized.contains('/fabric-loom/minecraftMaven/'))
        }
        classpath = files(widenedMinecraftClientJar) + filteredRuntimeClasspath
    }
}

'''

if "development launch tasks must use the same complete" not in text:
    marker = "tasks.register('printMainCompileClasspath') {\n"
    if marker not in text:
        raise SystemExit("Unable to insert Minecraft 26.2 development runtime classpath")
    text = text.replace(marker, snippet + marker, 1)

path.write_text(text, encoding="utf-8")
print("Configured complete Minecraft 26.2 runtime classpath for Loom launch tasks")
