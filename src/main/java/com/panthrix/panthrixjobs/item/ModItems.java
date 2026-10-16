package com.panthrix.panthrixjobs.item;

import com.panthrix.panthrixjobs.PanthrixJobs;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.Item;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

/**
 * Registro de todos los objetos del mod.
 */
public class ModItems {
    public static final DeferredRegister<Item> ITEMS =
            DeferredRegister.create(ForgeRegistries.ITEMS, PanthrixJobs.MOD_ID);

    // ---- Policia ----
    public static final RegistryObject<Item> POLICE_HELMET = armor("police_helmet", ModArmorMaterials.POLICE, ArmorItem.Type.HELMET);
    public static final RegistryObject<Item> POLICE_CHESTPLATE = armor("police_chestplate", ModArmorMaterials.POLICE, ArmorItem.Type.CHESTPLATE);
    public static final RegistryObject<Item> POLICE_LEGGINGS = armor("police_leggings", ModArmorMaterials.POLICE, ArmorItem.Type.LEGGINGS);
    public static final RegistryObject<Item> POLICE_BOOTS = armor("police_boots", ModArmorMaterials.POLICE, ArmorItem.Type.BOOTS);

    // ---- Bombero ----
    public static final RegistryObject<Item> FIREFIGHTER_HELMET = armor("firefighter_helmet", ModArmorMaterials.FIREFIGHTER, ArmorItem.Type.HELMET);
    public static final RegistryObject<Item> FIREFIGHTER_CHESTPLATE = armor("firefighter_chestplate", ModArmorMaterials.FIREFIGHTER, ArmorItem.Type.CHESTPLATE);
    public static final RegistryObject<Item> FIREFIGHTER_LEGGINGS = armor("firefighter_leggings", ModArmorMaterials.FIREFIGHTER, ArmorItem.Type.LEGGINGS);
    public static final RegistryObject<Item> FIREFIGHTER_BOOTS = armor("firefighter_boots", ModArmorMaterials.FIREFIGHTER, ArmorItem.Type.BOOTS);

    private static RegistryObject<Item> armor(String id, ModArmorMaterials material, ArmorItem.Type type) {
        return ITEMS.register(id, () -> new ArmorItem(material, type, new Item.Properties()));
    }

    public static void register(IEventBus eventBus) {
        ITEMS.register(eventBus);
    }
}
