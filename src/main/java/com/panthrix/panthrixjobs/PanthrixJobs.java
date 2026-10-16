package com.panthrix.panthrixjobs;

import com.mojang.logging.LogUtils;
import com.panthrix.panthrixjobs.item.ModItems;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import org.slf4j.Logger;

/**
 * Clase principal del mod Panthrix Jobs.
 * Forge la encuentra gracias a la anotacion @Mod y al MOD_ID.
 */
@Mod(PanthrixJobs.MOD_ID)
public class PanthrixJobs {
    public static final String MOD_ID = "panthrixjobs";
    private static final Logger LOGGER = LogUtils.getLogger();

    public PanthrixJobs() {
        IEventBus modEventBus = FMLJavaModLoadingContext.get().getModEventBus();
        ModItems.register(modEventBus);
        LOGGER.info("Panthrix Jobs: Disfraces de Empleos se ha cargado correctamente.");
    }
}
