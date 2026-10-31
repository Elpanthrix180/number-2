package com.panthrix.naturaldisasters.event;

import com.panthrix.naturaldisasters.config.CatastropheConfig;
import com.panthrix.naturaldisasters.core.BlockProtection;
import com.panthrix.naturaldisasters.core.CatastropheEvent;
import com.panthrix.naturaldisasters.core.CatastrophePhase;
import com.panthrix.naturaldisasters.core.CatastropheSavedData;
import com.panthrix.naturaldisasters.event.DisasterUtil;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.level.block.state.properties.Property;
import net.fabricmc.fabric.api.tag.convention.v1.ConventionalBlockTags;

public class HailstormEvent
extends CatastropheEvent {
    private static final BlockParticleOption SMALL_HAIL = new BlockParticleOption(ParticleTypes.FALLING_DUST, Blocks.PACKED_ICE.defaultBlockState());

    @Override
    public void onPhaseStart(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase) {
        switch (phase) {
            case PREPARATION: {
                DisasterUtil.startRain(level, false);
                break;
            }
            case RECOVERY: {
                DisasterUtil.clearWeather(level);
                break;
            }
        }
    }

    /*
     * WARNING - void declaration
     */
    @Override
    public void tick(ServerLevel level, CatastropheSavedData d, CatastrophePhase phase, long now) {
        boolean active;
        if (phase != CatastrophePhase.ACTIVE && phase != CatastrophePhase.ENDING) {
            return;
        }
        double f = CatastropheConfig.intensityFactor();
        boolean bl = active = phase == CatastrophePhase.ACTIVE;
        if (now % 4L == 0L) {
            int count = (int)((double)(active ? 30 : 10) * f);
            for (ServerPlayer p : DisasterUtil.playersInArea(level, d)) {
                level.sendParticles((ParticleOptions)ParticleTypes.ITEM_SNOWBALL, p.getX(), p.getY() + 5.0, p.getZ(), count, 6.0, 1.0, 6.0, 0.05);
                level.sendParticles((ParticleOptions)SMALL_HAIL, p.getX(), p.getY() + 6.0, p.getZ(), count, 7.0, 1.0, 7.0, 0.0);
            }
        }
        if (now % 8L == 0L) {
            for (ServerPlayer serverPlayer : DisasterUtil.playersInArea(level, d)) {
                BlockPos near = serverPlayer.blockPosition().offset(level.getRandom().nextInt(9) - 4, 0, level.getRandom().nextInt(9) - 4);
                level.playSound(null, near, SoundEvents.STONE_PLACE, SoundSource.WEATHER, 0.5f, 1.6f + level.getRandom().nextFloat() * 0.4f);
            }
        }
        if (!active) {
            return;
        }
        if (now % 40L == 0L) {
            float damage = (float)Math.max(1.0, f);
            for (LivingEntity e : DisasterUtil.livingInArea(level, d)) {
                if (!DisasterUtil.canHurt(e) || !DisasterUtil.exposedToSky(level, e) || !e.getItemBySlot(EquipmentSlot.HEAD).isEmpty()) continue;
                e.hurt(level.damageSources().generic(), damage);
            }
        }
        if (now % 20L == 0L && !CatastropheConfig.destructionOff()) {
            void var10_16;
            int tries = 1 + (int)(3.0 * f);
            boolean bl2 = false;
            while (var10_16 < tries) {
                BlockPos pos = DisasterUtil.randomSurface(level, d, level.getRandom());
                if (pos != null) {
                    BlockPos below;
                    BlockState s;
                    if (((Boolean)CatastropheConfig.HAIL_CROPS.get()).booleanValue()) {
                        HailstormEvent.damageCrop(level, d, pos);
                    }
                    if (((Boolean)CatastropheConfig.HAIL_GLASS.get()).booleanValue() && CatastropheConfig.DESTRUCTION.get() == CatastropheConfig.Destruction.INTENSE && ((s = level.getBlockState(below = pos.below())).is(Tags.Blocks.GLASS) || s.is(ConventionalBlockTags.GLASS_PANES) || s.is(Blocks.GLASS_PANE)) && BlockProtection.canModify(level, below, s) && DisasterUtil.takeBlockBudget(d)) {
                        level.destroyBlock(below, false);
                    }
                }
                ++var10_16;
            }
        }
    }

    private static void damageCrop(ServerLevel level, CatastropheSavedData d, BlockPos pos) {
        IntegerProperty age;
        BlockState s = level.getBlockState(pos);
        if (!(s.getBlock() instanceof CropBlock)) {
            return;
        }
        Object object = s.hasProperty((Property)BlockStateProperties.AGE_7) ? BlockStateProperties.AGE_7 : (age = s.hasProperty((Property)BlockStateProperties.AGE_3) ? BlockStateProperties.AGE_3 : null);
        if (age == null || (Integer)s.getValue((Property)age) <= 0 || !BlockProtection.canModify(level, pos, s)) {
            return;
        }
        if (!DisasterUtil.takeBlockBudget(d)) {
            return;
        }
        level.setBlock(pos, (BlockState)s.setValue((Property)age, (Comparable)Integer.valueOf((Integer)s.getValue((Property)age) - 1)), 2);
    }

    @Override
    public void onFinish(ServerLevel level, CatastropheSavedData d) {
        DisasterUtil.clearWeather(level);
    }
}

