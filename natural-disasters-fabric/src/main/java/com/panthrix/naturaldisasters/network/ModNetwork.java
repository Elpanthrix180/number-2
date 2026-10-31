package com.panthrix.naturaldisasters.network;

import io.netty.buffer.Unpooled;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;

public final class ModNetwork {
    public static final ResourceLocation SHAKE = new ResourceLocation("panthrixsnaturaldisasters", "shake");
    public static final ResourceLocation SKY_TINT = new ResourceLocation("panthrixsnaturaldisasters", "sky_tint");

    private ModNetwork() {
    }

    public static void register() {
        // Los paquetes solo van del servidor al cliente; el cliente registra sus receptores en NaturalDisastersClient.
    }

    public static void sendSkyTint(ServerPlayer player, float strength, int ticks) {
        if (ServerPlayNetworking.canSend(player, SKY_TINT)) {
            FriendlyByteBuf buf = new FriendlyByteBuf(Unpooled.buffer());
            new SkyTintPacket(strength, ticks).encode(buf);
            ServerPlayNetworking.send(player, SKY_TINT, buf);
        }
    }

    public static void sendShake(ServerPlayer player, float strength, int ticks) {
        if (ServerPlayNetworking.canSend(player, SHAKE)) {
            FriendlyByteBuf buf = new FriendlyByteBuf(Unpooled.buffer());
            new ShakePacket(strength, ticks).encode(buf);
            ServerPlayNetworking.send(player, SHAKE, buf);
        }
    }
}
