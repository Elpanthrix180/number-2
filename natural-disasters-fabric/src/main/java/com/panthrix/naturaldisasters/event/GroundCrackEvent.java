package com.panthrix.naturaldisasters.event;

import com.panthrix.naturaldisasters.config.CatastropheConfig;
import com.panthrix.naturaldisasters.core.BlockProtection;
import com.panthrix.naturaldisasters.core.CatastropheEvent;
import com.panthrix.naturaldisasters.core.CatastrophePhase;
import com.panthrix.naturaldisasters.core.CatastropheSavedData;
import com.panthrix.naturaldisasters.event.DisasterUtil;
import com.panthrix.naturaldisasters.network.ModNetwork;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;

public class GroundCrackEvent
extends CatastropheEvent {
    private static final String KEY = "cracks";
    private static final int MAX_CRACKS = 30;

    @Override
    public void onPhaseStart(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase) {
        if (phase != CatastrophePhase.ACTIVE) {
            return;
        }
        RandomSource r = level.getRandom();
        ListTag cracks = new ListTag();
        int n = (Integer)CatastropheConfig.CRACKS_COUNT.get();
        double base = r.nextDouble() * Math.PI * 2.0;
        for (int i = 0; i < n; ++i) {
            double ang = base + (double)i * (Math.PI * 2 / (double)n) + (r.nextDouble() - 0.5) * 0.6;
            cracks.add((Object)GroundCrackEvent.newCrack((double)d.centerX + 0.5, (double)d.centerZ + 0.5, ang, (Integer)CatastropheConfig.CRACKS_LENGTH.get(), ((Integer)CatastropheConfig.CRACKS_WIDTH.get()).intValue(), (Integer)CatastropheConfig.CRACKS_DEPTH.get(), 0));
        }
        d.eventData.put(KEY, (Tag)cracks);
        d.setDirty();
    }

    private static CompoundTag newCrack(double x, double z, double ang, int len, double width, int depth, int gen) {
        CompoundTag c = new CompoundTag();
        c.putDouble("x", x);
        c.putDouble("z", z);
        c.putDouble("ang", ang);
        c.putInt("len", Math.max(4, len));
        c.putDouble("width", Math.max(1.0, width));
        c.putInt("depth", Math.max(2, depth));
        c.putInt("gen", gen);
        c.putInt("t", 0);
        return c;
    }

    @Override
    public void tick(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase, long now) {
        if (phase == CatastrophePhase.PREPARATION) {
            if (now % 10L == 0L) {
                BlockPos at = new BlockPos(d.centerX, d.centerY, d.centerZ);
                level.playSound(null, at, SoundEvents.GRAVEL_BREAK, SoundSource.BLOCKS, 1.5f, 0.4f);
                GroundCrackEvent.surfaceDust(level, (double)d.centerX + 0.5, (double)d.centerZ + 0.5, 8, 3.0);
            }
            return;
        }
        if (phase != CatastrophePhase.ACTIVE && phase != CatastrophePhase.ENDING) {
            return;
        }
        ListTag cracks = d.eventData.getList(KEY, 10);
        if (cracks.isEmpty()) {
            return;
        }
        int interval = Math.max(1, 20 / (Integer)CatastropheConfig.CRACKS_SPEED.get());
        if (phase == CatastrophePhase.ENDING) {
            interval *= 2;
        }
        if (now % 20L == 0L && ((Boolean)CatastropheConfig.QUAKE_CAMERA_SHAKE.get()).booleanValue()) {
            for (ServerPlayer p : DisasterUtil.playersInArea(level, d)) {
                ModNetwork.sendShake(p, 0.35f, 25);
            }
        }
        if (now % (long)interval != 0L) {
            GroundCrackEvent.steam(level, cracks, now);
            return;
        }
        boolean destroy = !CatastropheConfig.destructionOff();
        RandomSource r = level.getRandom();
        int size = cracks.size();
        for (int i = 0; i < size; ++i) {
            CompoundTag c = cracks.getCompound(i);
            int t = c.getInt("t");
            if (t > c.getInt("len")) continue;
            GroundCrackEvent.step(level, d, c, destroy, r);
            if (!((Boolean)CatastropheConfig.CRACKS_BRANCHES.get()).booleanValue() || c.getInt("gen") >= 2 || cracks.size() >= 30 || t <= 3 || r.nextInt(14) != 0) continue;
            double side = r.nextBoolean() ? 1.0 : -1.0;
            double ang = c.getDouble("ang") + side * (0.5 + r.nextDouble() * 0.7);
            int left = c.getInt("len") - t;
            cracks.add((Object)GroundCrackEvent.newCrack(c.getDouble("x"), c.getDouble("z"), ang, (int)((double)left * (0.5 + r.nextDouble() * 0.4)), c.getDouble("width") * 0.6, (int)((double)c.getInt("depth") * 0.7), c.getInt("gen") + 1));
        }
        d.eventData.put(KEY, (Tag)cracks);
        d.setDirty();
    }

    private static void step(ServerLevel level, CatastropheSavedData d, CompoundTag c, boolean destroy, RandomSource r) {
        int t = c.getInt("t");
        int len = c.getInt("len");
        double x = c.getDouble("x");
        double z = c.getDouble("z");
        double ang = c.getDouble("ang");
        double frac = (double)t / (double)len;
        double taper = 1.0 - 0.75 * frac;
        double halfW = Math.max(0.5, c.getDouble("width") / 2.0 * taper);
        int depth = Math.max(2, (int)Math.round((double)c.getInt("depth") * taper));
        BlockPos column = BlockPos.containing((double)x, (double)d.centerY, (double)z);
        if (level.isLoaded(column)) {
            int top = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, column.getX(), column.getZ());
            BlockPos tip = new BlockPos(column.getX(), top, column.getZ());
            if (t % 3 == 0) {
                level.playSound(null, tip, SoundEvents.ROOTED_DIRT_FALL, SoundSource.BLOCKS, 1.2f, 0.5f);
            }
            GroundCrackEvent.surfaceDust(level, x, z, 6, halfW + 0.5);
            GroundCrackEvent.pushAway(level, x, top, z, ang);
            if (destroy) {
                GroundCrackEvent.carveSlice(level, d, x, z, ang, halfW, depth, c.getInt("depth"), r);
            }
        }
        c.putDouble("ang", ang += (r.nextDouble() - 0.5) * 0.35);
        c.putDouble("x", x + Math.cos(ang));
        c.putDouble("z", z + Math.sin(ang));
        c.putInt("t", t + 1);
    }

    private static void carveSlice(ServerLevel level, CatastropheSavedData d, double x, double z, double ang, double halfW, int depth, int maxDepth, RandomSource r) {
        int limit = (Integer)CatastropheConfig.CRACKS_MAX_BLOCKS.get();
        double px = -Math.sin(ang);
        double pz = Math.cos(ang);
        int reach = (int)Math.ceil(halfW);
        boolean lava = (Boolean)CatastropheConfig.CRACKS_LAVA.get() != false && CatastropheConfig.DESTRUCTION.get() == CatastropheConfig.Destruction.INTENSE && (double)depth >= Math.max(4.0, (double)maxDepth * 0.7);
        for (int off = -reach; off <= reach; ++off) {
            BlockPos p;
            int top;
            int bz;
            int bx = Mth.floor((double)(x + px * (double)off));
            if (!level.isLoaded(new BlockPos(bx, d.centerY, bz = Mth.floor((double)(z + pz * (double)off)))) || !level.getFluidState(new BlockPos(bx, top = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, bx, bz) - 1, bz)).isEmpty()) continue;
            int bottom = top;
            for (int dy = 0; dy <= depth; ++dy) {
                double allowed = halfW * (1.0 - 0.7 * (double)dy / (double)depth);
                if ((double)Math.abs(off) > allowed + 0.5) break;
                BlockPos p2 = new BlockPos(bx, top - dy, bz);
                if (!GroundCrackEvent.removable(level, p2)) continue;
                if (!DisasterUtil.takeBlockBudget(d, limit)) {
                    return;
                }
                level.setBlock(p2, Blocks.AIR.defaultBlockState(), 3);
                bottom = top - dy;
            }
            if (!lava || off != 0 || bottom >= top - 3 || r.nextInt(3) != 0 || !level.isEmptyBlock(p = new BlockPos(bx, bottom, bz)) || !BlockProtection.canPlace(level, p) || !DisasterUtil.takeBlockBudget(d, limit)) continue;
            level.setBlock(p, Blocks.LAVA.defaultBlockState(), 3);
        }
    }

    private static boolean removable(ServerLevel level, BlockPos pos) {
        if (pos.getY() <= level.getMinBuildHeight() + 1) {
            return false;
        }
        BlockState s = level.getBlockState(pos);
        if (s.isAir() || !s.getFluidState().isEmpty()) {
            return false;
        }
        for (Direction dir : Direction.values()) {
            if (level.getFluidState(pos.relative(dir)).isEmpty()) continue;
            return false;
        }
        return BlockProtection.canModify(level, pos, s);
    }

    private static void surfaceDust(ServerLevel level, double x, double z, int count, double spread) {
        BlockPos col = BlockPos.containing((double)x, (double)64.0, (double)z);
        if (!level.isLoaded(col)) {
            return;
        }
        int top = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, col.getX(), col.getZ());
        BlockState ground = level.getBlockState(new BlockPos(col.getX(), top - 1, col.getZ()));
        if (ground.isAir()) {
            ground = Blocks.DIRT.defaultBlockState();
        }
        level.sendParticles((ParticleOptions)new BlockParticleOption(ParticleTypes.BLOCK, ground), x, (double)top + 0.2, z, count, spread * 0.5, 0.2, spread * 0.5, 0.15);
        level.sendParticles((ParticleOptions)ParticleTypes.CAMPFIRE_COSY_SMOKE, x, (double)top, z, 1, 0.3, 0.1, 0.3, 0.02);
    }

    private static void steam(ServerLevel level, ListTag cracks, long now) {
        double z;
        if (now % 7L != 0L || cracks.isEmpty()) {
            return;
        }
        CompoundTag c = cracks.getCompound((int)(now % (long)cracks.size()));
        double x = c.getDouble("x") - Math.cos(c.getDouble("ang")) * 2.0;
        BlockPos col = BlockPos.containing((double)x, (double)64.0, (double)(z = c.getDouble("z") - Math.sin(c.getDouble("ang")) * 2.0));
        if (!level.isLoaded(col)) {
            return;
        }
        int top = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, col.getX(), col.getZ());
        level.sendParticles((ParticleOptions)ParticleTypes.CLOUD, x, (double)top + 0.5, z, 4, 0.3, 0.6, 0.3, 0.02);
    }

    private static void pushAway(ServerLevel level, double x, int y, double z, double ang) {
        AABB box = new AABB(x - 2.0, (double)(y - 1), z - 2.0, x + 2.0, (double)(y + 3), z + 2.0);
        double px = -Math.sin(ang);
        double pz = Math.cos(ang);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, box, LivingEntity::isAlive)) {
            Player p;
            if (e instanceof Player && ((p = (Player)e).isCreative() || p.isSpectator())) continue;
            double side = (e.getX() - x) * px + (e.getZ() - z) * pz >= 0.0 ? 1.0 : -1.0;
            e.setDeltaMovement(e.getDeltaMovement().add(px * side * 0.25, 0.15, pz * side * 0.25));
            e.hurtMarked = true;
        }
    }
}

