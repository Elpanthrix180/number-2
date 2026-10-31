package com.panthrix.naturaldisasters.event;

import com.panthrix.naturaldisasters.config.CatastropheConfig;
import com.panthrix.naturaldisasters.core.BlockProtection;
import com.panthrix.naturaldisasters.core.CatastropheEvent;
import com.panthrix.naturaldisasters.core.CatastrophePhase;
import com.panthrix.naturaldisasters.core.CatastropheSavedData;
import com.panthrix.naturaldisasters.event.DisasterUtil;
import it.unimi.dsi.fastutil.longs.LongArrayList;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.material.Fluids;
import net.minecraft.world.phys.Vec3;

public class FloodEvent
extends CatastropheEvent {
    private static final String WATER_KEY = "water";
    private CompoundTag cacheOwner;
    private LongArrayList placed = new LongArrayList();

    private LongArrayList placed(CatastropheSavedData d) {
        if (this.cacheOwner != d.eventData) {
            this.placed = new LongArrayList(d.eventData.getLongArray(WATER_KEY));
            this.cacheOwner = d.eventData;
        }
        return this.placed;
    }

    private void save(CatastropheSavedData d) {
        d.eventData.putLongArray(WATER_KEY, this.placed(d).toLongArray());
        d.setDirty();
    }

    private static int floodRadius() {
        return Math.min((Integer)CatastropheConfig.FLOOD_RADIUS.get(), DisasterUtil.radius());
    }

    @Override
    public void onPhaseStart(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase) {
        switch (phase) {
            case PREPARATION: {
                DisasterUtil.startRain(level, false);
                break;
            }
            case ACTIVE: {
                d.eventData.putInt("base", FloodEvent.findBaseLevel(level, d));
                d.eventData.putDouble("flow", level.getRandom().nextDouble() * Math.PI * 2.0);
                d.eventData.putLong("activeStart", level.getGameTime());
                d.setDirty();
                break;
            }
            case ENDING: 
            case RECOVERY: {
                this.save(d);
                if (phase != CatastrophePhase.RECOVERY) break;
                DisasterUtil.clearWeather(level);
                break;
            }
        }
    }

    private static int findBaseLevel(ServerLevel level, CatastropheSavedData d) {
        int lowest = Integer.MAX_VALUE;
        RandomSource r = level.getRandom();
        int fr = FloodEvent.floodRadius();
        for (int i = 0; i < 24; ++i) {
            int z;
            int x = d.centerX + r.nextInt(2 * fr + 1) - fr;
            if (!level.isLoaded(new BlockPos(x, d.centerY, z = d.centerZ + r.nextInt(2 * fr + 1) - fr))) continue;
            lowest = Math.min(lowest, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z));
        }
        if (lowest == Integer.MAX_VALUE) {
            lowest = d.centerY;
        }
        return Math.max(lowest, level.getSeaLevel());
    }

    @Override
    public void tick(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase, long now) {
        if (phase == CatastrophePhase.RECOVERY) {
            if (((Boolean)CatastropheConfig.FLOOD_TEMPORARY.get()).booleanValue()) {
                this.removeSome(level, d, 40);
            }
            return;
        }
        if (phase != CatastrophePhase.ACTIVE && phase != CatastrophePhase.ENDING) {
            return;
        }
        double f = CatastropheConfig.intensityFactor();
        if (now % 5L == 0L) {
            for (ServerPlayer p : DisasterUtil.playersInArea(level, d)) {
                level.sendParticles((ParticleOptions)ParticleTypes.SPLASH, p.getX(), p.getY() + 0.2, p.getZ(), (int)(20.0 * f), 5.0, 0.2, 5.0, 0.1);
            }
        }
        if (((Boolean)CatastropheConfig.FLOOD_CURRENTS.get()).booleanValue()) {
            FloodEvent.pushInWater(level, d, f);
        }
        if (phase != CatastrophePhase.ACTIVE || CatastropheConfig.destructionOff()) {
            return;
        }
        long activeTicks = (long)((Integer)CatastropheConfig.DURATION_SECONDS.get((Object)d.activeType).get()).intValue() * 20L;
        int maxRise = (Integer)CatastropheConfig.FLOOD_HEIGHT.get();
        long elapsed = now - d.eventData.getLong("activeStart");
        int rise = (int)Math.min((long)maxRise, 1L + elapsed * (long)maxRise / Math.max(1L, activeTicks * 2L / 3L));
        int waterTop = d.eventData.getInt("base") + rise;
        int perTick = (int)Math.max(2.0, 6.0 * f);
        RandomSource r = level.getRandom();
        int fr = FloodEvent.floodRadius();
        for (int i = 0; i < perTick * 3 && perTick > 0; ++i) {
            BlockPos pos;
            int y;
            BlockPos column;
            int z;
            int dz;
            int x = d.centerX + r.nextInt(2 * fr + 1) - fr;
            int dx = x - d.centerX;
            if (dx * dx + (dz = (z = d.centerZ + r.nextInt(2 * fr + 1) - fr) - d.centerZ) * dz > fr * fr || !level.isLoaded(column = new BlockPos(x, d.centerY, z)) || (y = level.getHeight(Heightmap.Types.MOTION_BLOCKING, x, z)) >= waterTop || !level.isEmptyBlock(pos = new BlockPos(x, y, z)) || !BlockProtection.canPlace(level, pos)) continue;
            if (!DisasterUtil.takeBlockBudget(d)) break;
            level.setBlock(pos, Blocks.WATER.defaultBlockState(), 3);
            this.placed(d).add(pos.asLong());
            --perTick;
        }
        if (now % 20L == 0L && this.placed(d).size() != d.eventData.getLongArray(WATER_KEY).length) {
            this.save(d);
        }
    }

    private static void pushInWater(ServerLevel level, CatastropheSavedData d, double f) {
        double flow = d.eventData.getDouble("flow");
        Vec3 push = new Vec3(Math.cos(flow), 0.0, Math.sin(flow)).scale(0.03 * f);
        for (LivingEntity e : DisasterUtil.livingInArea(level, d)) {
            Player p;
            if (!e.isInWater() || e instanceof Player && ((p = (Player)e).isCreative() || p.isSpectator())) continue;
            e.setDeltaMovement(e.getDeltaMovement().add(push));
            e.hurtMarked = true;
        }
    }

    private void removeSome(ServerLevel level, CatastropheSavedData d, int max) {
        int removed;
        LongArrayList list = this.placed(d);
        for (removed = 0; !list.isEmpty() && removed < max; ++removed) {
            BlockPos pos = BlockPos.of((long)list.removeLong(list.size() - 1));
            FloodEvent.removeWater(level, d, pos);
        }
        if (removed > 0) {
            this.save(d);
        }
    }

    private static void removeWater(ServerLevel level, CatastropheSavedData d, BlockPos pos) {
        if (!level.isLoaded(pos)) {
            return;
        }
        FloodEvent.removeIfFloodSource(level, pos);
        int base = d.eventData.getInt("base");
        for (Direction dir : new Direction[]{Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST, Direction.UP}) {
            BlockPos n = pos.relative(dir);
            if (n.getY() < base || !level.isLoaded(n)) continue;
            FloodEvent.removeIfFloodSource(level, n);
        }
    }

    private static void removeIfFloodSource(ServerLevel level, BlockPos pos) {
        FluidState fluid = level.getFluidState(pos);
        if (fluid.is((Fluid)Fluids.WATER) && fluid.isSource() && level.getBlockState(pos).is(Blocks.WATER)) {
            level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
        }
    }

    @Override
    public void onFinish(ServerLevel level, CatastropheSavedData d) {
        DisasterUtil.clearWeather(level);
        if (((Boolean)CatastropheConfig.FLOOD_TEMPORARY.get()).booleanValue()) {
            this.removeSome(level, d, Integer.MAX_VALUE);
        }
        this.cacheOwner = null;
    }
}

