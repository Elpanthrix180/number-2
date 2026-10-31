package com.panthrix.naturaldisasters.event;

import com.panthrix.naturaldisasters.config.CatastropheConfig;
import com.panthrix.naturaldisasters.core.BlockProtection;
import com.panthrix.naturaldisasters.core.CatastropheEvent;
import com.panthrix.naturaldisasters.core.CatastropheManager;
import com.panthrix.naturaldisasters.core.CatastrophePhase;
import com.panthrix.naturaldisasters.core.CatastropheSavedData;
import com.panthrix.naturaldisasters.core.CatastropheType;
import com.panthrix.naturaldisasters.event.DisasterUtil;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.FarmBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.Property;

public class DroughtEvent
extends CatastropheEvent {
    @Override
    public void onPhaseStart(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase) {
        switch (phase) {
            case PREPARATION: 
            case ACTIVE: {
                level.setWeatherParameters(36000, 0, false, false);
                break;
            }
            case RECOVERY: {
                level.setWeatherParameters(0, 2400, true, false);
                break;
            }
        }
    }

    @Override
    public void tick(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase, long now) {
        if (phase != CatastrophePhase.ACTIVE && phase != CatastrophePhase.ENDING) {
            return;
        }
        if (now % 200L == 0L && level.isRaining()) {
            level.setWeatherParameters(36000, 0, false, false);
        }
        if (now % 10L == 0L) {
            int count = (int)(12.0 * CatastropheConfig.intensityFactor());
            for (ServerPlayer p : DisasterUtil.playersInArea(level, d)) {
                level.sendParticles((ParticleOptions)ParticleTypes.WHITE_ASH, p.getX(), p.getY() + 1.0, p.getZ(), count, 6.0, 2.0, 6.0, 0.02);
            }
        }
        if (phase == CatastrophePhase.ACTIVE && now % 40L == 0L && ((Boolean)CatastropheConfig.DROUGHT_DRY_FARMLAND.get()).booleanValue() && !CatastropheConfig.destructionOff()) {
            int tries = 1 + (int)(2.0 * CatastropheConfig.intensityFactor());
            for (int i = 0; i < tries; ++i) {
                BlockPos pos = DisasterUtil.randomSurface(level, d, level.getRandom());
                if (pos == null) continue;
                for (BlockPos p : new BlockPos[]{pos.below(), pos}) {
                    BlockState s = level.getBlockState(p);
                    if (!s.is(Blocks.FARMLAND) || (Integer)s.getValue((Property)FarmBlock.MOISTURE) <= 0 || !BlockProtection.canModify(level, p, s) || !DisasterUtil.takeBlockBudget(d)) continue;
                    level.setBlock(p, (BlockState)s.setValue((Property)FarmBlock.MOISTURE, (Comparable)Integer.valueOf(0)), 2);
                }
            }
        }
    }

    @Override
    public void onFinish(ServerLevel level, CatastropheSavedData d) {
    }

    /** true si la sequia debe impedir este intento de crecimiento del cultivo. */
    public static boolean shouldBlockGrowth(ServerLevel level, BlockPos pos) {
        if (level.dimension() != Level.OVERWORLD) {
            return false;
        }
        if (!CatastropheConfig.DROUGHT_CROPS.get().booleanValue()) {
            return false;
        }
        CatastropheSavedData d = CatastropheManager.data(level.getServer());
        if (d.activeType != CatastropheType.DROUGHT) {
            return false;
        }
        if (d.phase != CatastrophePhase.ACTIVE && d.phase != CatastrophePhase.ENDING) {
            return false;
        }
        if (!DisasterUtil.inArea(d, pos.getX(), pos.getZ())) {
            return false;
        }
        double chance = Math.min(0.9, 0.45 * CatastropheConfig.intensityFactor());
        return level.getRandom().nextDouble() < chance;
    }
}
