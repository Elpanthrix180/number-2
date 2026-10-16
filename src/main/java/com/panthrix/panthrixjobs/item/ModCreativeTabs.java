package com.panthrix.panthrixjobs.item;

import com.panthrix.panthrixjobs.PanthrixJobs;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

/**
 * Pestana creativa "Panthrix Jobs". Muestra automaticamente
 * todos los objetos registrados en ModItems, en el orden en que se registran.
 */
public class ModCreativeTabs {
    public static final DeferredRegister<CreativeModeTab> CREATIVE_TABS =
            DeferredRegister.create(Registries.CREATIVE_MODE_TAB, PanthrixJobs.MOD_ID);

    public static final RegistryObject<CreativeModeTab> PANTHRIX_JOBS_TAB = CREATIVE_TABS.register("panthrix_jobs",
            () -> CreativeModeTab.builder()
                    .title(Component.translatable("itemGroup.panthrixjobs"))
                    .icon(() -> new ItemStack(ModItems.POLICE_HELMET.get()))
                    .displayItems((parameters, output) ->
                            ModItems.ITEMS.getEntries().forEach(item -> output.accept(item.get())))
                    .build());

    public static void register(IEventBus eventBus) {
        CREATIVE_TABS.register(eventBus);
    }
}
