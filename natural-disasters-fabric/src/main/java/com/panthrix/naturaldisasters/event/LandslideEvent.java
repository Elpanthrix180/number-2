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
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.item.FallingBlockEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;

public class LandslideEvent
extends CatastropheEvent {
    private static final int[][] DIRS = new int[][]{{1, 0}, {-1, 0}, {0, 1}, {0, -1}};

    @Override
    public void chooseLocation(ServerLevel level, CatastropheSavedData d) {
        RandomSource r = level.getRandom();
        int search = DisasterUtil.radius();
        int bestX = d.centerX;
        int bestZ = d.centerZ;
        int bestSlope = -1;
        for (int i = 0; i < 64; ++i) {
            int z;
            int x = d.centerX + r.nextInt(2 * search + 1) - search;
            int slope = LandslideEvent.slopeAt(level, x, z = d.centerZ + r.nextInt(2 * search + 1) - search);
            if (slope <= bestSlope) continue;
            bestSlope = slope;
            bestX = x;
            bestZ = z;
        }
        d.centerX = bestX;
        d.centerZ = bestZ;
        if (level.isLoaded(new BlockPos(bestX, d.centerY, bestZ))) {
            d.centerY = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, bestX, bestZ);
        }
        d.eventData.putInt("slope", bestSlope);
        d.setDirty();
    }

    private static int slopeAt(ServerLevel level, int x, int z) {
        int[][] offs;
        int min = Integer.MAX_VALUE;
        int max = Integer.MIN_VALUE;
        for (int[] o : offs = new int[][]{{0, 0}, {3, 0}, {-3, 0}, {0, 3}, {0, -3}}) {
            if (!level.isLoaded(new BlockPos(x + o[0], 64, z + o[1]))) {
                return -1;
            }
            int h = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x + o[0], z + o[1]);
            min = Math.min(min, h);
            max = Math.max(max, h);
        }
        return max - min;
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
        int sr = (Integer)CatastropheConfig.SLIDE_RADIUS.get();
        RandomSource r = level.getRandom();
        if (now % 20L == 0L) {
            BlockPos at = new BlockPos(d.centerX, d.centerY, d.centerZ);
            level.playSound(null, at, SoundEvents.GRAVEL_BREAK, SoundSource.BLOCKS, active ? 3.0f : 1.0f, 0.4f);
            level.playSound(null, at, SoundEvents.ROOTED_DIRT_FALL, SoundSource.BLOCKS, active ? 2.0f : 0.7f, 0.5f);
            if (((Boolean)CatastropheConfig.QUAKE_CAMERA_SHAKE.get()).booleanValue()) {
                for (ServerPlayer p : DisasterUtil.playersInArea(level, d)) {
                    ModNetwork.sendShake(p, active ? (float)(0.4 * f) : 0.15f, 25);
                }
            }
        }
        if (now % 4L == 0L) {
            BlockState dust = level.getBlockState(new BlockPos(d.centerX, d.centerY - 1, d.centerZ));
            if (dust.isAir()) {
                dust = Blocks.DIRT.defaultBlockState();
            }
            level.sendParticles((ParticleOptions)new BlockParticleOption(ParticleTypes.BLOCK, dust), (double)d.centerX + 0.5, (double)(d.centerY + 1), (double)d.centerZ + 0.5, active ? (int)(25.0 * f) : 6, (double)sr * 0.5, 1.0, (double)sr * 0.5, 0.1);
        }
        if (phase == CatastrophePhase.PREPARATION) {
            return;
        }
        if (now % 5L == 0L) {
            LandslideEvent.pushEntities(level, d, sr, f);
        }
        if (CatastropheConfig.destructionOff()) {
            return;
        }
        int moved = d.eventData.getInt("moved");
        if (moved >= (Integer)CatastropheConfig.SLIDE_MAX_BLOCKS.get()) {
            return;
        }
        int perTick = active ? (int)Math.max(1.0, 3.0 * f) : 1;
        for (int i = 0; i < perTick; ++i) {
            moved += LandslideEvent.slideOne(level, d, r, sr);
        }
        d.eventData.putInt("moved", moved);
        d.setDirty();
    }

    private static int slideOne(ServerLevel level, CatastropheSavedData d, RandomSource r, int sr) {
        BlockPos pos;
        BlockState s;
        int z;
        int x = d.centerX + r.nextInt(2 * sr + 1) - sr;
        if ((x - d.centerX) * (x - d.centerX) + ((z = d.centerZ + r.nextInt(2 * sr + 1) - sr) - d.centerZ) * (z - d.centerZ) > sr * sr) {
            return 0;
        }
        if (!level.isLoaded(new BlockPos(x, d.centerY, z))) {
            return 0;
        }
        int h = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
        int bestDx = 0;
        int bestDz = 0;
        int drop = 0;
        for (int[] o : DIRS) {
            int hn;
            if (!level.isLoaded(new BlockPos(x + o[0] * 2, h, z + o[1] * 2)) || h - (hn = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x + o[0] * 2, z + o[1] * 2)) <= drop) continue;
            drop = h - hn;
            bestDx = o[0];
            bestDz = o[1];
        }
        if (drop < 2) {
            return 0;
        }
        int layers = 1 + r.nextInt(((Integer)CatastropheConfig.SLIDE_DEPTH.get()).intValue());
        int count = 0;
        for (int k = 0; k < layers && LandslideEvent.canSlide(s = level.getBlockState(pos = new BlockPos(x, h - 1 - k, z))) && BlockProtection.canModify(level, pos, s) && DisasterUtil.takeBlockBudget(d); ++k) {
            BlockState moving = s.is(BlockTags.BASE_STONE_OVERWORLD) ? (r.nextBoolean() ? Blocks.GRAVEL.defaultBlockState() : Blocks.COBBLESTONE.defaultBlockState()) : (s.is(Blocks.GRASS_BLOCK) ? Blocks.DIRT.defaultBlockState() : s);
            level.setBlock(pos, moving, 3);
            FallingBlockEntity fb = FallingBlockEntity.fall((Level)level, (BlockPos)pos, (BlockState)moving);
            fb.setDeltaMovement((double)bestDx * (0.35 + r.nextDouble() * 0.3), 0.15, (double)bestDz * (0.35 + r.nextDouble() * 0.3));
            fb.hurtMarked = true;
            if (((Boolean)CatastropheConfig.DAMAGE_PLAYERS.get()).booleanValue() || ((Boolean)CatastropheConfig.DAMAGE_MOBS.get()).booleanValue()) {
                fb.setHurtsEntities(1.0f, 6);
            }
            ++count;
        }
        BlockPos above = new BlockPos(x, h, z);
        BlockState top = level.getBlockState(above);
        if (count > 0 && !top.isAir() && top.canBeReplaced() && top.getFluidState().isEmpty() && BlockProtection.canModify(level, above, top)) {
            level.destroyBlock(above, false);
        }
        return count;
    }

    private static boolean canSlide(BlockState s) {
        if (s.isAir() || !s.getFluidState().isEmpty()) {
            return false;
        }
        if (s.is(BlockTags.DIRT) || s.is(BlockTags.SAND) || s.is(Blocks.GRAVEL) || s.is(Blocks.CLAY) || s.is(BlockTags.BASE_STONE_OVERWORLD) || s.is(Blocks.COBBLESTONE) || s.is(Blocks.SNOW_BLOCK)) {
            return true;
        }
        return (Boolean)CatastropheConfig.SLIDE_BUILDINGS.get() != false && (s.is(BlockTags.PLANKS) || s.is(BlockTags.STAIRS) || s.is(BlockTags.SLABS) || s.is(Blocks.BRICKS) || s.is(BlockTags.STONE_BRICKS) || s.is(BlockTags.LOGS));
    }

    private static void pushEntities(ServerLevel level, CatastropheSavedData d, int sr, double f) {
        AABB box = new AABB((double)(d.centerX - sr), (double)(d.centerY - sr), (double)(d.centerZ - sr), (double)(d.centerX + sr), (double)(d.centerY + sr), (double)(d.centerZ + sr));
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, box, LivingEntity::isAlive)) {
            Player p;
            if (e instanceof Player && ((p = (Player)e).isCreative() || p.isSpectator()) || !e.onGround()) continue;
            int x = e.getBlockX();
            int z = e.getBlockZ();
            int h = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
            double bx = 0.0;
            double bz = 0.0;
            for (int[] o : DIRS) {
                int hn;
                if (!level.isLoaded(new BlockPos(x + o[0] * 2, h, z + o[1] * 2)) || (hn = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x + o[0] * 2, z + o[1] * 2)) >= h) continue;
                bx += (double)(o[0] * (h - hn));
                bz += (double)(o[1] * (h - hn));
            }
            double len = Math.sqrt(bx * bx + bz * bz);
            if (len < 0.01) continue;
            e.setDeltaMovement(e.getDeltaMovement().add(bx / len * 0.08 * f, 0.0, bz / len * 0.08 * f));
            e.hurtMarked = true;
        }
    }
}

