package com.panthrix.naturaldisasters.core;

import com.panthrix.naturaldisasters.core.CatastropheEvent;
import com.panthrix.naturaldisasters.core.CatastropheType;
import com.panthrix.naturaldisasters.event.BlackHoleEvent;
import com.panthrix.naturaldisasters.event.BlizzardEvent;
import com.panthrix.naturaldisasters.event.DroughtEvent;
import com.panthrix.naturaldisasters.event.EarthquakeEvent;
import com.panthrix.naturaldisasters.event.ExtremeThunderstormEvent;
import com.panthrix.naturaldisasters.event.FloodEvent;
import com.panthrix.naturaldisasters.event.GroundCrackEvent;
import com.panthrix.naturaldisasters.event.HailstormEvent;
import com.panthrix.naturaldisasters.event.LandslideEvent;
import com.panthrix.naturaldisasters.event.MeteorShowerEvent;
import com.panthrix.naturaldisasters.event.TornadoEvent;
import com.panthrix.naturaldisasters.event.VolcanoEvent;
import java.util.EnumMap;
import java.util.Map;

public final class CatastropheEvents {
    private static final Map<CatastropheType, CatastropheEvent> EVENTS = new EnumMap<CatastropheType, CatastropheEvent>(CatastropheType.class);

    private CatastropheEvents() {
    }

    public static CatastropheEvent get(CatastropheType type) {
        return type == null ? null : EVENTS.get((Object)type);
    }

    public static boolean isImplemented(CatastropheType type) {
        return EVENTS.containsKey((Object)type);
    }

    static {
        EVENTS.put(CatastropheType.BLIZZARD, new BlizzardEvent());
        EVENTS.put(CatastropheType.THUNDERSTORM, new ExtremeThunderstormEvent());
        EVENTS.put(CatastropheType.HAILSTORM, new HailstormEvent());
        EVENTS.put(CatastropheType.DROUGHT, new DroughtEvent());
        EVENTS.put(CatastropheType.TORNADO, new TornadoEvent());
        EVENTS.put(CatastropheType.FLOOD, new FloodEvent());
        EVENTS.put(CatastropheType.EARTHQUAKE, new EarthquakeEvent());
        EVENTS.put(CatastropheType.VOLCANO, new VolcanoEvent());
        EVENTS.put(CatastropheType.LANDSLIDE, new LandslideEvent());
        EVENTS.put(CatastropheType.METEOR_SHOWER, new MeteorShowerEvent());
        EVENTS.put(CatastropheType.BLACK_HOLE, new BlackHoleEvent());
        EVENTS.put(CatastropheType.GROUND_CRACKS, new GroundCrackEvent());
    }
}

