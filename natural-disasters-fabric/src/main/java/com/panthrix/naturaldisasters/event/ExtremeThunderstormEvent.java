package com.panthrix.naturaldisasters.event;

import com.panthrix.naturaldisasters.config.CatastropheConfig;
import com.panthrix.naturaldisasters.core.CatastropheEvent;
import com.panthrix.naturaldisasters.core.CatastrophePhase;
import com.panthrix.naturaldisasters.core.CatastropheSavedData;
import com.panthrix.naturaldisasters.event.DisasterUtil;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Vec3i;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

public class ExtremeThunderstormEvent
extends CatastropheEvent {
    private static final int MAX_BOLTS_PER_EVENT = 300;

    @Override
    public void onPhaseStart(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase) {
        switch (phase) {
            case PREPARATION: {
                DisasterUtil.startRain(level, true);
                break;
            }
            case RECOVERY: {
                DisasterUtil.clearWeather(level);
                break;
            }
        }
    }

    @Override
    public void tick(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase, long now) {
        boolean realBolt;
        if (phase == CatastrophePhase.PREPARATION && now % 100L == 0L) {
            for (ServerPlayer p : DisasterUtil.playersInArea(level, d)) {
                level.playSound(null, p.blockPosition(), SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.WEATHER, 0.6f, 0.6f);
            }
            return;
        }
        if (phase != CatastrophePhase.ACTIVE && phase != CatastrophePhase.ENDING) {
            return;
        }
        int interval = (int)Math.max(10.0, 60.0 / CatastropheConfig.intensityFactor());
        if (phase == CatastrophePhase.ENDING) {
            interval *= 3;
        }
        if (now % (long)interval != 0L) {
            return;
        }
        int bolts = d.eventData.getInt("bolts");
        if (bolts >= 300) {
            return;
        }
        BlockPos pos = DisasterUtil.randomSurface(level, d, level.getRandom());
        if (pos == null) {
            return;
        }
        LightningBolt bolt = (LightningBolt)EntityType.LIGHTNING_BOLT.create((Level)level);
        if (bolt == null) {
            return;
        }
        bolt.moveTo(Vec3.atBottomCenterOf((Vec3i)pos));
        boolean bl = realBolt = (Boolean)CatastropheConfig.LIGHTNING_FIRES.get() != false && !CatastropheConfig.destructionOff() && (Boolean)CatastropheConfig.DAMAGE_PLAYERS.get() != false && (Boolean)CatastropheConfig.DAMAGE_MOBS.get() != false;
        if (!realBolt) {
            bolt.setVisualOnly(true);
            AABB box = new AABB(pos).inflate(3.0);
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, box, LivingEntity::isAlive)) {
                if (!DisasterUtil.canHurt(e)) continue;
                e.hurt(level.damageSources().lightningBolt(), 5.0f);
            }
        }
        level.addFreshEntity((Entity)bolt);
        d.eventData.putInt("bolts", bolts + 1);
        d.setDirty();
    }

    @Override
    public void onFinish(ServerLevel level, CatastropheSavedData d) {
        DisasterUtil.clearWeather(level);
    }
}

