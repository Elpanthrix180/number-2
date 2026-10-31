package com.panthrix.naturaldisasters.event;

import com.panthrix.naturaldisasters.config.CatastropheConfig;
import com.panthrix.naturaldisasters.core.BlockProtection;
import com.panthrix.naturaldisasters.core.CatastropheEvent;
import com.panthrix.naturaldisasters.core.CatastrophePhase;
import com.panthrix.naturaldisasters.core.CatastropheSavedData;
import com.panthrix.naturaldisasters.event.DisasterUtil;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.item.FallingBlockEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

public class TornadoEvent
extends CatastropheEvent {
    private static final int FUNNEL_HEIGHT = 28;

    @Override
    public void onPhaseStart(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase) {
        switch (phase) {
            case WARNING: {
                RandomSource r = level.getRandom();
                double angle = r.nextDouble() * Math.PI * 2.0;
                double dist = (double)DisasterUtil.radius() * 0.8;
                d.eventData.putDouble("tx", (double)d.centerX + Math.cos(angle) * dist);
                d.eventData.putDouble("tz", (double)d.centerZ + Math.sin(angle) * dist);
                d.eventData.putDouble("dir", angle + Math.PI + (r.nextDouble() - 0.5));
                d.setDirty();
                break;
            }
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
        double tz;
        if (phase != CatastrophePhase.PREPARATION && phase != CatastrophePhase.ACTIVE && phase != CatastrophePhase.ENDING) {
            return;
        }
        double f = CatastropheConfig.intensityFactor();
        double size = phase == CatastrophePhase.ACTIVE ? 1.0 : 0.4;
        double tx = d.eventData.getDouble("tx");
        BlockPos column = BlockPos.containing((double)tx, (double)d.centerY, (double)(tz = d.eventData.getDouble("tz")));
        if (!level.isLoaded(column)) {
            return;
        }
        int baseY = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, column.getX(), column.getZ());
        if (phase != CatastrophePhase.PREPARATION) {
            TornadoEvent.move(level, d, tx, tz, now);
        }
        if (now % 2L == 0L) {
            TornadoEvent.drawFunnel(level, tx, baseY, tz, now, size * (0.7 + 0.3 * f));
        }
        if (now % 20L == 0L) {
            level.playSound(null, column.atY(baseY), SoundEvents.ELYTRA_FLYING, SoundSource.WEATHER, (float)(3.0 * size), 0.5f);
        }
        if (phase == CatastrophePhase.PREPARATION) {
            return;
        }
        TornadoEvent.pullEntities(level, tx, baseY, tz, now, f * size);
        if (!CatastropheConfig.destructionOff() && ((Boolean)CatastropheConfig.TORNADO_LIFTS_BLOCKS.get()).booleanValue()) {
            int interval;
            int n = interval = CatastropheConfig.DESTRUCTION.get() == CatastropheConfig.Destruction.INTENSE ? 3 : 8;
            if (phase == CatastrophePhase.ENDING) {
                interval *= 2;
            }
            if (now % (long)interval == 0L) {
                TornadoEvent.liftBlock(level, d, tx, tz, f);
            }
        }
    }

    private static void move(ServerLevel level, CatastropheSavedData d, double tx, double tz, long now) {
        double nz;
        double dz;
        double dx;
        RandomSource r = level.getRandom();
        double dir = d.eventData.getDouble("dir");
        if (now % 100L == 0L) {
            dir += (r.nextDouble() - 0.5) * Math.PI / 2.0;
        }
        if ((dx = (double)d.centerX - tx) * dx + (dz = (double)d.centerZ - tz) * dz > Math.pow((double)DisasterUtil.radius() * 1.5, 2.0)) {
            dir = Math.atan2(dz, dx);
        }
        double step = (Double)CatastropheConfig.TORNADO_SPEED.get() / 20.0;
        double nx = tx + Math.cos(dir) * step;
        if (!level.isLoaded(BlockPos.containing((double)nx, (double)d.centerY, (double)(nz = tz + Math.sin(dir) * step)))) {
            dir += Math.PI;
            nx = tx;
            nz = tz;
        }
        d.eventData.putDouble("tx", nx);
        d.eventData.putDouble("tz", nz);
        d.eventData.putDouble("dir", dir);
        d.setDirty();
    }

    private static void drawFunnel(ServerLevel level, double x, int baseY, double z, long now, double size) {
        double spin = (double)now * 0.35;
        for (int h = 0; h < 28; h += 2) {
            double radius = (0.6 + (double)h * 0.22) * size;
            for (int arm = 0; arm < 3; ++arm) {
                double a = spin + (double)arm * 2.0943951023931953 + (double)h * 0.3;
                level.sendParticles((ParticleOptions)ParticleTypes.CLOUD, x + Math.cos(a) * radius, (double)(baseY + h), z + Math.sin(a) * radius, 1, 0.1, 0.1, 0.1, 0.0);
            }
        }
        BlockState ground = level.getBlockState(BlockPos.containing((double)x, (double)(baseY - 1), (double)z));
        if (!ground.isAir()) {
            level.sendParticles((ParticleOptions)new BlockParticleOption(ParticleTypes.BLOCK, ground), x, (double)baseY + 0.5, z, 8, 1.5 * size, 0.3, 1.5 * size, 0.2);
        }
        level.sendParticles((ParticleOptions)ParticleTypes.LARGE_SMOKE, x, (double)(baseY + 28), z, 3, 3.0 * size, 0.5, 3.0 * size, 0.01);
    }

    private static void pullEntities(ServerLevel level, double tx, int baseY, double tz, long now, double strength) {
        int pull = (Integer)CatastropheConfig.TORNADO_PULL_RADIUS.get();
        AABB box = new AABB(tx - (double)pull, (double)(baseY - 4), tz - (double)pull, tx + (double)pull, (double)(baseY + 28), tz + (double)pull);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, box, LivingEntity::isAlive)) {
            double dz;
            double dx;
            double dist;
            Player p;
            if (e instanceof Player && ((p = (Player)e).isCreative() || p.isSpectator()) || (dist = Math.max(0.5, Math.sqrt((dx = tx - e.getX()) * dx + (dz = tz - e.getZ()) * dz))) > (double)pull) continue;
            double closeness = 1.0 - dist / (double)pull;
            Vec3 inward = new Vec3(dx / dist, 0.0, dz / dist).scale(0.06 * strength * closeness);
            Vec3 around = new Vec3(-dz / dist, 0.0, dx / dist).scale(0.1 * strength * closeness);
            double up = DisasterUtil.canHurt(e) && dist < 3.0 && e.getY() < (double)(baseY + 18) ? 0.12 * strength : 0.0;
            Vec3 v = e.getDeltaMovement().add(inward).add(around).add(0.0, up, 0.0);
            e.setDeltaMovement(v.x, Mth.clamp((double)v.y, (double)-1.0, (double)0.7), v.z);
            e.hurtMarked = true;
            if (now % 20L != 0L || !(dist < 3.0) || !DisasterUtil.canHurt(e)) continue;
            e.hurt(level.damageSources().generic(), (float)Math.max(1.0, 2.0 * strength));
        }
    }

    private static void liftBlock(ServerLevel level, CatastropheSavedData d, double tx, double tz, double f) {
        int z;
        RandomSource r = level.getRandom();
        double reach = 2.0 + 2.0 * f;
        int x = Mth.floor((double)(tx + (r.nextDouble() * 2.0 - 1.0) * reach));
        BlockPos top = new BlockPos(x, d.centerY, z = Mth.floor((double)(tz + (r.nextDouble() * 2.0 - 1.0) * reach)));
        if (!level.isLoaded(top)) {
            return;
        }
        BlockPos pos = level.getHeightmapPos(Heightmap.Types.WORLD_SURFACE, top).below();
        BlockState state = level.getBlockState(pos);
        if (state.isAir() || !state.getFluidState().isEmpty() || !TornadoEvent.isLiftable(state)) {
            return;
        }
        if (!BlockProtection.canModify(level, pos, state) || !DisasterUtil.takeBlockBudget(d)) {
            return;
        }
        if (state.canBeReplaced()) {
            level.destroyBlock(pos, false);
            return;
        }
        FallingBlockEntity falling = FallingBlockEntity.fall((Level)level, (BlockPos)pos, (BlockState)state);
        double a = r.nextDouble() * Math.PI * 2.0;
        falling.setDeltaMovement(Math.cos(a) * 0.5, 0.8 + r.nextDouble() * 0.6, Math.sin(a) * 0.5);
        falling.hurtMarked = true;
    }

    private static boolean isLiftable(BlockState s) {
        if (s.canBeReplaced()) {
            return true;
        }
        if (s.is(BlockTags.LEAVES) || s.is(BlockTags.SAND) || s.is(Blocks.GRAVEL) || s.is(Blocks.DIRT) || s.is(Blocks.GRASS_BLOCK) || s.is(Blocks.COARSE_DIRT) || s.is(Blocks.PODZOL) || s.is(Blocks.MYCELIUM)) {
            return true;
        }
        return s.is(BlockTags.LOGS) && (Boolean)CatastropheConfig.TORNADO_UPROOTS_TREES.get() != false && CatastropheConfig.DESTRUCTION.get() == CatastropheConfig.Destruction.INTENSE;
    }

    @Override
    public void onFinish(ServerLevel level, CatastropheSavedData d) {
        DisasterUtil.clearWeather(level);
    }
}

