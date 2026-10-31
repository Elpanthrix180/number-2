package com.panthrix.naturaldisasters.event;

import com.panthrix.naturaldisasters.config.CatastropheConfig;
import com.panthrix.naturaldisasters.core.BlockProtection;
import com.panthrix.naturaldisasters.core.CatastropheEvent;
import com.panthrix.naturaldisasters.core.CatastrophePhase;
import com.panthrix.naturaldisasters.core.CatastropheSavedData;
import com.panthrix.naturaldisasters.event.DisasterUtil;
import java.util.Arrays;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

public class BlizzardEvent
extends CatastropheEvent {
    private static final String SNOW_KEY = "snow";

    @Override
    public void onPhaseStart(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase) {
        switch (phase) {
            case PREPARATION: {
                DisasterUtil.startRain(level, false);
                break;
            }
            case RECOVERY: {
                DisasterUtil.clearWeather(level);
                BlizzardEvent.removeTemporarySnow(level, d);
                break;
            }
        }
    }

    @Override
    public void tick(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase, long now) {
        boolean active;
        if (phase != CatastrophePhase.PREPARATION && phase != CatastrophePhase.ACTIVE && phase != CatastrophePhase.ENDING) {
            return;
        }
        double f = CatastropheConfig.intensityFactor();
        boolean bl = active = phase == CatastrophePhase.ACTIVE;
        if (now % 5L == 0L) {
            int count = active ? (int)(60.0 * f) : (int)(15.0 * f);
            for (ServerPlayer p : DisasterUtil.playersInArea(level, d)) {
                level.sendParticles((ParticleOptions)ParticleTypes.SNOWFLAKE, p.getX(), p.getY() + 3.0, p.getZ(), count, 8.0, 3.0, 8.0, 0.15);
                if (!active) continue;
                level.sendParticles((ParticleOptions)ParticleTypes.WHITE_ASH, p.getX(), p.getY() + 1.0, p.getZ(), count / 2, 4.0, 2.0, 4.0, 0.05);
            }
        }
        if (now % 60L == 0L) {
            for (ServerPlayer p : DisasterUtil.playersInArea(level, d)) {
                level.playSound(null, p.blockPosition(), SoundEvents.ELYTRA_FLYING, SoundSource.WEATHER, active ? 0.4f : 0.2f, 0.5f);
            }
        }
        if (!active) {
            return;
        }
        if (now % 20L == 0L) {
            for (ServerPlayer p : DisasterUtil.playersInArea(level, d)) {
                if (!DisasterUtil.exposedToSky(level, (LivingEntity)p) || p.isCreative() || p.isSpectator()) continue;
                p.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 40, f > 1.0 ? 1 : 0, false, false));
                if (!((Boolean)CatastropheConfig.FREEZING.get()).booleanValue() || !DisasterUtil.canHurt((LivingEntity)p) || !p.canFreeze()) continue;
                int target = p.getTicksRequiredToFreeze() + 40 + (int)(20.0 * f);
                p.setTicksFrozen(Math.min(p.getTicksFrozen() + 40, target));
            }
        }
        if (((Boolean)CatastropheConfig.SNOW_ACCUMULATION.get()).booleanValue() && now % 10L == 0L) {
            int tries = 1 + (int)(2.0 * f);
            for (int i = 0; i < tries; ++i) {
                BlockState snow;
                BlockPos pos = DisasterUtil.randomSurface(level, d, level.getRandom());
                if (pos == null || !level.isEmptyBlock(pos) || !(snow = Blocks.SNOW.defaultBlockState()).canSurvive((LevelReader)level, pos) || !BlockProtection.canPlace(level, pos)) continue;
                if (!DisasterUtil.takeBlockBudget(d)) {
                    return;
                }
                level.setBlock(pos, snow, 3);
                long[] old = d.eventData.getLongArray(SNOW_KEY);
                long[] grown = Arrays.copyOf(old, old.length + 1);
                grown[old.length] = pos.asLong();
                d.eventData.putLongArray(SNOW_KEY, grown);
                d.setDirty();
            }
        }
    }

    @Override
    public void onFinish(ServerLevel level, CatastropheSavedData d) {
        DisasterUtil.clearWeather(level);
        BlizzardEvent.removeTemporarySnow(level, d);
    }

    private static void removeTemporarySnow(ServerLevel level, CatastropheSavedData d) {
        if (!((Boolean)CatastropheConfig.SNOW_TEMPORARY.get()).booleanValue()) {
            return;
        }
        for (long l : d.eventData.getLongArray(SNOW_KEY)) {
            BlockPos pos = BlockPos.of((long)l);
            if (!level.isLoaded(pos) || !level.getBlockState(pos).is(Blocks.SNOW)) continue;
            level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
        }
        d.eventData.remove(SNOW_KEY);
        d.setDirty();
    }
}

