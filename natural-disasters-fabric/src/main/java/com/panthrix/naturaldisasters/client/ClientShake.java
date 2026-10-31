package com.panthrix.naturaldisasters.client;

import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.minecraft.client.Minecraft;

@Environment(EnvType.CLIENT)
public final class ClientShake {
    private static float strength;
    private static int ticksLeft;
    private static int age;

    private ClientShake() {
    }

    public static void start(float s, int ticks) {
        strength = Math.max(strength * (float)(ticksLeft > 0 ? 1 : 0), s);
        ticksLeft = Math.max(ticksLeft, ticks);
    }

    public static void onClientTick(Minecraft mc) {
        if (mc.isPaused()) {
            return;
        }
        ++age;
        if (ticksLeft > 0 && --ticksLeft == 0) {
            strength = 0.0f;
        }
    }

    /** Devuelve {pitch, yaw, roll} extra en grados, o null si no hay vibracion. */
    public static float[] offsets(float partialTick) {
        if (ticksLeft <= 0 || strength <= 0.0f) {
            return null;
        }
        double t = (double)age + partialTick;
        float fade = Math.min(1.0f, (float)ticksLeft / 10.0f);
        float s = strength * fade;
        return new float[]{
            (float)(Math.sin(t * 1.9) * (double)s),
            (float)(Math.sin(t * 1.3 + 1.0) * (double)s * 0.6),
            (float)(Math.sin(t * 2.3 + 2.0) * (double)s * 0.8)
        };
    }
}
