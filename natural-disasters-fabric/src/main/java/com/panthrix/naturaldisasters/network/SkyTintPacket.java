package com.panthrix.naturaldisasters.network;

import net.minecraft.network.FriendlyByteBuf;

public class SkyTintPacket {
    public final float strength;
    public final int ticks;

    public SkyTintPacket(float strength, int ticks) {
        this.strength = strength;
        this.ticks = ticks;
    }

    public SkyTintPacket(FriendlyByteBuf buf) {
        this.strength = buf.readFloat();
        this.ticks = buf.readVarInt();
    }

    public void encode(FriendlyByteBuf buf) {
        buf.writeFloat(this.strength);
        buf.writeVarInt(this.ticks);
    }

    /** Valores ya limitados para aplicar en el cliente: {fuerza, ticks}. */
    public float clampedStrength() {
        float s = Math.max(0.0f, Math.min(this.strength, 1.0f));
        int t = Math.min(this.ticks, 400);
        return s;
    }

    public int clampedTicks() {
        float s = Math.max(0.0f, Math.min(this.strength, 1.0f));
        int t = Math.min(this.ticks, 400);
        return t;
    }
}
