from pathlib import Path

for relative in (
    "buildSrc/src/main/java/io/github/opencubicchunks/gradle/MixinGenExtension.java",
    "buildSrc/src/main/java/io/github/opencubicchunks/gradle/DasmGenExtension.java",
):
    path = Path(relative)
    text = path.read_text(encoding="utf-8")
    if "JavaPluginConvention" in text:
        path.write_text(text.replace("JavaPluginConvention", "JavaPluginExtension"), encoding="utf-8")
    elif "JavaPluginExtension" not in text:
        raise SystemExit(f"Expected Gradle Java plugin API use was not found in {relative}")

core_build = Path("CubicChunksCore/build.gradle")
core_text = core_build.read_text(encoding="utf-8")
if "jcenter()" in core_text:
    core_build.write_text(core_text.replace("jcenter()", "mavenCentral()"), encoding="utf-8")
elif "mavenCentral()" not in core_text:
    raise SystemExit("Expected a Maven repository declaration in CubicChunksCore/build.gradle")
