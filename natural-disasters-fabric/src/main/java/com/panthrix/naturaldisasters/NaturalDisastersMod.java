package com.panthrix.naturaldisasters;

import com.mojang.logging.LogUtils;
import com.panthrix.naturaldisasters.command.CatastropheCommands;
import com.panthrix.naturaldisasters.config.CatastropheConfig;
import com.panthrix.naturaldisasters.core.CatastropheManager;
import com.panthrix.naturaldisasters.core.VolcanoRegistry;
import com.panthrix.naturaldisasters.network.ModNetwork;
import com.panthrix.naturaldisasters.worldgen.ModFeatures;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.loader.api.FabricLoader;
import org.slf4j.Logger;

public class NaturalDisastersMod implements ModInitializer {
    public static final String MOD_ID = "panthrixsnaturaldisasters";
    public static final Logger LOGGER = LogUtils.getLogger();

    public static java.nio.file.Path configFile() {
        return FabricLoader.getInstance().getConfigDir().resolve(MOD_ID + ".json");
    }

    @Override
    public void onInitialize() {
        CatastropheConfig.SPEC.load(configFile());
        ModNetwork.register();
        ModFeatures.register();

        CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> CatastropheCommands.register(dispatcher));

        ServerLifecycleEvents.SERVER_STARTING.register(server -> {
            CatastropheConfig.SPEC.load(configFile());
            LOGGER.info("[Panthrix's Natural Disasters] El servidor esta arrancando. Director de catastrofes listo.");
        });

        ServerTickEvents.END_SERVER_TICK.register(server -> {
            VolcanoRegistry.drainPending(server);
            CatastropheManager.tick(server);
        });

        LOGGER.info("[Panthrix's Natural Disasters] Mod cargado correctamente.");
    }
}
