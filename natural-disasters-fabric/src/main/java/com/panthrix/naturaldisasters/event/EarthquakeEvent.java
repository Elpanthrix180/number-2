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

public class EarthquakeEvent
extends CatastropheEvent {
    private static final int TYPE_CRACK = 0;
    private static final int TYPE_CAVE = 1;

    @Override
    public void onPhaseStart(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase) {
        if (phase == CatastrophePhase.ACTIVE && !CatastropheConfig.destructionOff()) {
            d.eventData.put("plans", (Tag)EarthquakeEvent.makePlans(level, d));
            d.eventData.putInt("plan", 0);
            d.setDirty();
        }
    }

    @Override
    public void tick(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase, long now) {
        float shake;
        if (phase != CatastrophePhase.PREPARATION && phase != CatastrophePhase.ACTIVE && phase != CatastrophePhase.ENDING) {
            return;
        }
        double f = CatastropheConfig.intensityFactor();
        switch (phase) {
            case PREPARATION: {
                float f2 = 0.35f;
                break;
            }
            case ACTIVE: {
                float f2 = (float)(1.2 * f);
                break;
            }
            default: {
                float f2 = shake = 0.5f;
            }
        }
        if (now % 20L == 0L) {
            for (ServerPlayer p : DisasterUtil.playersInArea(level, d)) {
                if (((Boolean)CatastropheConfig.QUAKE_CAMERA_SHAKE.get()).booleanValue()) {
                    ModNetwork.sendShake(p, shake, 25);
                }
                level.playSound(null, p.blockPosition().below(3), SoundEvents.GRAVEL_BREAK, SoundSource.AMBIENT, 1.5f, 0.3f);
                if (phase != CatastrophePhase.ACTIVE || level.getRandom().nextInt(3) != 0) continue;
                level.playSound(null, p.blockPosition().below(8), SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.AMBIENT, 0.5f, 0.4f);
            }
        }
        if (now % 4L == 0L) {
            for (ServerPlayer p : DisasterUtil.playersInArea(level, d)) {
                BlockState ground = level.getBlockState(p.blockPosition().below());
                if (ground.isAir()) continue;
                level.sendParticles((ParticleOptions)new BlockParticleOption(ParticleTypes.BLOCK, ground), p.getX(), p.getY() + 0.1, p.getZ(), (int)(6.0f * shake) + 2, 4.0, 0.1, 4.0, 0.1);
            }
        }
        if (phase != CatastrophePhase.PREPARATION && now % 5L == 0L) {
            EarthquakeEvent.shakeEntities(level, d, shake);
        }
        if (phase == CatastrophePhase.PREPARATION || CatastropheConfig.destructionOff()) {
            return;
        }
        EarthquakeEvent.runPlans(level, d);
        if (phase == CatastrophePhase.ACTIVE && now % 20L == 0L && ((Boolean)CatastropheConfig.QUAKE_BUILDING_DAMAGE.get()).booleanValue()) {
            EarthquakeEvent.damageBuilding(level, d);
        }
    }

    private static void shakeEntities(ServerLevel level, CatastropheSavedData d, float shake) {
        RandomSource r = level.getRandom();
        for (LivingEntity e : DisasterUtil.livingInArea(level, d)) {
            Player p;
            if (!e.onGround() || e instanceof Player && ((p = (Player)e).isCreative() || p.isSpectator())) continue;
            double k = 0.04 * (double)shake;
            e.setDeltaMovement(e.getDeltaMovement().add((r.nextDouble() - 0.5) * k, 0.02 * (double)shake, (r.nextDouble() - 0.5) * k));
            e.hurtMarked = true;
        }
    }

    private static ListTag makePlans(ServerLevel level, CatastropheSavedData d) {
        RandomSource r = level.getRandom();
        double f = CatastropheConfig.intensityFactor();
        boolean intense = CatastropheConfig.DESTRUCTION.get() == CatastropheConfig.Destruction.INTENSE;
        int radius = DisasterUtil.radius();
        ListTag plans = new ListTag();
        int cracks = Math.max(1, (int)Math.round((double)((Integer)CatastropheConfig.QUAKE_CRACK_COUNT.get()).intValue() * Math.min(f, 1.5)));
        for (int i = 0; i < cracks; ++i) {
            plans.add((Object)EarthquakeEvent.crackPlan(r, d, radius, (Integer)CatastropheConfig.QUAKE_CRACK_WIDTH.get(), (Integer)CatastropheConfig.QUAKE_CRACK_DEPTH.get(), f));
        }
        if (intense) {
            int trenches = 1 + (f > 1.0 ? 1 : 0);
            for (int i = 0; i < trenches; ++i) {
                plans.add((Object)EarthquakeEvent.crackPlan(r, d, radius, Math.min(7, (Integer)CatastropheConfig.QUAKE_CRACK_WIDTH.get() + 3), Math.max(3, (Integer)CatastropheConfig.QUAKE_CRACK_DEPTH.get() / 3), f));
            }
            if (((Boolean)CatastropheConfig.QUAKE_CAVES.get()).booleanValue()) {
                int caves = 1 + (f > 1.0 ? 1 : 0);
                for (int i = 0; i < caves; ++i) {
                    CompoundTag cave = EarthquakeEvent.cavePlan(level, r, d, radius);
                    if (cave == null) continue;
                    plans.add((Object)cave);
                }
            }
        }
        return plans;
    }

    private static CompoundTag crackPlan(RandomSource r, CatastropheSavedData d, int radius, int width, int depth, double f) {
        CompoundTag p = new CompoundTag();
        p.putInt("type", 0);
        double a = r.nextDouble() * Math.PI * 2.0;
        double off = r.nextDouble() * (double)radius * 0.6;
        p.putDouble("x", (double)d.centerX + Math.cos(a) * off);
        p.putDouble("z", (double)d.centerZ + Math.sin(a) * off);
        p.putDouble("ang", r.nextDouble() * Math.PI * 2.0);
        p.putDouble("seed", r.nextDouble() * 100.0);
        int len = Math.max(5, (int)((double)((Integer)CatastropheConfig.QUAKE_CRACK_LENGTH.get()).intValue() * (0.6 + 0.4 * Math.min(f, 1.5) * r.nextDouble() * 1.5)));
        p.putInt("len", Math.min(len, (Integer)CatastropheConfig.QUAKE_CRACK_LENGTH.get()));
        p.putInt("width", width);
        p.putInt("depth", Math.max(2, (int)((double)depth * Math.min(1.0, 0.6 + 0.4 * f))));
        p.putInt("t", 0);
        return p;
    }

    private static CompoundTag cavePlan(ServerLevel level, RandomSource r, CatastropheSavedData d, int radius) {
        int z;
        int x = d.centerX + r.nextInt(radius) - radius / 2;
        if (!level.isLoaded(new BlockPos(x, d.centerY, z = d.centerZ + r.nextInt(radius) - radius / 2))) {
            return null;
        }
        int surface = level.getHeight(Heightmap.Types.OCEAN_FLOOR, x, z);
        int y = surface - 10 - r.nextInt(12);
        if (y < level.getMinBuildHeight() + 6) {
            return null;
        }
        CompoundTag p = new CompoundTag();
        p.putInt("type", 1);
        p.putInt("cx", x);
        p.putInt("cy", y);
        p.putInt("cz", z);
        p.putInt("rx", 4 + r.nextInt(4));
        p.putInt("ry", 3 + r.nextInt(2));
        p.putInt("rz", 4 + r.nextInt(4));
        p.putInt("t", 0);
        return p;
    }

    private static void runPlans(ServerLevel level, CatastropheSavedData d) {
        ListTag plans = d.eventData.getList("plans", 10);
        int index = d.eventData.getInt("plan");
        int[] quota = new int[]{(Integer)CatastropheConfig.QUAKE_BLOCKS_PER_TICK.get()};
        while (index < plans.size() && quota[0] > 0) {
            boolean finished;
            CompoundTag p = plans.getCompound(index);
            boolean bl = finished = p.getInt("type") == 1 ? EarthquakeEvent.caveStep(level, d, p, quota) : EarthquakeEvent.crackStep(level, d, p, quota);
            if (finished) {
                ++index;
            }
            if (!d.eventData.getBoolean("budgetFull")) continue;
            index = plans.size();
        }
        d.eventData.putInt("plan", index);
        d.setDirty();
    }

    private static boolean crackStep(ServerLevel level, CatastropheSavedData d, CompoundTag p, int[] quota) {
        int len;
        int t = p.getInt("t");
        if (t > (len = p.getInt("len"))) {
            return true;
        }
        double ang = p.getDouble("ang") + Math.sin((double)t * 0.25 + p.getDouble("seed")) * 0.35;
        double cx = p.getDouble("x");
        double cz = p.getDouble("z");
        double frac = (double)t / (double)len;
        double taper = Math.max(0.3, Math.sin(Math.PI * frac));
        double halfW = Math.max(0.5, (double)p.getInt("width") / 2.0 * taper);
        int depth = Math.max(2, (int)Math.round((double)p.getInt("depth") * taper));
        double px = -Math.sin(ang);
        double pz = Math.cos(ang);
        int reach = (int)Math.ceil(halfW);
        block0: for (int off = -reach; off <= reach; ++off) {
            int top;
            int bz;
            int bx = Mth.floor((double)(cx + px * (double)off));
            BlockPos column = new BlockPos(bx, d.centerY, bz = Mth.floor((double)(cz + pz * (double)off)));
            if (!level.isLoaded(column) || !level.getFluidState(new BlockPos(bx, top = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, bx, bz) - 1, bz)).isEmpty()) continue;
            for (int dy = 0; dy <= depth; ++dy) {
                double allowed = halfW * (1.0 - 0.7 * (double)dy / (double)depth);
                if (!((double)Math.abs(off) > allowed + 0.5) && !EarthquakeEvent.carve(level, d, new BlockPos(bx, top - dy, bz), quota)) continue block0;
            }
        }
        if (((Boolean)CatastropheConfig.QUAKE_COLLAPSES.get()).booleanValue() && level.getRandom().nextInt(3) == 0) {
            int side = level.getRandom().nextBoolean() ? 1 : -1;
            int ex = Mth.floor((double)(cx + px * (double)(reach + 1) * (double)side));
            int ez = Mth.floor((double)(cz + pz * (double)(reach + 1) * (double)side));
            EarthquakeEvent.collapse(level, d, ex, ez, -px * (double)side, -pz * (double)side);
        }
        p.putDouble("x", cx + Math.cos(ang));
        p.putDouble("z", cz + Math.sin(ang));
        p.putInt("t", t + 1);
        quota[0] = quota[0] - 4;
        return t + 1 > len;
    }

    private static void collapse(ServerLevel level, CatastropheSavedData d, int x, int z, double dirX, double dirZ) {
        BlockPos column = new BlockPos(x, d.centerY, z);
        if (!level.isLoaded(column)) {
            return;
        }
        BlockPos pos = new BlockPos(x, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z) - 1, z);
        BlockState s = level.getBlockState(pos);
        if (!(EarthquakeEvent.isLoose(s) && BlockProtection.canModify(level, pos, s) && DisasterUtil.takeBlockBudget(d))) {
            return;
        }
        BlockState falling = s.is(Blocks.STONE) || s.is(Blocks.DEEPSLATE) ? Blocks.COBBLESTONE.defaultBlockState() : s;
        level.setBlock(pos, falling, 3);
        FallingBlockEntity e = FallingBlockEntity.fall((Level)level, (BlockPos)pos, (BlockState)falling);
        e.setDeltaMovement(dirX * 0.25, 0.1, dirZ * 0.25);
        e.hurtMarked = true;
    }

    private static boolean isLoose(BlockState s) {
        return s.is(BlockTags.DIRT) || s.is(BlockTags.SAND) || s.is(Blocks.GRAVEL) || s.is(BlockTags.BASE_STONE_OVERWORLD) || s.is(Blocks.COBBLESTONE) || s.is(Blocks.GRASS_BLOCK);
    }

    private static boolean caveStep(ServerLevel level, CatastropheSavedData d, CompoundTag p, int[] quota) {
        int t;
        int rx = p.getInt("rx");
        int ry = p.getInt("ry");
        int rz = p.getInt("rz");
        int rows = (2 * ry + 1) * (2 * rx + 1);
        for (t = p.getInt("t"); t < rows && quota[0] > 0; ++t) {
            BlockPos pos;
            double e;
            int dy = t / (2 * rx + 1) - ry;
            int dx = t % (2 * rx + 1) - rx;
            for (int dz = -rz; dz <= rz && ((e = EarthquakeEvent.sq((double)dx / (double)rx) + EarthquakeEvent.sq((double)dy / (double)ry) + EarthquakeEvent.sq((double)dz / (double)rz)) > 1.0 || EarthquakeEvent.carve(level, d, pos = new BlockPos(p.getInt("cx") + dx, p.getInt("cy") + dy, p.getInt("cz") + dz), quota)); ++dz) {
            }
            quota[0] = quota[0] - 2;
        }
        p.putInt("t", t);
        return t >= rows;
    }

    private static double sq(double v) {
        return v * v;
    }

    private static boolean carve(ServerLevel level, CatastropheSavedData d, BlockPos pos, int[] quota) {
        if (pos.getY() <= level.getMinBuildHeight() + 1 || !level.isLoaded(pos)) {
            return true;
        }
        BlockState s = level.getBlockState(pos);
        if (s.isAir() || !s.getFluidState().isEmpty()) {
            return true;
        }
        for (Direction dir : Direction.values()) {
            if (level.getFluidState(pos.relative(dir)).isEmpty()) continue;
            return true;
        }
        if (!BlockProtection.canModify(level, pos, s)) {
            return true;
        }
        if (!DisasterUtil.takeBlockBudget(d)) {
            d.eventData.putBoolean("budgetFull", true);
            return false;
        }
        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
        quota[0] = quota[0] - 1;
        return true;
    }

    private static void damageBuilding(ServerLevel level, CatastropheSavedData d) {
        boolean building;
        BlockPos top = DisasterUtil.randomSurface(level, d, level.getRandom());
        if (top == null) {
            return;
        }
        BlockPos pos = top.below();
        BlockState s = level.getBlockState(pos);
        boolean bl = building = s.is(BlockTags.PLANKS) || s.is(BlockTags.STAIRS) || s.is(BlockTags.SLABS) || s.is(BlockTags.WALLS) || s.is(BlockTags.STONE_BRICKS) || s.is(Blocks.BRICKS) || s.is(Blocks.COBBLESTONE) || s.is(BlockTags.LOGS);
        if (!(building && BlockProtection.canModify(level, pos, s) && DisasterUtil.takeBlockBudget(d))) {
            return;
        }
        FallingBlockEntity.fall((Level)level, (BlockPos)pos, (BlockState)s);
    }
}

