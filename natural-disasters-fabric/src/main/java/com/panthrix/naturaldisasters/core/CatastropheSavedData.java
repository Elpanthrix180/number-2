package com.panthrix.naturaldisasters.core;

import com.panthrix.naturaldisasters.core.CatastrophePhase;
import com.panthrix.naturaldisasters.core.CatastropheType;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.Tag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.saveddata.SavedData;

public class CatastropheSavedData
extends SavedData {
    private static final String NAME = "panthrixsnaturaldisasters_state";
    public boolean randomEnabled = true;
    public long nextEventTick = -1L;
    public CatastrophePhase phase = CatastrophePhase.CALM;
    public CatastropheType activeType = null;
    public long phaseEndTick = 0L;
    public CatastropheType lastType = null;
    public int centerX;
    public int centerY;
    public int centerZ;
    public CompoundTag eventData = new CompoundTag();

    public static CatastropheSavedData get(ServerLevel overworld) {
        return (CatastropheSavedData)overworld.getDataStorage().computeIfAbsent(CatastropheSavedData::load, CatastropheSavedData::new, NAME);
    }

    private static CatastropheSavedData load(CompoundTag tag) {
        CatastropheSavedData d = new CatastropheSavedData();
        d.randomEnabled = tag.getBoolean("randomEnabled");
        d.nextEventTick = tag.getLong("nextEventTick");
        d.phaseEndTick = tag.getLong("phaseEndTick");
        d.centerX = tag.getInt("centerX");
        d.centerY = tag.getInt("centerY");
        d.centerZ = tag.getInt("centerZ");
        d.eventData = tag.getCompound("eventData");
        d.activeType = CatastropheType.byId(tag.getString("activeType"));
        d.lastType = CatastropheType.byId(tag.getString("lastType"));
        try {
            d.phase = CatastrophePhase.valueOf(tag.getString("phase"));
        }
        catch (IllegalArgumentException e) {
            d.phase = CatastrophePhase.CALM;
        }
        if (d.activeType == null) {
            d.phase = CatastrophePhase.CALM;
        }
        if (d.phase == CatastrophePhase.CALM) {
            d.activeType = null;
        }
        return d;
    }

    public CompoundTag save(CompoundTag tag) {
        tag.putBoolean("randomEnabled", this.randomEnabled);
        tag.putLong("nextEventTick", this.nextEventTick);
        tag.putLong("phaseEndTick", this.phaseEndTick);
        tag.putInt("centerX", this.centerX);
        tag.putInt("centerY", this.centerY);
        tag.putInt("centerZ", this.centerZ);
        tag.putString("phase", this.phase.name());
        tag.putString("activeType", this.activeType == null ? "" : this.activeType.id);
        tag.putString("lastType", this.lastType == null ? "" : this.lastType.id);
        tag.put("eventData", (Tag)this.eventData);
        return tag;
    }
}

