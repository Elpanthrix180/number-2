package com.panthrix.naturaldisasters.event;

import com.panthrix.naturaldisasters.config.CatastropheConfig;
import com.panthrix.naturaldisasters.core.BlockProtection;
import com.panthrix.naturaldisasters.core.CatastropheEvent;
import com.panthrix.naturaldisasters.core.CatastrophePhase;
import com.panthrix.naturaldisasters.core.CatastropheSavedData;
import com.panthrix.naturaldisasters.core.VolcanoRegistry;
import com.panthrix.naturaldisasters.event.DisasterUtil;
import com.panthrix.naturaldisasters.network.ModNetwork;
import com.panthrix.naturaldisasters.worldgen.VolcanoBuilder;
import java.util.Arrays;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.item.FallingBlockEntity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;

public class VolcanoEvent
extends CatastropheEvent {
    private static final String LAVA_KEY = "lava";

    @Override
    public void chooseLocation(ServerLevel level, CatastropheSavedData d) {
        BlockPos crater = VolcanoRegistry.get(level).nearest(d.centerX, d.centerZ, (Integer)CatastropheConfig.VOLCANO_SEARCH_RADIUS.get());
        if (crater != null) {
            d.centerX = crater.getX();
            d.centerY = crater.getY();
            d.centerZ = crater.getZ();
            d.eventData.putBoolean("hasVolcano", true);
        } else {
            RandomSource r = level.getRandom();
            double a = r.nextDouble() * Math.PI * 2.0;
            d.centerX += (int)(Math.cos(a) * 28.0);
            d.centerZ += (int)(Math.sin(a) * 28.0);
            d.eventData.putBoolean("hasVolcano", false);
        }
        d.setDirty();
    }

    @Override
    public void onPhaseStart(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase) {
        BlockPos crater;
        BlockPos center;
        if (phase == CatastrophePhase.PREPARATION && !d.eventData.getBoolean("hasVolcano") && !CatastropheConfig.destructionOff() && ((Boolean)CatastropheConfig.VOLCANO_CREATE_IF_NONE.get()).booleanValue() && level.isLoaded(center = new BlockPos(d.centerX, d.centerY, d.centerZ)) && (crater = VolcanoBuilder.build((WorldGenLevel)level, center, level.getRandom(), true)) != null) {
            d.centerY = crater.getY();
            d.eventData.putBoolean("hasVolcano", true);
            VolcanoRegistry.get(level).add(crater);
            d.setDirty();
        }
        if (phase == CatastrophePhase.RECOVERY) {
            VolcanoEvent.removeLava(level, d);
        }
    }

    @Override
    public void tick(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase, long now) {
        if (phase != CatastrophePhase.PREPARATION && phase != CatastrophePhase.ACTIVE && phase != CatastrophePhase.ENDING) {
            return;
        }
        if (!level.isLoaded(new BlockPos(d.centerX, d.centerY, d.centerZ))) {
            return;
        }
        double f = CatastropheConfig.intensityFactor();
        boolean active = phase == CatastrophePhase.ACTIVE;
        double x = (double)d.centerX + 0.5;
        double y = d.centerY;
        double z = (double)d.centerZ + 0.5;
        RandomSource r = level.getRandom();
        if (now % 3L == 0L) {
            level.sendParticles((ParticleOptions)ParticleTypes.CAMPFIRE_SIGNAL_SMOKE, x, y + 1.0, z, active ? 6 : 2, 1.5, 0.5, 1.5, 0.02);
            if (active) {
                level.sendParticles((ParticleOptions)ParticleTypes.LAVA, x, y, z, (int)(10.0 * f), 1.5, 0.5, 1.5, 0.0);
                level.sendParticles((ParticleOptions)ParticleTypes.FLAME, x, y + 1.0, z, (int)(8.0 * f), 1.0, 2.0, 1.0, 0.08);
                level.sendParticles((ParticleOptions)ParticleTypes.LARGE_SMOKE, x, y + 4.0, z, 10, 3.0, 3.0, 3.0, 0.05);
            }
        }
        if (now % 6L == 0L) {
            for (ServerPlayer p : DisasterUtil.playersInArea(level, d)) {
                level.sendParticles((ParticleOptions)ParticleTypes.ASH, p.getX(), p.getY() + 3.0, p.getZ(), active ? 40 : 10, 8.0, 3.0, 8.0, 0.0);
                if (!active) continue;
                level.sendParticles((ParticleOptions)ParticleTypes.WHITE_ASH, p.getX(), p.getY() + 3.0, p.getZ(), 15, 8.0, 3.0, 8.0, 0.0);
            }
        }
        if (now % 20L == 0L) {
            BlockPos at = BlockPos.containing((double)x, (double)y, (double)z);
            level.playSound(null, at, SoundEvents.LAVA_EXTINGUISH, SoundSource.BLOCKS, 3.0f, 0.6f);
            if (active) {
                level.playSound(null, at, SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.BLOCKS, 1.5f, 0.3f);
            }
            if (((Boolean)CatastropheConfig.QUAKE_CAMERA_SHAKE.get()).booleanValue()) {
                for (ServerPlayer p : DisasterUtil.playersInArea(level, d)) {
                    ModNetwork.sendShake(p, active ? (float)(0.6 * f) : 0.2f, 25);
                }
            }
        }
        if (phase == CatastrophePhase.PREPARATION) {
            return;
        }
        if (now % 20L == 0L) {
            VolcanoEvent.heatDamage(level, d, x, y, z);
        }
        if (CatastropheConfig.destructionOff()) {
            return;
        }
        int bombInterval = (int)Math.max(5.0, 20.0 / f);
        if (phase == CatastrophePhase.ENDING) {
            bombInterval *= 3;
        }
        if (((Boolean)CatastropheConfig.VOLCANO_BOMBS.get()).booleanValue() && now % (long)bombInterval == 0L) {
            VolcanoEvent.launchBomb(level, d, x, y, z, r);
        }
        if (active && ((Boolean)CatastropheConfig.VOLCANO_LAVA_FLOWS.get()).booleanValue() && d.eventData.getBoolean("hasVolcano") && now % 40L == 0L) {
            VolcanoEvent.overflowLava(level, d, r);
        }
    }

    private static void heatDamage(ServerLevel level, CatastropheSavedData d, double x, double y, double z) {
        int danger = (Integer)CatastropheConfig.VOLCANO_DANGER_RADIUS.get();
        AABB box = new AABB(x - (double)danger, y - (double)danger, z - (double)danger, x + (double)danger, y + (double)danger, z + (double)danger);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, box, LivingEntity::isAlive)) {
            double dist;
            if (!DisasterUtil.canHurt(e) || e.fireImmune() || (dist = Math.sqrt(e.distanceToSqr(x, y, z))) > (double)danger) continue;
            if (dist < (double)danger * 0.5) {
                e.setSecondsOnFire(3);
            }
            e.hurt(level.damageSources().hotFloor(), 1.0f);
        }
    }

    private static void launchBomb(ServerLevel level, CatastropheSavedData d, double x, double y, double z, RandomSource r) {
        if (!DisasterUtil.takeBlockBudget(d)) {
            return;
        }
        BlockPos start = BlockPos.containing((double)x, (double)(y + 2.0), (double)z);
        if (!level.isEmptyBlock(start)) {
            return;
        }
        BlockState rock = r.nextInt(3) == 0 ? Blocks.MAGMA_BLOCK.defaultBlockState() : Blocks.BLACKSTONE.defaultBlockState();
        level.setBlock(start, rock, 3);
        FallingBlockEntity bomb = FallingBlockEntity.fall((Level)level, (BlockPos)start, (BlockState)rock);
        double a = r.nextDouble() * Math.PI * 2.0;
        double speed = 0.4 + r.nextDouble() * 0.6;
        bomb.setDeltaMovement(Math.cos(a) * speed, 0.9 + r.nextDouble() * 0.6, Math.sin(a) * speed);
        bomb.hurtMarked = true;
        bomb.dropItem = false;
        if (((Boolean)CatastropheConfig.DAMAGE_PLAYERS.get()).booleanValue() || ((Boolean)CatastropheConfig.DAMAGE_MOBS.get()).booleanValue()) {
            bomb.setHurtsEntities(2.0f, 20);
        }
    }

    private static void overflowLava(ServerLevel level, CatastropheSavedData d, RandomSource r) {
        int lz;
        long[] old = d.eventData.getLongArray(LAVA_KEY);
        if ((double)old.length >= 8.0 * CatastropheConfig.intensityFactor()) {
            return;
        }
        double a = r.nextDouble() * Math.PI * 2.0;
        int lx = d.centerX + (int)Math.round(Math.cos(a) * 4.0);
        BlockPos pos = new BlockPos(lx, level.getHeight(Heightmap.Types.MOTION_BLOCKING, lx, lz = d.centerZ + (int)Math.round(Math.sin(a) * 4.0)), lz);
        if (!(level.isLoaded(pos) && level.isEmptyBlock(pos) && BlockProtection.canPlace(level, pos))) {
            return;
        }
        if (!DisasterUtil.takeBlockBudget(d)) {
            return;
        }
        level.setBlock(pos, Blocks.LAVA.defaultBlockState(), 3);
        long[] grown = Arrays.copyOf(old, old.length + 1);
        grown[old.length] = pos.asLong();
        d.eventData.putLongArray(LAVA_KEY, grown);
        d.setDirty();
    }

    private static void removeLava(ServerLevel level, CatastropheSavedData d) {
        if (!((Boolean)CatastropheConfig.VOLCANO_LAVA_TEMPORARY.get()).booleanValue()) {
            return;
        }
        for (long l : d.eventData.getLongArray(LAVA_KEY)) {
            BlockPos pos = BlockPos.of((long)l);
            if (!level.isLoaded(pos) || !level.getBlockState(pos).is(Blocks.LAVA)) continue;
            level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
        }
        d.eventData.remove(LAVA_KEY);
        d.setDirty();
    }

    @Override
    public void onFinish(ServerLevel level, CatastropheSavedData d) {
        VolcanoEvent.removeLava(level, d);
    }
}

