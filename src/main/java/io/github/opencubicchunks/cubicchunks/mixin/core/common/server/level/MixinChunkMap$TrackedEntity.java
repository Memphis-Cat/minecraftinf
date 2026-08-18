package io.github.opencubicchunks.cubicchunks.mixin.core.common.server.level;

import io.github.notstirred.dasm.api.annotations.Dasm;
import io.github.notstirred.dasm.api.annotations.redirect.redirects.AddTransformToSets;
import io.github.notstirred.dasm.api.annotations.selector.Ref;
import io.github.notstirred.dasm.api.annotations.transform.TransformFromMethod;
import io.github.opencubicchunks.cubicchunks.mixin.dasmsets.ChunkToCloSet;
import io.github.opencubicchunks.cubicchunks.server.level.CubicChunkMap;
import io.github.opencubicchunks.cubicchunks.server.level.EntityTracking;
import io.github.opencubicchunks.cubicchunks.world.entity.EntityCubePosGetter;
import net.minecraft.server.level.ChunkMap;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Dynamic;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

@Dasm(value = ChunkToCloSet.class, target = @Ref(ChunkMap.TrackedEntity.class))
@Mixin(ChunkMap.TrackedEntity.class)
public abstract class MixinChunkMap$TrackedEntity {
    @Shadow @Final Entity entity;

    // region [cc_updatePlayer dasm + mixin]
    @AddTransformToSets(ChunkToCloSet.ChunkMap$TrackedEntity_redirects.class)
    @TransformFromMethod("updatePlayer(Lnet/minecraft/server/level/ServerPlayer;)V")
    public native void cc_updatePlayer(ServerPlayer player);

    @Dynamic @Redirect(method = "cc_updatePlayer", at = @At(value = "INVOKE", target = "Lnet/minecraft/server/level/ChunkMap;isChunkTracked(Lnet/minecraft/server/level/ServerPlayer;II)Z"))
    private boolean cc_updatePlayer_isChunkTracked(ChunkMap instance, ServerPlayer player, int x, int z) {
        return EntityTracking.isTracked((CubicChunkMap) instance, player, (EntityCubePosGetter) this.entity);
    }
    // endregion
}
