package com.panthrix.naturaldisasters.event;

import com.panthrix.naturaldisasters.NaturalDisastersMod;
import com.panthrix.naturaldisasters.config.CatastropheConfig;
import com.panthrix.naturaldisasters.core.BlockProtection;
import com.panthrix.naturaldisasters.core.CatastropheEvent;
import com.panthrix.naturaldisasters.core.CatastrophePhase;
import com.panthrix.naturaldisasters.core.CatastropheSavedData;
import com.panthrix.naturaldisasters.event.DisasterUtil;
import com.panthrix.naturaldisasters.network.ModNetwork;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Position;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.FloatTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.Fluids;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

public class MeteorShowerEvent
extends CatastropheEvent {
    private static final String KEY = "meteors";
    private static final String CRATERS = "craters";
    private static final String ENTITY_TAG = "panthrixsnaturaldisasters_meteor";
    private static final int MAX_IN_FLIGHT = 8;

    @Override
    public void tick(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase, long now) {
        MeteorShowerEvent.tintSky(level, d, phase, now);
        if (phase == CatastrophePhase.PREPARATION && now % 8L == 0L) {
            for (ServerPlayer p : DisasterUtil.playersInArea(level, d)) {
                level.sendParticles((ParticleOptions)ParticleTypes.END_ROD, p.getX(), p.getY() + 45.0, p.getZ(), 6, 35.0, 6.0, 35.0, 0.3);
                level.sendParticles((ParticleOptions)ParticleTypes.FLAME, p.getX(), p.getY() + 50.0, p.getZ(), 4, 40.0, 4.0, 40.0, 0.1);
            }
        }
        MeteorShowerEvent.digCraters(level, d);
        if (phase != CatastrophePhase.ACTIVE && phase != CatastrophePhase.ENDING && phase != CatastrophePhase.RECOVERY) {
            return;
        }
        ListTag meteors = d.eventData.getList(KEY, 10);
        if (phase != CatastrophePhase.RECOVERY) {
            int interval;
            double perMinute = (double)((Integer)CatastropheConfig.METEORS_PER_MINUTE.get()).intValue() * CatastropheConfig.intensityFactor();
            if (phase == CatastrophePhase.ENDING) {
                perMinute /= 3.0;
            }
            if (now % (long)(interval = (int)Math.max(10.0, 1200.0 / Math.max(1.0, perMinute))) == 0L && meteors.size() < 8) {
                MeteorShowerEvent.spawnMeteor(level, d, meteors, now);
            }
        }
        for (int i = meteors.size() - 1; i >= 0; --i) {
            Entity ball;
            CompoundTag m = meteors.getCompound(i);
            double t = (double)(now - m.getLong("t0")) / (double)m.getInt("dur");
            float size = m.getFloat("size");
            Entity entity = ball = m.hasUUID("ent") ? level.getEntity(m.getUUID("ent")) : null;
            if (t >= 1.0) {
                if (ball != null) {
                    ball.discard();
                }
                MeteorShowerEvent.impact(level, d, BlockPos.of((long)m.getLong("target")), size);
                meteors.remove(i);
                continue;
            }
            double e = t * t;
            Vec3 start = new Vec3(m.getDouble("sx"), m.getDouble("sy"), m.getDouble("sz"));
            Vec3 end = new Vec3(m.getDouble("tx"), m.getDouble("ty"), m.getDouble("tz"));
            Vec3 pos = start.lerp(end, e);
            if (ball != null) {
                ball.setPos(pos.x, pos.y, pos.z);
            }
            MeteorShowerEvent.drawMeteor(level, pos, start.subtract(end).normalize(), size);
            if (now % 20L != 0L) continue;
            level.playSound(null, BlockPos.containing((Position)pos), SoundEvents.FIRECHARGE_USE, SoundSource.WEATHER, 6.0f, 0.3f);
        }
        d.eventData.put(KEY, (Tag)meteors);
        d.setDirty();
    }

    private static void tintSky(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase, long now) {
        float strength;
        if (!((Boolean)CatastropheConfig.METEOR_SKY_TINT.get()).booleanValue() || now % 20L != 0L) {
            return;
        }
        switch (phase) {
            case WARNING: {
                float f = 0.35f;
                break;
            }
            case PREPARATION: {
                float f = 0.75f;
                break;
            }
            case ACTIVE: {
                float f = 1.0f;
                break;
            }
            case ENDING: {
                float f = 0.5f;
                break;
            }
            default: {
                float f = strength = 0.0f;
            }
        }
        if (strength <= 0.0f) {
            return;
        }
        double far = (double)DisasterUtil.radius() * 4.0;
        for (ServerPlayer p : level.players()) {
            double dz;
            double dx = p.getX() - (double)d.centerX;
            if (!(dx * dx + (dz = p.getZ() - (double)d.centerZ) * dz <= far * far)) continue;
            ModNetwork.sendSkyTint(p, strength, 60);
        }
    }

    private static void drawMeteor(ServerLevel level, Vec3 pos, Vec3 back, float size) {
        double r = 1.6 * (double)size;
        level.sendParticles((ParticleOptions)ParticleTypes.FLAME, pos.x, pos.y, pos.z, (int)(30.0f * size), r, r, r, 0.06);
        level.sendParticles((ParticleOptions)ParticleTypes.LAVA, pos.x, pos.y, pos.z, (int)(5.0f * size), r * 0.7, r * 0.7, r * 0.7, 0.0);
        for (int k = 1; k <= 10; ++k) {
            Vec3 p = pos.add(back.scale((double)k * 3.0 * (double)size));
            double spread = r * (1.0 - (double)k / 12.0);
            level.sendParticles((ParticleOptions)(k < 4 ? ParticleTypes.FLAME : ParticleTypes.CAMPFIRE_COSY_SMOKE), p.x, p.y, p.z, (int)(7.0f * size), spread, spread, spread, 0.01);
        }
    }

    private static void spawnMeteor(ServerLevel level, CatastropheSavedData d, ListTag meteors, long now) {
        RandomSource r = level.getRandom();
        BlockPos target = DisasterUtil.randomSurface(level, d, r);
        if (target == null) {
            return;
        }
        double a = r.nextDouble() * Math.PI * 2.0;
        float size = (float)((1.5 + r.nextDouble() * 1.5) * Math.min(1.5, CatastropheConfig.intensityFactor()));
        CompoundTag m = new CompoundTag();
        m.putDouble("sx", (double)target.getX() + 0.5 + Math.cos(a) * 70.0);
        m.putDouble("sy", (double)Math.min(level.getMaxBuildHeight() - 2, target.getY() + 140));
        m.putDouble("sz", (double)target.getZ() + 0.5 + Math.sin(a) * 70.0);
        m.putDouble("tx", (double)target.getX() + 0.5);
        m.putDouble("ty", (double)target.getY());
        m.putDouble("tz", (double)target.getZ() + 0.5);
        m.putLong("target", target.asLong());
        m.putLong("t0", now);
        m.putInt("dur", 70 + r.nextInt(40));
        m.putFloat("size", size);
        Entity ball = MeteorShowerEvent.spawnBall(level, new Vec3(m.getDouble("sx"), m.getDouble("sy"), m.getDouble("sz")), 3.0f * size);
        if (ball != null) {
            m.putUUID("ent", ball.getUUID());
        }
        meteors.add((Object)m);
    }

    private static Entity spawnBall(ServerLevel level, Vec3 pos, float scale) {
        try {
            Display.BlockDisplay ball = (Display.BlockDisplay)EntityType.BLOCK_DISPLAY.create((Level)level);
            if (ball == null) {
                return null;
            }
            CompoundTag tag = new CompoundTag();
            CompoundTag state = new CompoundTag();
            state.putString("Name", "minecraft:magma_block");
            tag.put("block_state", (Tag)state);
            CompoundTag tr = new CompoundTag();
            tr.put("translation", (Tag)MeteorShowerEvent.floats(-scale / 2.0f, -scale / 2.0f, -scale / 2.0f));
            tr.put("scale", (Tag)MeteorShowerEvent.floats(scale, scale, scale));
            tr.put("left_rotation", (Tag)MeteorShowerEvent.floats(0.0f, 0.0f, 0.0f, 1.0f));
            tr.put("right_rotation", (Tag)MeteorShowerEvent.floats(0.0f, 0.0f, 0.0f, 1.0f));
            tag.put("transformation", (Tag)tr);
            CompoundTag light = new CompoundTag();
            light.putInt("sky", 15);
            light.putInt("block", 15);
            tag.put("brightness", (Tag)light);
            tag.putFloat("view_range", 8.0f);
            ball.load(tag);
            ball.moveTo(pos.x, pos.y, pos.z, 0.0f, 0.0f);
            ball.addTag(ENTITY_TAG);
            level.addFreshEntity((Entity)ball);
            return ball;
        }
        catch (Exception e) {
            NaturalDisastersMod.LOGGER.warn("[Panthrix's Natural Disasters] No se pudo crear la bola del meteorito; solo habra particulas.", (Throwable)e);
            return null;
        }
    }

    private static ListTag floats(float ... values) {
        ListTag list = new ListTag();
        for (float v : values) {
            list.add((Object)FloatTag.valueOf((float)v));
        }
        return list;
    }

    private static void impact(ServerLevel level, CatastropheSavedData d, BlockPos pos, float size) {
        double dist;
        if (!level.isLoaded(pos)) {
            return;
        }
        double x = (double)pos.getX() + 0.5;
        double y = (double)pos.getY() + 0.5;
        double z = (double)pos.getZ() + 0.5;
        RandomSource rand = level.getRandom();
        for (int i = 0; i < 4 + (int)(2.0f * size); ++i) {
            level.sendParticles((ParticleOptions)ParticleTypes.EXPLOSION_EMITTER, x + rand.nextGaussian() * 3.0 * (double)size, y + rand.nextDouble() * 3.0, z + rand.nextGaussian() * 3.0 * (double)size, 1, 0.0, 0.0, 0.0, 0.0);
        }
        level.sendParticles((ParticleOptions)ParticleTypes.LAVA, x, y + 1.0, z, (int)(60.0f * size), (double)(4.0f * size), 1.5, (double)(4.0f * size), 0.0);
        level.sendParticles((ParticleOptions)ParticleTypes.FLAME, x, y + 1.0, z, (int)(80.0f * size), (double)(4.0f * size), 3.0, (double)(4.0f * size), 0.3);
        level.sendParticles((ParticleOptions)ParticleTypes.CAMPFIRE_SIGNAL_SMOKE, x, y + 2.0, z, (int)(40.0f * size), (double)(4.0f * size), 2.0, (double)(4.0f * size), 0.06);
        level.playSound(null, pos, SoundEvents.GENERIC_EXPLODE, SoundSource.WEATHER, 12.0f, 0.4f);
        level.playSound(null, pos, SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.WEATHER, 10.0f, 0.3f);
        double reach = 8.0f + 5.0f * size;
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(pos).inflate(reach), LivingEntity::isAlive)) {
            dist = Math.sqrt(e.distanceToSqr(x, y, z));
            if (dist > reach) continue;
            double k = 1.0 - dist / reach;
            if (DisasterUtil.canHurt(e)) {
                e.hurt(level.damageSources().explosion(null, null), (float)((double)(14.0f * size) * k) + 1.0f);
                if (k > 0.4) {
                    e.setSecondsOnFire(6);
                }
            }
            Vec3 away = e.position().subtract(x, y, z).normalize().scale(2.0 * k);
            e.setDeltaMovement(e.getDeltaMovement().add(away.x, 0.8 * k, away.z));
            e.hurtMarked = true;
        }
        if (((Boolean)CatastropheConfig.QUAKE_CAMERA_SHAKE.get()).booleanValue()) {
            for (ServerPlayer p : level.players()) {
                dist = Math.sqrt(p.distanceToSqr(x, y, z));
                if (!(dist < 100.0)) continue;
                ModNetwork.sendShake(p, (float)(3.0 * (double)size * (1.0 - dist / 100.0)), 35);
            }
        }
        if (CatastropheConfig.destructionOff()) {
            return;
        }
        int r = Math.max(3, Math.round((float)((Integer)CatastropheConfig.METEOR_CRATER_RADIUS.get()).intValue() * size * 0.6f));
        CompoundTag job = new CompoundTag();
        job.putInt("x", pos.getX());
        job.putInt("y", pos.getY());
        job.putInt("z", pos.getZ());
        job.putInt("r", r);
        job.putInt("depth", Math.max(3, (int)((double)r * 0.65)));
        job.putInt("stage", 0);
        job.putInt("idx", 0);
        ListTag craters = d.eventData.getList(CRATERS, 10);
        craters.add((Object)job);
        d.eventData.put(CRATERS, (Tag)craters);
        d.setDirty();
    }

    private static void digCraters(ServerLevel level, CatastropheSavedData d) {
        ListTag craters = d.eventData.getList(CRATERS, 10);
        if (craters.isEmpty()) {
            return;
        }
        int[] quota = new int[]{(Integer)CatastropheConfig.METEOR_BLOCKS_PER_TICK.get()};
        while (!craters.isEmpty() && quota[0] > 0) {
            CompoundTag job = craters.getCompound(0);
            if (!MeteorShowerEvent.craterStep(level, d, job, quota)) continue;
            craters.remove(0);
        }
        d.eventData.put(CRATERS, (Tag)craters);
        d.setDirty();
    }

    private static boolean craterStep(ServerLevel level, CatastropheSavedData d, CompoundTag job, int[] quota) {
        int cx = job.getInt("x");
        int cy = job.getInt("y");
        int cz = job.getInt("z");
        int r = job.getInt("r");
        int depth = job.getInt("depth");
        int side = 2 * r + 1;
        int columns = side * side;
        int limit = (Integer)CatastropheConfig.METEOR_MAX_BLOCKS.get();
        RandomSource rand = level.getRandom();
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        while (quota[0] > 0) {
            int stage = job.getInt("stage");
            int idx = job.getInt("idx");
            if (idx >= columns) {
                if (stage >= 2) {
                    return true;
                }
                job.putInt("stage", stage + 1);
                job.putInt("idx", 0);
                continue;
            }
            job.putInt("idx", idx + 1);
            int dx = idx % side - r;
            int dz = idx / side - r;
            double hd = Math.sqrt(dx * dx + dz * dz) / (double)r;
            if (hd > 1.0) continue;
            int bottom = (int)Math.round((double)(-depth) * Math.sqrt(1.0 - hd * hd));
            int x = cx + dx;
            int z = cz + dz;
            if (!level.isLoaded((BlockPos)p.set(x, cy, z))) continue;
            if (stage == 0) {
                for (int dy = bottom; dy <= Math.max(6, r / 2); ++dy) {
                    p.set(x, cy + dy, z);
                    if (!MeteorShowerEvent.removable(level, (BlockPos)p)) continue;
                    if (!DisasterUtil.takeBlockBudget(d, limit)) {
                        return true;
                    }
                    level.setBlock((BlockPos)p, Blocks.AIR.defaultBlockState(), 18);
                    quota[0] = quota[0] - 1;
                }
                quota[0] = quota[0] - 1;
                continue;
            }
            if (stage == 1) {
                for (int layer = 1; layer <= 2; ++layer) {
                    p.set(x, cy + bottom - layer, z);
                    BlockState old = level.getBlockState((BlockPos)p);
                    if (!old.isAir() && !MeteorShowerEvent.removable(level, (BlockPos)p)) continue;
                    if (!BlockProtection.canPlace(level, (BlockPos)p) || !DisasterUtil.takeBlockBudget(d, limit)) {
                        return true;
                    }
                    int n = rand.nextInt(10);
                    BlockState rock = n < 4 ? Blocks.OBSIDIAN.defaultBlockState() : (n < 7 ? Blocks.MAGMA_BLOCK.defaultBlockState() : Blocks.BLACKSTONE.defaultBlockState());
                    level.setBlock((BlockPos)p, rock, 2);
                    quota[0] = quota[0] - 1;
                }
                if (!(hd > 0.85) || rand.nextInt(6) != 0) continue;
                p.set(x, cy + bottom, z);
                if (!level.isEmptyBlock((BlockPos)p) || !BlockProtection.canPlace(level, (BlockPos)p)) continue;
                level.setBlock((BlockPos)p, Blocks.FIRE.defaultBlockState(), 3);
                continue;
            }
            if (hd > 0.35) continue;
            p.set(x, cy + bottom, z);
            if (!level.isEmptyBlock((BlockPos)p) || !BlockProtection.canPlace(level, (BlockPos)p)) continue;
            if (!DisasterUtil.takeBlockBudget(d, limit)) {
                return true;
            }
            BlockPos below = p.below();
            if (((Boolean)CatastropheConfig.METEOR_ORES.get()).booleanValue() && rand.nextInt(5) == 0 && (level.isEmptyBlock(below) || MeteorShowerEvent.removable(level, below))) {
                level.setBlock(below, Blocks.RAW_IRON_BLOCK.defaultBlockState(), 2);
            }
            level.setBlock((BlockPos)p, Blocks.LAVA.defaultBlockState(), 3);
            quota[0] = quota[0] - 2;
        }
        return false;
    }

    private static boolean removable(ServerLevel level, BlockPos pos) {
        if (!level.isLoaded(pos)) {
            return false;
        }
        BlockState s = level.getBlockState(pos);
        if (s.isAir() || !s.getFluidState().isEmpty()) {
            return false;
        }
        for (Direction dir : Direction.values()) {
            if (!level.getFluidState(pos.relative(dir)).is((Fluid)Fluids.WATER)) continue;
            return false;
        }
        return BlockProtection.canModify(level, pos, s);
    }

    @Override
    public void onPhaseStart(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase) {
        if (phase == CatastrophePhase.RECOVERY) {
            MeteorShowerEvent.removeBalls(level, d);
        }
    }

    @Override
    public void onFinish(ServerLevel level, CatastropheSavedData d) {
        MeteorShowerEvent.removeBalls(level, d);
        ListTag craters = d.eventData.getList(CRATERS, 10);
        int[] quota = new int[]{Integer.MAX_VALUE};
        for (int i = 0; i < craters.size(); ++i) {
            MeteorShowerEvent.craterStep(level, d, craters.getCompound(i), quota);
        }
    }

    private static void removeBalls(ServerLevel level, CatastropheSavedData d) {
        for (Tag t : d.eventData.getList(KEY, 10)) {
            UUID id;
            Entity e;
            CompoundTag m = (CompoundTag)t;
            if (!m.hasUUID("ent") || (e = level.getEntity(id = m.getUUID("ent"))) == null) continue;
            e.discard();
        }
        double far = (double)DisasterUtil.radius() * 4.0 + 100.0;
        AABB box = new AABB((double)d.centerX - far, (double)level.getMinBuildHeight(), (double)d.centerZ - far, (double)d.centerX + far, (double)level.getMaxBuildHeight(), (double)d.centerZ + far);
        for (Entity e : level.getEntitiesOfClass(Display.BlockDisplay.class, box, en -> en.getTags().contains(ENTITY_TAG))) {
            e.discard();
        }
    }
}

