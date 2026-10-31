package com.panthrix.naturaldisasters.event;

import com.panthrix.naturaldisasters.config.CatastropheConfig;
import com.panthrix.naturaldisasters.core.BlockProtection;
import com.panthrix.naturaldisasters.core.CatastropheEvent;
import com.panthrix.naturaldisasters.core.CatastrophePhase;
import com.panthrix.naturaldisasters.core.CatastropheSavedData;
import com.panthrix.naturaldisasters.event.DisasterUtil;
import com.panthrix.naturaldisasters.network.ModNetwork;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.item.FallingBlockEntity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

public class BlackHoleEvent
extends CatastropheEvent {
    @Override
    public void chooseLocation(ServerLevel level, CatastropheSavedData d) {
        RandomSource r = level.getRandom();
        double a = r.nextDouble() * Math.PI * 2.0;
        d.centerX += (int)(Math.cos(a) * 20.0);
        d.centerZ += (int)(Math.sin(a) * 20.0);
        if (level.isLoaded(new BlockPos(d.centerX, d.centerY, d.centerZ))) {
            d.centerY = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, d.centerX, d.centerZ);
        }
        d.centerY += ((Integer)CatastropheConfig.BLACK_HOLE_HEIGHT.get()).intValue();
        d.setDirty();
    }

    @Override
    public void onPhaseStart(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase) {
        if (phase == CatastrophePhase.ACTIVE) {
            d.eventData.putLong("activeStart", level.getGameTime());
            d.setDirty();
        }
        if (phase == CatastrophePhase.RECOVERY) {
            BlackHoleEvent.collapse(level, d);
        }
    }

    private static double growth(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase) {
        if (phase == CatastrophePhase.PREPARATION) {
            return 0.05;
        }
        long activeTicks = Math.max(1L, (long)((Integer)CatastropheConfig.DURATION_SECONDS.get((Object)d.activeType).get()).intValue() * 20L);
        double g = (double)(level.getGameTime() - d.eventData.getLong("activeStart")) / (double)activeTicks;
        return phase == CatastrophePhase.ENDING ? 1.0 : Math.max(0.05, Math.min(1.0, g * 1.15));
    }

    @Override
    public void tick(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase, long now) {
        if (phase != CatastrophePhase.PREPARATION && phase != CatastrophePhase.ACTIVE && phase != CatastrophePhase.ENDING) {
            return;
        }
        double cx = (double)d.centerX + 0.5;
        double cy = (double)d.centerY + 0.5;
        double cz = (double)d.centerZ + 0.5;
        if (!level.isLoaded(BlockPos.containing((double)cx, (double)cy, (double)cz))) {
            return;
        }
        double f = CatastropheConfig.intensityFactor();
        double g = BlackHoleEvent.growth(level, d, phase);
        int maxR = (Integer)CatastropheConfig.BLACK_HOLE_MAX_RADIUS.get();
        double eatRadius = 1.5 + ((double)maxR - 1.5) * g;
        double coreW = 0.6 + eatRadius * 0.25;
        double coreH = coreW * 3.0;
        if (now % 2L == 0L) {
            BlackHoleEvent.draw(level, cx, cy, cz, now, coreW, coreH, eatRadius);
        }
        if (now % 40L == 0L) {
            BlockPos at = BlockPos.containing((double)cx, (double)cy, (double)cz);
            float vol = (float)(1.0 + 3.0 * g);
            level.playSound(null, at, SoundEvents.PORTAL_TRAVEL, SoundSource.HOSTILE, vol, 0.4f);
            level.playSound(null, at, SoundEvents.WARDEN_HEARTBEAT, SoundSource.HOSTILE, vol, 0.5f);
            if (((Boolean)CatastropheConfig.QUAKE_CAMERA_SHAKE.get()).booleanValue()) {
                for (ServerPlayer p : level.players()) {
                    if (!(p.distanceToSqr(cx, cy, cz) < Math.pow(BlackHoleEvent.pullRadius(eatRadius) * 2.0, 2.0))) continue;
                    ModNetwork.sendShake(p, (float)((0.3 + 1.2 * g) * f), 45);
                }
            }
        }
        if (phase == CatastrophePhase.PREPARATION) {
            return;
        }
        BlackHoleEvent.pull(level, cx, cy, cz, BlackHoleEvent.pullRadius(eatRadius), (0.4 + 0.9 * g) * f, eatRadius, now);
        if (CatastropheConfig.destructionOff()) {
            return;
        }
        boolean intense = CatastropheConfig.DESTRUCTION.get() == CatastropheConfig.Destruction.INTENSE;
        int perTick = (int)Math.max(2.0, (double)(intense ? 70 : 35) * f * (0.3 + g));
        if (phase == CatastrophePhase.ENDING) {
            perTick /= 2;
        }
        RandomSource r = level.getRandom();
        for (int i = 0; i < perTick && BlackHoleEvent.absorbBlock(level, d, cx, cy, cz, eatRadius, coreH, r, intense); ++i) {
        }
    }

    private static double pullRadius(double eatRadius) {
        return (double)((Integer)CatastropheConfig.BLACK_HOLE_PULL_RADIUS.get()).intValue() + eatRadius * 1.5;
    }

    private static void draw(ServerLevel level, double x, double y, double z, long now, double w, double h, double eat) {
        int layers = Math.max(3, (int)(h * 1.5));
        for (int k = 0; k < layers; ++k) {
            double ly = y - h + 2.0 * h * (double)k / ((double)layers - 1.0);
            double t = (ly - y) / h;
            double lw = w * Math.sqrt(Math.max(0.05, 1.0 - t * t));
            level.sendParticles((ParticleOptions)ParticleTypes.SQUID_INK, x, ly, z, 3, lw * 0.5, 0.2, lw * 0.5, 0.0);
        }
        level.sendParticles((ParticleOptions)ParticleTypes.REVERSE_PORTAL, x, y, z, 15, w, h, w, 0.05);
        double spin = (double)now * 0.22;
        double tilt = (double)now * 0.01;
        double ax = Math.cos(tilt);
        double az = Math.sin(tilt);
        int points = 24;
        for (int k = 0; k < points; ++k) {
            double a = spin + (double)k * (Math.PI * 2 / (double)points);
            double rad = w * 1.8 + 1.0 + (double)(k % 3) * 0.6;
            double hx = Math.cos(a) * rad;
            double vy = Math.sin(a) * rad * 1.4;
            level.sendParticles((ParticleOptions)(k % 3 == 0 ? ParticleTypes.FLAME : ParticleTypes.END_ROD), x + hx * ax, y + vy, z + hx * az, 1, 0.0, 0.0, 0.0, 0.0);
        }
        level.sendParticles((ParticleOptions)ParticleTypes.END_ROD, x, y + h + 1.0, z, 4, 0.2, 2.5, 0.2, 0.15);
        level.sendParticles((ParticleOptions)ParticleTypes.END_ROD, x, y - h - 1.0, z, 4, 0.2, 2.5, 0.2, 0.15);
        level.sendParticles((ParticleOptions)ParticleTypes.PORTAL, x, y, z, 20, eat, eat * 0.6, eat, 0.6);
    }

    private static void pull(ServerLevel level, double cx, double cy, double cz, double radius, double strength, double eatRadius, long now) {
        AABB box = new AABB(cx - radius, cy - radius, cz - radius, cx + radius, cy + radius, cz + radius);
        double coreR = 1.0 + eatRadius * 0.15;
        for (Entity e : level.getEntities((Entity)null, box, en -> en instanceof LivingEntity || en instanceof ItemEntity || en instanceof FallingBlockEntity)) {
            Vec3 toCenter;
            double dist;
            Player p;
            if (e instanceof Player && ((p = (Player)e).isCreative() || p.isSpectator()) || (dist = (toCenter = new Vec3(cx - e.getX(), cy - e.getY(), cz - e.getZ())).length()) > radius || dist < 0.01) continue;
            double closeness = 1.0 - dist / radius;
            Vec3 dir = toCenter.normalize();
            Vec3 around = new Vec3(-dir.z, 0.0, dir.x).scale(0.05 * strength * closeness);
            Vec3 v = e.getDeltaMovement().add(dir.scale(0.04 + 0.14 * strength * closeness)).add(around);
            if (v.length() > 1.4) {
                v = v.normalize().scale(1.4);
            }
            e.setDeltaMovement(v);
            e.hurtMarked = true;
            e.fallDistance = 0.0f;
            if (!(dist < coreR)) continue;
            if (e instanceof LivingEntity) {
                LivingEntity le = (LivingEntity)e;
                if (now % 10L == 0L && DisasterUtil.canHurt(le)) {
                    le.hurt(level.damageSources().magic(), (float)(5.0 * strength));
                    continue;
                }
            }
            if (e instanceof ItemEntity) {
                ItemEntity item = (ItemEntity)e;
                if (((Boolean)CatastropheConfig.BLACK_HOLE_CONSUMES_ITEMS.get()).booleanValue()) {
                    level.sendParticles((ParticleOptions)ParticleTypes.REVERSE_PORTAL, item.getX(), item.getY(), item.getZ(), 6, 0.1, 0.1, 0.1, 0.1);
                    item.discard();
                    continue;
                }
            }
            if (!(e instanceof FallingBlockEntity)) continue;
            FallingBlockEntity fb = (FallingBlockEntity)e;
            fb.discard();
        }
    }

    private static boolean absorbBlock(ServerLevel level, CatastropheSavedData d, double cx, double cy, double cz, double radius, double coreH, RandomSource r, boolean intense) {
        double u = r.nextDouble() * 2.0 - 1.0;
        double th = r.nextDouble() * Math.PI * 2.0;
        double s = Math.sqrt(1.0 - u * u);
        double dist = radius * (0.55 + 0.45 * Math.cbrt(r.nextDouble()));
        double vertical = 1.0 + Math.min(1.0, coreH / Math.max(1.0, radius));
        BlockPos pos = BlockPos.containing((double)(cx + s * Math.cos(th) * dist), (double)(cy + u * dist * vertical), (double)(cz + s * Math.sin(th) * dist));
        if (!level.isLoaded(pos)) {
            return true;
        }
        BlockState st = level.getBlockState(pos);
        if (st.isAir()) {
            return true;
        }
        if (!st.getFluidState().isEmpty()) {
            if (!BlockProtection.canPlace(level, pos)) {
                return true;
            }
            if (!DisasterUtil.takeBlockBudget(d, (Integer)CatastropheConfig.BLACK_HOLE_MAX_BLOCKS.get())) {
                return false;
            }
            level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
            return true;
        }
        if (!BlockProtection.canModify(level, pos, st)) {
            return true;
        }
        if (!DisasterUtil.takeBlockBudget(d, (Integer)CatastropheConfig.BLACK_HOLE_MAX_BLOCKS.get())) {
            return false;
        }
        if (intense && r.nextInt(3) == 0) {
            FallingBlockEntity fb = FallingBlockEntity.fall((Level)level, (BlockPos)pos, (BlockState)st);
            fb.dropItem = false;
            fb.setNoGravity(true);
            fb.setDeltaMovement(new Vec3(cx - fb.getX(), cy - fb.getY(), cz - fb.getZ()).normalize().scale(0.5));
            fb.hurtMarked = true;
        } else {
            level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
            Vec3 toC = new Vec3(cx - (double)pos.getX(), cy - (double)pos.getY(), cz - (double)pos.getZ()).normalize();
            level.sendParticles((ParticleOptions)new BlockParticleOption(ParticleTypes.BLOCK, st), (double)pos.getX() + 0.5, (double)pos.getY() + 0.5, (double)pos.getZ() + 0.5, 6, toC.x, toC.y, toC.z, 0.4);
        }
        return true;
    }

    private static void collapse(ServerLevel level, CatastropheSavedData d) {
        double cx = (double)d.centerX + 0.5;
        double cy = (double)d.centerY + 0.5;
        double cz = (double)d.centerZ + 0.5;
        if (!level.isLoaded(BlockPos.containing((double)cx, (double)cy, (double)cz))) {
            return;
        }
        level.sendParticles((ParticleOptions)ParticleTypes.FLASH, cx, cy, cz, 1, 0.0, 0.0, 0.0, 0.0);
        level.sendParticles((ParticleOptions)ParticleTypes.REVERSE_PORTAL, cx, cy, cz, 200, 3.0, 6.0, 3.0, 0.8);
        level.sendParticles((ParticleOptions)ParticleTypes.END_ROD, cx, cy, cz, 80, 1.0, 4.0, 1.0, 0.5);
        level.playSound(null, BlockPos.containing((double)cx, (double)cy, (double)cz), SoundEvents.END_PORTAL_SPAWN, SoundSource.HOSTILE, 3.0f, 1.2f);
        double radius = BlackHoleEvent.pullRadius(((Integer)CatastropheConfig.BLACK_HOLE_MAX_RADIUS.get()).intValue());
        AABB box = new AABB(cx - radius, cy - radius, cz - radius, cx + radius, cy + radius, cz + radius);
        for (FallingBlockEntity fb : level.getEntitiesOfClass(FallingBlockEntity.class, box, Entity::isNoGravity)) {
            fb.discard();
        }
    }

    @Override
    public void onFinish(ServerLevel level, CatastropheSavedData d) {
        BlackHoleEvent.collapse(level, d);
    }
}

