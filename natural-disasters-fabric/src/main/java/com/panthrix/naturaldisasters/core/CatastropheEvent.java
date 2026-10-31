package com.panthrix.naturaldisasters.core;

import com.panthrix.naturaldisasters.core.CatastrophePhase;
import com.panthrix.naturaldisasters.core.CatastropheSavedData;
import net.minecraft.server.level.ServerLevel;

public abstract class CatastropheEvent {
    public void chooseLocation(ServerLevel level, CatastropheSavedData d) {
    }

    public void onPhaseStart(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase) {
    }

    public void tick(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase, long now) {
    }

    public void onFinish(ServerLevel level, CatastropheSavedData d) {
    }
}

