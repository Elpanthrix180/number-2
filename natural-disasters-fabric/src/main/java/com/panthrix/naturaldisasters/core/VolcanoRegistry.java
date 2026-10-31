package com.panthrix.naturaldisasters.core;

import it.unimi.dsi.fastutil.longs.LongArrayList;
import java.util.concurrent.ConcurrentLinkedQueue;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.saveddata.SavedData;

public class VolcanoRegistry
extends SavedData {
    private static final String NAME = "panthrixsnaturaldisasters_volcanoes";
    private static final int MAX = 512;
    private static final ConcurrentLinkedQueue<Long> PENDING = new ConcurrentLinkedQueue();
    private final LongArrayList craters = new LongArrayList();

    public static void queue(BlockPos crater) {
        PENDING.add(crater.asLong());
    }

    public static VolcanoRegistry get(ServerLevel overworld) {
        return (VolcanoRegistry)overworld.getDataStorage().computeIfAbsent(VolcanoRegistry::load, VolcanoRegistry::new, NAME);
    }

    public static void drainPending(MinecraftServer server) {
        Long l;
        if (PENDING.isEmpty()) {
            return;
        }
        VolcanoRegistry reg = VolcanoRegistry.get(server.overworld());
        while ((l = PENDING.poll()) != null) {
            reg.add(BlockPos.of((long)l));
        }
    }

    public void add(BlockPos crater) {
        long key = crater.asLong();
        if (this.craters.contains(key)) {
            return;
        }
        this.craters.add(key);
        while (this.craters.size() > 512) {
            this.craters.removeLong(0);
        }
        this.setDirty();
    }

    public BlockPos nearest(int x, int z, int maxDistance) {
        BlockPos best = null;
        long bestD = (long)maxDistance * (long)maxDistance;
        for (int i = 0; i < this.craters.size(); ++i) {
            long dz;
            BlockPos p = BlockPos.of((long)this.craters.getLong(i));
            long dx = p.getX() - x;
            long dd = dx * dx + (dz = (long)(p.getZ() - z)) * dz;
            if (dd > bestD) continue;
            bestD = dd;
            best = p;
        }
        return best;
    }

    public int size() {
        return this.craters.size();
    }

    private static VolcanoRegistry load(CompoundTag tag) {
        VolcanoRegistry r = new VolcanoRegistry();
        for (long l : tag.getLongArray("craters")) {
            r.craters.add(l);
        }
        return r;
    }

    public CompoundTag save(CompoundTag tag) {
        tag.putLongArray("craters", this.craters.toLongArray());
        return tag;
    }
}

