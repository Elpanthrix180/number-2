package com.panthrix.naturaldisasters.mixin;

import com.mojang.blaze3d.systems.RenderSystem;
import com.panthrix.naturaldisasters.client.ClientSkyTint;
import net.minecraft.client.Camera;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.FogRenderer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Cielo naranja de la lluvia de meteoritos (equivale a ViewportEvent.ComputeFogColor de Forge). */
@Mixin(FogRenderer.class)
public abstract class FogRendererMixin {
    @Shadow private static float fogRed;
    @Shadow private static float fogGreen;
    @Shadow private static float fogBlue;

    @Inject(method = "setupColor", at = @At("TAIL"))
    private static void pnd$tintFog(Camera camera, float partialTick, ClientLevel level, int renderDistance, float darkenWorldAmount, CallbackInfo ci) {
        float[] c = ClientSkyTint.apply(fogRed, fogGreen, fogBlue);
        if (c == null) {
            return;
        }
        fogRed = c[0];
        fogGreen = c[1];
        fogBlue = c[2];
        RenderSystem.clearColor(fogRed, fogGreen, fogBlue, 0.0f);
    }
}
