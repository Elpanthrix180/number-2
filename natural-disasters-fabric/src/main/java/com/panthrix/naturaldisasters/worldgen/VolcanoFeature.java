package com.panthrix.naturaldisasters.worldgen;

import com.mojang.serialization.Codec;
import com.panthrix.naturaldisasters.config.CatastropheConfig;
import com.panthrix.naturaldisasters.core.VolcanoRegistry;
import com.panthrix.naturaldisasters.worldgen.VolcanoBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.FeaturePlaceContext;
import net.minecraft.world.level.levelgen.feature.configurations.NoneFeatureConfiguration;

public class VolcanoFeature
extends Feature<NoneFeatureConfiguration> {
    public VolcanoFeature(Codec<NoneFeatureConfiguration> codec) {
        super(codec);
    }

    public boolean place(FeaturePlaceContext<NoneFeatureConfiguration> ctx) {
        if (!((Boolean)CatastropheConfig.VOLCANO_NATURAL.get()).booleanValue()) {
            return false;
        }
        WorldGenLevel level = ctx.level();
        if (level.getLevel().dimension() != Level.OVERWORLD) {
            return false;
        }
        RandomSource r = ctx.random();
        if (r.nextInt(((Integer)CatastropheConfig.VOLCANO_RARITY.get()).intValue()) != 0) {
            return false;
        }
        BlockPos origin = ctx.origin();
        BlockPos center = new BlockPos((origin.getX() & 0xFFFFFFF0) + 8, 0, (origin.getZ() & 0xFFFFFFF0) + 8);
        if (VolcanoFeature.looksBuilt(level, center)) {
            return false;
        }
        BlockPos crater = VolcanoBuilder.build(level, center, r, false);
        if (crater == null) {
            return false;
        }
        VolcanoRegistry.queue(crater);
        return true;
    }

    private static boolean looksBuilt(WorldGenLevel level, BlockPos center) {
        for (int dx = -12; dx <= 12; dx += 4) {
            for (int dz = -12; dz <= 12; dz += 4) {
                int z;
                int y;
                int x = center.getX() + dx;
                BlockState s = level.getBlockState(new BlockPos(x, y = level.getHeight(Heightmap.Types.WORLD_SURFACE_WG, x, z = center.getZ() + dz) - 1, z));
                if (!s.hasBlockEntity() && !s.is(BlockTags.PLANKS) && !s.is(BlockTags.STAIRS) && !s.is(BlockTags.SLABS) && !s.is(BlockTags.WOOL) && !s.is(BlockTags.BEDS) && !s.is(BlockTags.DOORS) && !s.is(BlockTags.FENCES)) continue;
                return true;
            }
        }
        return false;
    }
}

