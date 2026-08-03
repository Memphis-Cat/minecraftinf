from pathlib import Path

for relative in (
    "buildSrc/src/main/java/io/github/opencubicchunks/gradle/MixinGenExtension.java",
    "buildSrc/src/main/java/io/github/opencubicchunks/gradle/DasmGenExtension.java",
):
    path = Path(relative)
    text = path.read_text(encoding="utf-8")
    if "JavaPluginConvention" not in text:
        raise SystemExit(f"Expected Gradle 8 JavaPluginConvention use was not found in {relative}")
    path.write_text(text.replace("JavaPluginConvention", "JavaPluginExtension"), encoding="utf-8")
