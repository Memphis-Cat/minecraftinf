#!/usr/bin/env python3
"""Port Minecraft 26.2 player-spawn loading to cubic ticket APIs."""

from pathlib import Path

# Add the transformed asynchronous cube ticket API used by PrepareSpawnTask.
iface = Path("src/main/java/io/github/opencubicchunks/cubicchunks/server/level/ServerCubeCache.java")
text = iface.read_text(encoding="utf-8")
anchor = "    void cc_addTicketWithRadius(TicketType ticket, CloPos cloPos, int radius);\n"
addition = "    CompletableFuture<?> cc_addTicketAndLoadWithRadius(TicketType ticket, CloPos cloPos, int radius);\n\n"
if addition.strip() not in text:
    if anchor not in text:
        raise SystemExit("Unable to add the asynchronous cube ticket API")
    text = text.replace(anchor, anchor + "\n" + addition, 1)
iface.write_text(text, encoding="utf-8")

mixin = Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/level/MixinServerChunkCache.java")
text = mixin.read_text(encoding="utf-8")
anchor = '''    @AddTransformToSets(ChunkToCloSet.ServerChunkCache_redirects.class)
    @TransformFromMethod(useRedirectSets = ChunkToCloSet.class, value = "addTicketWithRadius(Lnet/minecraft/server/level/TicketType;Lnet/minecraft/world/level/ChunkPos;I)V")
    public native void cc_addTicketWithRadius(TicketType ticket, CloPos cloPos, int radius);
'''
addition = '''
    @AddTransformToSets(ChunkToCloSet.ServerChunkCache_redirects.class)
    @TransformFromMethod(useRedirectSets = ChunkToCloSet.class, value = "addTicketAndLoadWithRadius(Lnet/minecraft/server/level/TicketType;Lnet/minecraft/world/level/ChunkPos;I)Ljava/util/concurrent/CompletableFuture;")
    public native CompletableFuture<?> cc_addTicketAndLoadWithRadius(TicketType ticket, CloPos cloPos, int radius);
'''
if "public native CompletableFuture<?> cc_addTicketAndLoadWithRadius" not in text:
    if anchor not in text:
        raise SystemExit("Unable to transform ServerChunkCache.addTicketAndLoadWithRadius")
    text = text.replace(anchor, anchor + addition, 1)
mixin.write_text(text, encoding="utf-8")

pkg = Path("src/main/java/io/github/opencubicchunks/cubicchunks/mixin/core/common/server/network/config")
pkg.mkdir(parents=True, exist_ok=True)
(pkg / "MixinPrepareSpawnTask$Preparing.java").write_text('''package io.github.opencubicchunks.cubicchunks.mixin.core.common.server.network.config;

import java.util.concurrent.CompletableFuture;

import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cc_core.world.level.CloPos;
import io.github.opencubicchunks.cubicchunks.CanBeCubic;
import io.github.opencubicchunks.cubicchunks.server.level.ServerCubeCache;
import net.minecraft.server.level.ServerChunkCache;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.TicketType;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.phys.Vec3;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;

@Mixin(targets = "net.minecraft.server.network.config.PrepareSpawnTask$Preparing")
public abstract class MixinPrepareSpawnTask$Preparing {
    @Shadow @Final private ServerLevel spawnLevel;
    @Shadow @Final private CompletableFuture<Vec3> spawnPosition;

    @WrapOperation(method = "lambda$tick$0", at = @At(value = "INVOKE", target = "Lnet/minecraft/server/level/ServerChunkCache;addTicketAndLoadWithRadius(Lnet/minecraft/server/level/TicketType;Lnet/minecraft/world/level/ChunkPos;I)Ljava/util/concurrent/CompletableFuture;"))
    private CompletableFuture<?> cc_loadSpawnCube(
            ServerChunkCache cache, TicketType type, ChunkPos pos, int radius, Operation<CompletableFuture<?>> original
    ) {
        CompletableFuture<?> columnFuture = original.call(cache, type, pos, radius);
        if (!((CanBeCubic) this.spawnLevel).cc_isCubic()) {
            return columnFuture;
        }
        Vec3 spawn = this.spawnPosition.join();
        CloPos cubePos = CloPos.cube(CubePos.from(spawn.x, spawn.y, spawn.z));
        CompletableFuture<?> cubeFuture = ((ServerCubeCache) cache).cc_addTicketAndLoadWithRadius(type, cubePos, radius);
        return CompletableFuture.allOf(columnFuture, cubeFuture);
    }
}
''', encoding="utf-8")
(pkg / "MixinPrepareSpawnTask$Ready.java").write_text('''package io.github.opencubicchunks.cubicchunks.mixin.core.common.server.network.config;

import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import io.github.opencubicchunks.cc_core.api.CubePos;
import io.github.opencubicchunks.cc_core.world.level.CloPos;
import io.github.opencubicchunks.cubicchunks.CanBeCubic;
import io.github.opencubicchunks.cubicchunks.server.level.ServerCubeCache;
import net.minecraft.server.level.ServerChunkCache;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.TicketType;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.phys.Vec3;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;

@Mixin(targets = "net.minecraft.server.network.config.PrepareSpawnTask$Ready")
public abstract class MixinPrepareSpawnTask$Ready {
    @Shadow @Final private ServerLevel spawnLevel;
    @Shadow @Final private Vec3 spawnPosition;

    @WrapOperation(method = "keepAlive", at = @At(value = "INVOKE", target = "Lnet/minecraft/server/level/ServerChunkCache;addTicketWithRadius(Lnet/minecraft/server/level/TicketType;Lnet/minecraft/world/level/ChunkPos;I)V"))
    private void cc_keepSpawnCubeAlive(
            ServerChunkCache cache, TicketType type, ChunkPos pos, int radius, Operation<Void> original
    ) {
        original.call(cache, type, pos, radius);
        if (((CanBeCubic) this.spawnLevel).cc_isCubic()) {
            CloPos cubePos = CloPos.cube(CubePos.from(this.spawnPosition.x, this.spawnPosition.y, this.spawnPosition.z));
            ((ServerCubeCache) cache).cc_addTicketWithRadius(type, cubePos, radius);
        }
    }
}
''', encoding="utf-8")

required = (
    "cc_addTicketAndLoadWithRadius",
    "PrepareSpawnTask$Preparing",
    "PrepareSpawnTask$Ready",
    "CompletableFuture.allOf(columnFuture, cubeFuture)",
)
combined = iface.read_text(encoding="utf-8") + mixin.read_text(encoding="utf-8")
combined += "".join(path.read_text(encoding="utf-8") for path in pkg.glob("*.java"))
for marker in required:
    if marker not in combined:
        raise SystemExit(f"Missing Minecraft 26.2 spawn migration marker: {marker}")
print("Migrated Minecraft 26.2 player-spawn cube loading and keepalive tickets")
