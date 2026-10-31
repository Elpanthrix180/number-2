package com.panthrix.naturaldisasters.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.panthrix.naturaldisasters.client.ClientShake;
import net.minecraft.client.renderer.GameRenderer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Vibracion de camara de los terremotos (equivale a ViewportEvent.ComputeCameraAngles de Forge). */
@Mixin(GameRenderer.class)
public abstract class GameRendererMixin {
    @Inject(method = "bobHurt", at = @At("TAIL"))
    private void pnd$shakeCamera(PoseStack poseStack, float partialTick, CallbackInfo ci) {
        float[] o = ClientShake.offsets(partialTick);
        if (o == null) {
            return;
        }
        poseStack.mulPose(Axis.ZP.rotationDegrees(o[2]));
        poseStack.mulPose(Axis.XP.rotationDegrees(o[0]));
        poseStack.mulPose(Axis.YP.rotationDegrees(o[1]));
    }
}
