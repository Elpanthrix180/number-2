package com.panthrix.naturaldisasters.event;

import com.panthrix.naturaldisasters.config.CatastropheConfig;
import com.panthrix.naturaldisasters.core.CatastropheSavedData;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;

public final class DisasterUtil {
    private DisasterUtil() {
    }

    public static int radius() {
        return (Integer)CatastropheConfig.RADIUS.get();
    }

    public static boolean inArea(CatastropheSavedData d, double x, double z) {
        double dx = x - (double)d.centerX;
        double dz = z - (double)d.centerZ;
        int r = DisasterUtil.radius();
        return dx * dx + dz * dz <= (double)r * (double)r;
    }

    public static List<ServerPlayer> playersInArea(ServerLevel level, CatastropheSavedData d) {
        ArrayList<ServerPlayer> result = new ArrayList<ServerPlayer>();
        for (ServerPlayer p : level.players()) {
            if (!DisasterUtil.inArea(d, p.getX(), p.getZ())) continue;
            result.add(p);
        }
        return result;
    }

    public static List<LivingEntity> livingInArea(ServerLevel level, CatastropheSavedData d) {
        int r = DisasterUtil.radius();
        AABB box = new AABB((double)(d.centerX - r), (double)level.getMinBuildHeight(), (double)(d.centerZ - r), (double)(d.centerX + r), (double)level.getMaxBuildHeight(), (double)(d.centerZ + r));
        return level.getEntitiesOfClass(LivingEntity.class, box, e -> e.isAlive() && DisasterUtil.inArea(d, e.getX(), e.getZ()));
    }

    public static boolean canHurt(LivingEntity e) {
        if (e instanceof Player) {
            Player p = (Player)e;
            return (Boolean)CatastropheConfig.DAMAGE_PLAYERS.get() != false && !p.isCreative() && !p.isSpectator();
        }
        return (Boolean)CatastropheConfig.DAMAGE_MOBS.get();
    }

    public static boolean exposedToSky(ServerLevel level, LivingEntity e) {
        return level.canSeeSky(e.blockPosition());
    }

    public static BlockPos randomSurface(ServerLevel level, CatastropheSavedData d, RandomSource random) {
        int z;
        int r = DisasterUtil.radius();
        int x = d.centerX + random.nextInt(2 * r + 1) - r;
        if (!DisasterUtil.inArea(d, x, z = d.centerZ + random.nextInt(2 * r + 1) - r)) {
            return null;
        }
        BlockPos column = new BlockPos(x, d.centerY, z);
        if (!level.isLoaded(column)) {
            return null;
        }
        return level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING, column);
    }

    public static boolean takeBlockBudget(CatastropheSavedData d) {
        return DisasterUtil.takeBlockBudget(d, (Integer)CatastropheConfig.MAX_BLOCKS_PER_EVENT.get());
    }

    public static boolean takeBlockBudget(CatastropheSavedData d, int limit) {
        int used = d.eventData.getInt("blocks");
        if (used >= limit) {
            return false;
        }
        d.eventData.putInt("blocks", used + 1);
        d.setDirty();
        return true;
    }

    public static void clearWeather(ServerLevel level) {
        level.setWeatherParameters(12000, 0, false, false);
    }

    public static void startRain(ServerLevel level, boolean thunder) {
        level.setWeatherParameters(0, 36000, true, thunder);
    }
}

