package com.panthrix.naturaldisasters.mixin;

import com.panthrix.naturaldisasters.event.DroughtEvent;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** La sequia frena el crecimiento de los cultivos (equivale a BlockEvent.CropGrowEvent.Pre de Forge). */
@Mixin(CropBlock.class)
public abstract class CropBlockMixin {
    @Inject(method = "randomTick", at = @At("HEAD"), cancellable = true)
    private void pnd$drought(BlockState state, ServerLevel level, BlockPos pos, RandomSource random, CallbackInfo ci) {
        if (DroughtEvent.shouldBlockGrowth(level, pos)) {
            ci.cancel();
        }
    }
}
