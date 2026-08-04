#!/usr/bin/env python3
"""Configure the Fabric-compatible 26.2 unit suite and bootstrap Minecraft before discovery."""

from pathlib import Path

listener = Path("src/test/java/io/github/opencubicchunks/cubicchunks/testutils/MinecraftBootstrapListener.java")
listener.parent.mkdir(parents=True, exist_ok=True)
listener.write_text(
    """package io.github.opencubicchunks.cubicchunks.testutils;

import io.github.opencubicchunks.cubicchunks.CubicChunks;
import net.minecraft.SharedConstants;
import net.minecraft.server.Bootstrap;
import org.junit.platform.launcher.LauncherSession;
import org.junit.platform.launcher.LauncherSessionListener;

/** Bootstraps Minecraft before JUnit loads test classes with static registry references. */
public final class MinecraftBootstrapListener implements LauncherSessionListener {
    @Override public void launcherSessionOpened(LauncherSession session) {
        SharedConstants.tryDetectVersion();
        CubicChunks.IS_IN_TEST = true;
        Bootstrap.bootStrap();
        SharedConstants.IS_RUNNING_IN_IDE = true;
    }
}
""",
    encoding="utf-8",
)

service = Path("src/test/resources/META-INF/services/org.junit.platform.launcher.LauncherSessionListener")
service.parent.mkdir(parents=True, exist_ok=True)
service.write_text(
    "io.github.opencubicchunks.cubicchunks.testutils.MinecraftBootstrapListener\n",
    encoding="utf-8",
)

build = Path("build.gradle")
text = build.read_text(encoding="utf-8")
launcher_compile = "    testImplementation 'org.junit.platform:junit-platform-launcher'\n"
if launcher_compile not in text:
    anchor = "    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'\n"
    if anchor not in text:
        raise SystemExit("Unable to locate the JUnit Platform launcher dependency")
    text = text.replace(anchor, launcher_compile + anchor, 1)

suite = r'''
// The legacy NeoForge test task depended on Forge's transformed test runtime.
// Fabric's plain JVM test task runs only tests that exercise untransformed
// production code. DASM/mixin behavior is validated by the dedicated-server
// start/save/restart gate below instead of pretending raw classes are mixed in.
tasks.named('test') {
    enabled = true
    useJUnitPlatform()
    filter {
        includeTestsMatching 'io.github.opencubicchunks.cubicchunks.network.TestCubeNetworkPayloads'
        includeTestsMatching 'io.github.opencubicchunks.cubicchunks.test.server.TestServerShutdownWork'
        includeTestsMatching 'io.github.opencubicchunks.cubicchunks.test.server.level.TestCloStatusUpdates'
        includeTestsMatching 'io.github.opencubicchunks.cubicchunks.test.server.level.TestCloTrackingView'
        includeTestsMatching 'io.github.opencubicchunks.cubicchunks.test.server.level.TestCubeMapMath'
        includeTestsMatching 'io.github.opencubicchunks.cubicchunks.test.server.network.TestCloSendOrder'
        includeTestsMatching 'io.github.opencubicchunks.cubicchunks.test.client.multiplayer.TestClientCubeAvailability'
        includeTestsMatching 'io.github.opencubicchunks.cubicchunks.test.world.level.TestCubicLevelReader'
        includeTestsMatching 'io.github.opencubicchunks.cubicchunks.world.level.cube.status.TestCubeColumnBridge'
    }
}

'''
if "includeTestsMatching 'io.github.opencubicchunks.cubicchunks.network.TestCubeNetworkPayloads'" not in text:
    marker = "spotless {\n"
    if marker not in text:
        raise SystemExit("Unable to insert the Fabric-compatible unit suite")
    text = text.replace(marker, suite + marker, 1)

build.write_text(text, encoding="utf-8")
print("Configured Minecraft bootstrap and the Fabric-compatible 26.2 unit suite")
