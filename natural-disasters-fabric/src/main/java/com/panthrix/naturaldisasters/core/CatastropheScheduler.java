package com.panthrix.naturaldisasters.core;

import com.panthrix.naturaldisasters.config.CatastropheConfig;
import com.panthrix.naturaldisasters.core.CatastropheType;
import java.util.ArrayList;
import net.minecraft.util.RandomSource;

public final class CatastropheScheduler {
    public static final long TICKS_PER_DAY = 24000L;

    private CatastropheScheduler() {
    }

    public static long minDelayTicks() {
        return (long)((Integer)CatastropheConfig.MIN_DAYS.get()).intValue() * 24000L;
    }

    public static long maxDelayTicks() {
        return (long)Math.max((Integer)CatastropheConfig.MIN_DAYS.get(), (Integer)CatastropheConfig.MAX_DAYS.get()) * 24000L;
    }

    public static long randomDelayTicks(RandomSource random) {
        long min = CatastropheScheduler.minDelayTicks();
        long max = CatastropheScheduler.maxDelayTicks();
        return min + (long)(random.nextDouble() * (double)(max - min));
    }

    public static CatastropheType pickRandom(RandomSource random, CatastropheType last) {
        ArrayList<CatastropheType> candidates = new ArrayList<CatastropheType>();
        for (CatastropheType t : CatastropheType.values()) {
            if (!((Boolean)CatastropheConfig.ENABLED.get((Object)t).get()).booleanValue() || (Integer)CatastropheConfig.WEIGHT.get((Object)t).get() <= 0) continue;
            candidates.add(t);
        }
        if (candidates.size() > 1 && last != null) {
            candidates.remove((Object)last);
        }
        int total = 0;
        for (CatastropheType t : candidates) {
            total += ((Integer)CatastropheConfig.WEIGHT.get((Object)t).get()).intValue();
        }
        if (total <= 0) {
            return null;
        }
        int roll = random.nextInt(total);
        for (CatastropheType t : candidates) {
            if ((roll -= ((Integer)CatastropheConfig.WEIGHT.get((Object)t).get()).intValue()) >= 0) continue;
            return t;
        }
        return (CatastropheType)((Object)candidates.get(candidates.size() - 1));
    }
}

