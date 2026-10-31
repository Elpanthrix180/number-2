package com.panthrix.naturaldisasters.core;

import com.panthrix.naturaldisasters.NaturalDisastersMod;
import com.panthrix.naturaldisasters.config.CatastropheConfig;
import com.panthrix.naturaldisasters.core.CatastropheEvent;
import com.panthrix.naturaldisasters.core.CatastropheEvents;
import com.panthrix.naturaldisasters.core.CatastrophePhase;
import com.panthrix.naturaldisasters.core.CatastropheSavedData;
import com.panthrix.naturaldisasters.core.CatastropheScheduler;
import com.panthrix.naturaldisasters.core.CatastropheType;
import com.panthrix.naturaldisasters.core.CatastropheWarningManager;
import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

public final class CatastropheManager {
    private static final long RETRY_TICKS = 1200L;

    private CatastropheManager() {
    }

    public static CatastropheSavedData data(MinecraftServer server) {
        return CatastropheSavedData.get(server.overworld());
    }

    public static long now(MinecraftServer server) {
        return server.overworld().getGameTime();
    }

    public static void tick(MinecraftServer server) {
        CatastropheSavedData d = CatastropheManager.data(server);
        try {
            long now = CatastropheManager.now(server);
            if (d.phase == CatastrophePhase.CALM) {
                CatastropheManager.tickCalm(server, d, now);
            } else {
                CatastropheEvent ev = CatastropheEvents.get(d.activeType);
                if (ev != null) {
                    ev.tick(server.overworld(), d, d.phase, now);
                }
                if (d.phase != CatastrophePhase.CALM && now >= d.phaseEndTick) {
                    CatastropheManager.advancePhase(server, d, now);
                }
            }
        }
        catch (Exception e) {
            NaturalDisastersMod.LOGGER.error("[Panthrix's Natural Disasters] Error en la catastrofe activa; se cancela.", (Throwable)e);
            CatastropheManager.resetToCalm(server, d);
        }
    }

    private static void tickCalm(MinecraftServer server, CatastropheSavedData d, long now) {
        if (!d.randomEnabled) {
            return;
        }
        if (d.nextEventTick < 0L || d.nextEventTick - now > CatastropheScheduler.maxDelayTicks()) {
            CatastropheManager.scheduleNext(server, d);
            return;
        }
        if (now < d.nextEventTick) {
            return;
        }
        CatastropheType type = CatastropheScheduler.pickRandom(server.overworld().getRandom(), d.lastType);
        if (type == null) {
            NaturalDisastersMod.LOGGER.warn("[Panthrix's Natural Disasters] No hay ningun fenomeno activado; no se inicia nada.");
            CatastropheManager.scheduleNext(server, d);
            return;
        }
        if (CatastropheManager.start(server, type) != null) {
            d.nextEventTick = now + 1200L;
            d.setDirty();
        }
    }

    public static String start(MinecraftServer server, CatastropheType type) {
        CatastropheSavedData d = CatastropheManager.data(server);
        if (d.phase != CatastrophePhase.CALM) {
            return "Ya hay una cat\u00e1strofe activa (" + d.activeType.displayName + "). Usa /pnd stop primero.";
        }
        ServerLevel overworld = server.overworld();
        List players = overworld.players();
        if (players.isEmpty()) {
            return "No hay ning\u00fan jugador en el mundo normal (Overworld).";
        }
        ServerPlayer target = (ServerPlayer)players.get(overworld.getRandom().nextInt(players.size()));
        d.activeType = type;
        d.eventData = new CompoundTag();
        d.centerX = target.getBlockX();
        d.centerY = target.getBlockY();
        d.centerZ = target.getBlockZ();
        CatastropheEvent ev = CatastropheEvents.get(type);
        if (ev != null) {
            ev.chooseLocation(overworld, d);
        }
        CatastropheManager.enterPhase(server, d, CatastrophePhase.WARNING, CatastropheManager.now(server));
        NaturalDisastersMod.LOGGER.info("[Panthrix's Natural Disasters] Comienza {} cerca de {} {} {}", new Object[]{type.id, d.centerX, d.centerY, d.centerZ});
        return null;
    }

    public static boolean stop(MinecraftServer server) {
        CatastropheSavedData d = CatastropheManager.data(server);
        if (d.phase == CatastrophePhase.CALM) {
            return false;
        }
        CatastropheWarningManager.broadcast(server, "Un administrador ha detenido la cat\u00e1strofe.", ChatFormatting.GREEN);
        CatastropheManager.resetToCalm(server, d);
        return true;
    }

    public static void setRandomEnabled(MinecraftServer server, boolean enabled) {
        CatastropheSavedData d = CatastropheManager.data(server);
        d.randomEnabled = enabled;
        if (enabled && d.nextEventTick < CatastropheManager.now(server)) {
            CatastropheManager.scheduleNext(server, d);
        }
        d.setDirty();
    }

    public static void scheduleNext(MinecraftServer server, CatastropheSavedData d) {
        d.nextEventTick = CatastropheManager.now(server) + CatastropheScheduler.randomDelayTicks(server.overworld().getRandom());
        d.setDirty();
    }

    private static void advancePhase(MinecraftServer server, CatastropheSavedData d, long now) {
        CatastrophePhase next = d.phase.next();
        if (next == CatastrophePhase.CALM) {
            CatastropheWarningManager.broadcast(server, "La cat\u00e1strofe ha terminado. La zona puede seguir da\u00f1ada.", ChatFormatting.GREEN);
            CatastropheManager.resetToCalm(server, d);
        } else {
            CatastropheManager.enterPhase(server, d, next, now);
        }
    }

    private static void enterPhase(MinecraftServer server, CatastropheSavedData d, CatastrophePhase phase, long now) {
        d.phase = phase;
        d.phaseEndTick = now + CatastropheManager.phaseDurationTicks(d.activeType, phase);
        d.setDirty();
        CatastropheType t = d.activeType;
        switch (phase) {
            case WARNING: {
                CatastropheWarningManager.announceWarning(server, t, d.centerX, d.centerZ);
                break;
            }
            case PREPARATION: {
                CatastropheWarningManager.broadcast(server, "Aparecen las primeras se\u00f1ales: " + t.displayName + ".", ChatFormatting.YELLOW);
                break;
            }
            case ACTIVE: {
                CatastropheWarningManager.broadcast(server, "\u00a1" + t.displayName + " en curso! Buscad refugio.", ChatFormatting.RED);
                break;
            }
            case ENDING: {
                CatastropheWarningManager.broadcast(server, t.displayName + ": el fen\u00f3meno pierde intensidad.", ChatFormatting.YELLOW);
                break;
            }
        }
        CatastropheEvent ev = CatastropheEvents.get(t);
        if (ev != null) {
            ev.onPhaseStart(server.overworld(), d, phase);
        }
    }

    private static void resetToCalm(MinecraftServer server, CatastropheSavedData d) {
        CatastropheEvent ev = CatastropheEvents.get(d.activeType);
        if (ev != null) {
            try {
                ev.onFinish(server.overworld(), d);
            }
            catch (Exception e) {
                NaturalDisastersMod.LOGGER.error("[Panthrix's Natural Disasters] Error al terminar la catastrofe.", (Throwable)e);
            }
        }
        d.eventData = new CompoundTag();
        if (d.activeType != null) {
            d.lastType = d.activeType;
        }
        d.activeType = null;
        d.phase = CatastrophePhase.CALM;
        d.phaseEndTick = 0L;
        CatastropheManager.scheduleNext(server, d);
    }

    public static long phaseDurationTicks(CatastropheType type, CatastrophePhase phase) {
        int seconds = switch (phase) {
            case WARNING -> (Integer)CatastropheConfig.WARNING_SECONDS.get();
            case PREPARATION -> (Integer)CatastropheConfig.PREPARATION_SECONDS.get();
            case ACTIVE -> (Integer)CatastropheConfig.DURATION_SECONDS.get((Object)type).get();
            case ENDING -> (Integer)CatastropheConfig.ENDING_SECONDS.get();
            case RECOVERY -> (Integer)CatastropheConfig.RECOVERY_SECONDS.get();
            case CALM -> 0;
        };
        return (long)seconds * 20L;
    }
}

