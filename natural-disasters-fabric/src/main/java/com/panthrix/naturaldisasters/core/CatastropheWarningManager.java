package com.panthrix.naturaldisasters.core;

import com.panthrix.naturaldisasters.config.CatastropheConfig;
import com.panthrix.naturaldisasters.core.CatastropheType;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;

public final class CatastropheWarningManager {
    private CatastropheWarningManager() {
    }

    public static void announceWarning(MinecraftServer server, CatastropheType type, int x, int z) {
        if (!((Boolean)CatastropheConfig.WARNINGS.get()).booleanValue()) {
            return;
        }
        MutableComponent title = Component.literal((String)type.displayName.toUpperCase()).withStyle(new ChatFormatting[]{ChatFormatting.RED, ChatFormatting.BOLD});
        MutableComponent subtitle = Component.literal((String)type.warningMessage).withStyle(ChatFormatting.GOLD);
        MutableComponent chat = Component.literal((String)"[Catastrofes] ").withStyle(ChatFormatting.DARK_RED).append((Component)Component.literal((String)(type.warningMessage + " Zona: X " + x + ", Z " + z)).withStyle(ChatFormatting.GOLD));
        for (ServerPlayer p : server.getPlayerList().getPlayers()) {
            p.connection.send((Packet)new ClientboundSetTitlesAnimationPacket(10, 70, 20));
            p.connection.send((Packet)new ClientboundSetTitleTextPacket((Component)title));
            p.connection.send((Packet)new ClientboundSetSubtitleTextPacket((Component)subtitle));
            p.sendSystemMessage((Component)chat);
        }
    }

    public static void broadcast(MinecraftServer server, String message, ChatFormatting color) {
        if (!((Boolean)CatastropheConfig.WARNINGS.get()).booleanValue()) {
            return;
        }
        server.getPlayerList().broadcastSystemMessage((Component)Component.literal((String)"[Catastrofes] ").withStyle(ChatFormatting.DARK_RED).append((Component)Component.literal((String)message).withStyle(color)), false);
    }
}

