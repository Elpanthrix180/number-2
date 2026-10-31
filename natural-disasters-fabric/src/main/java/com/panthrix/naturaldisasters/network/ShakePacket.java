package com.panthrix.naturaldisasters.network;

import net.minecraft.network.FriendlyByteBuf;

public class ShakePacket {
    public final float strength;
    public final int ticks;

    public ShakePacket(float strength, int ticks) {
        this.strength = strength;
        this.ticks = ticks;
    }

    public ShakePacket(FriendlyByteBuf buf) {
        this.strength = buf.readFloat();
        this.ticks = buf.readVarInt();
    }

    public void encode(FriendlyByteBuf buf) {
        buf.writeFloat(this.strength);
        buf.writeVarInt(this.ticks);
    }

    /** Valores ya limitados para aplicar en el cliente: {fuerza, ticks}. */
    public float clampedStrength() {
        float s = Math.min(this.strength, 5.0f);
        int t = Math.min(this.ticks, 200);
        return s;
    }

    public int clampedTicks() {
        float s = Math.min(this.strength, 5.0f);
        int t = Math.min(this.ticks, 200);
        return t;
    }
}
