package com.panthrix.naturaldisasters.worldgen;

import net.fabricmc.fabric.api.biome.v1.BiomeModifications;
import net.fabricmc.fabric.api.biome.v1.BiomeSelectors;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.levelgen.GenerationStep;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.configurations.NoneFeatureConfiguration;
import net.minecraft.world.level.levelgen.placement.PlacedFeature;

public final class ModFeatures {
    public static final ResourceLocation VOLCANO_ID = new ResourceLocation("panthrixsnaturaldisasters", "volcano");
    public static final Feature<NoneFeatureConfiguration> VOLCANO = new VolcanoFeature(NoneFeatureConfiguration.CODEC);
    public static final TagKey<Biome> HAS_VOLCANO = TagKey.create(Registries.BIOME, new ResourceLocation("panthrixsnaturaldisasters", "has_volcano"));
    public static final ResourceKey<PlacedFeature> VOLCANO_PLACED = ResourceKey.create(Registries.PLACED_FEATURE, VOLCANO_ID);

    private ModFeatures() {
    }

    public static void register() {
        Registry.register(BuiltInRegistries.FEATURE, VOLCANO_ID, VOLCANO);
        // Equivale al biome_modifier "forge:add_features" de la version de Forge.
        BiomeModifications.addFeature(BiomeSelectors.tag(HAS_VOLCANO), GenerationStep.Decoration.TOP_LAYER_MODIFICATION, VOLCANO_PLACED);
    }
}
