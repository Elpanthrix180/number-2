package com.panthrix.naturaldisasters.client;

import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.minecraft.client.Minecraft;

@Environment(EnvType.CLIENT)
public final class ClientSkyTint {
    private static final float R = 1.0f;
    private static final float G = 0.45f;
    private static final float B = 0.12f;
    private static float target;
    private static float current;
    private static int ticksLeft;

    private ClientSkyTint() {
    }

    public static void set(float strength, int ticks) {
        target = strength;
        ticksLeft = ticks;
    }

    public static void onClientTick(Minecraft mc) {
        if (mc.isPaused()) {
            return;
        }
        if (ticksLeft > 0) {
            --ticksLeft;
        }
        float goal = ticksLeft > 0 ? target : 0.0f;
        current += (goal - current) * 0.03f;
        if (current < 0.001f && goal == 0.0f) {
            current = 0.0f;
        }
    }

    /** Mezcla el color de la niebla/cielo con naranja. Devuelve null si no hay tinte. */
    public static float[] apply(float red, float green, float blue) {
        if (current <= 0.0f) {
            return null;
        }
        float k = current * 0.75f;
        return new float[]{red + (R - red) * k, green + (G - green) * k, blue + (B - blue) * k};
    }
}
