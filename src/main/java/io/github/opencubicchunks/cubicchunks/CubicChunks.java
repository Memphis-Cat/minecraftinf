package io.github.opencubicchunks.cubicchunks;

import java.lang.reflect.InvocationTargetException;

import io.github.opencubicchunks.cc_core.CubicChunksBase;
import io.github.opencubicchunks.cc_core.config.EarlyConfig;
import io.github.opencubicchunks.cc_core.utils.Coords;
import io.github.opencubicchunks.cubicchunks.config.CommonConfig;
import net.fabricmc.api.ModInitializer;
import net.minecraft.SharedConstants;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ChunkMap;

public class CubicChunks extends CubicChunksBase implements ModInitializer {
    public static boolean IS_IN_TEST = false;
    protected static CommonConfig config = null;
    public static final int SUPERFLAT_HEIGHT = 5;

    @Override
    public void onInitialize() {
        ChunkMap.class.getName();
        EarlyConfig.getDiameterInSections();
        Coords.blockToIndex(new BlockPos(0, 0, 0));

        if (System.getProperty("cubicchunks.debug", "false").equalsIgnoreCase("true")) {
            try {
                Class.forName("io.github.opencubicchunks.cubicchunks.debug.DebugVisualization").getMethod("enable").invoke(null);
                SharedConstants.IS_RUNNING_IN_IDE = true;
            } catch (IllegalAccessException | InvocationTargetException | NoSuchMethodException | ClassNotFoundException exception) {
                LOGGER.catching(exception);
            }
        }
    }

    public static CommonConfig config() {
        if (config == null) {
            config = CommonConfig.getConfig();
        }
        return config;
    }
}
