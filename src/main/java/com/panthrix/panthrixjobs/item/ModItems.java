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

    // ---- Medico ----
    public static final RegistryObject<Item> DOCTOR_HELMET = armor("doctor_helmet", ModArmorMaterials.DOCTOR, ArmorItem.Type.HELMET);
    public static final RegistryObject<Item> DOCTOR_CHESTPLATE = armor("doctor_chestplate", ModArmorMaterials.DOCTOR, ArmorItem.Type.CHESTPLATE);
    public static final RegistryObject<Item> DOCTOR_LEGGINGS = armor("doctor_leggings", ModArmorMaterials.DOCTOR, ArmorItem.Type.LEGGINGS);
    public static final RegistryObject<Item> DOCTOR_BOOTS = armor("doctor_boots", ModArmorMaterials.DOCTOR, ArmorItem.Type.BOOTS);

    // ---- Obrero de construccion ----
    public static final RegistryObject<Item> BUILDER_HELMET = armor("builder_helmet", ModArmorMaterials.BUILDER, ArmorItem.Type.HELMET);
    public static final RegistryObject<Item> BUILDER_CHESTPLATE = armor("builder_chestplate", ModArmorMaterials.BUILDER, ArmorItem.Type.CHESTPLATE);
    public static final RegistryObject<Item> BUILDER_LEGGINGS = armor("builder_leggings", ModArmorMaterials.BUILDER, ArmorItem.Type.LEGGINGS);
    public static final RegistryObject<Item> BUILDER_BOOTS = armor("builder_boots", ModArmorMaterials.BUILDER, ArmorItem.Type.BOOTS);

    // ---- Piloto de avion ----
    public static final RegistryObject<Item> PILOT_HELMET = armor("pilot_helmet", ModArmorMaterials.PILOT, ArmorItem.Type.HELMET);
    public static final RegistryObject<Item> PILOT_CHESTPLATE = armor("pilot_chestplate", ModArmorMaterials.PILOT, ArmorItem.Type.CHESTPLATE);
    public static final RegistryObject<Item> PILOT_LEGGINGS = armor("pilot_leggings", ModArmorMaterials.PILOT, ArmorItem.Type.LEGGINGS);
    public static final RegistryObject<Item> PILOT_BOOTS = armor("pilot_boots", ModArmorMaterials.PILOT, ArmorItem.Type.BOOTS);

    // ---- Conductor de autobus ----
    public static final RegistryObject<Item> BUS_DRIVER_HELMET = armor("bus_driver_helmet", ModArmorMaterials.BUS_DRIVER, ArmorItem.Type.HELMET);
    public static final RegistryObject<Item> BUS_DRIVER_CHESTPLATE = armor("bus_driver_chestplate", ModArmorMaterials.BUS_DRIVER, ArmorItem.Type.CHESTPLATE);
    public static final RegistryObject<Item> BUS_DRIVER_LEGGINGS = armor("bus_driver_leggings", ModArmorMaterials.BUS_DRIVER, ArmorItem.Type.LEGGINGS);
    public static final RegistryObject<Item> BUS_DRIVER_BOOTS = armor("bus_driver_boots", ModArmorMaterials.BUS_DRIVER, ArmorItem.Type.BOOTS);

    // ---- Maquinista de tren ----
    public static final RegistryObject<Item> TRAIN_DRIVER_HELMET = armor("train_driver_helmet", ModArmorMaterials.TRAIN_DRIVER, ArmorItem.Type.HELMET);
    public static final RegistryObject<Item> TRAIN_DRIVER_CHESTPLATE = armor("train_driver_chestplate", ModArmorMaterials.TRAIN_DRIVER, ArmorItem.Type.CHESTPLATE);
    public static final RegistryObject<Item> TRAIN_DRIVER_LEGGINGS = armor("train_driver_leggings", ModArmorMaterials.TRAIN_DRIVER, ArmorItem.Type.LEGGINGS);
    public static final RegistryObject<Item> TRAIN_DRIVER_BOOTS = armor("train_driver_boots", ModArmorMaterials.TRAIN_DRIVER, ArmorItem.Type.BOOTS);

    // ---- Mecanico ----
    public static final RegistryObject<Item> MECHANIC_HELMET = armor("mechanic_helmet", ModArmorMaterials.MECHANIC, ArmorItem.Type.HELMET);
    public static final RegistryObject<Item> MECHANIC_CHESTPLATE = armor("mechanic_chestplate", ModArmorMaterials.MECHANIC, ArmorItem.Type.CHESTPLATE);
    public static final RegistryObject<Item> MECHANIC_LEGGINGS = armor("mechanic_leggings", ModArmorMaterials.MECHANIC, ArmorItem.Type.LEGGINGS);
    public static final RegistryObject<Item> MECHANIC_BOOTS = armor("mechanic_boots", ModArmorMaterials.MECHANIC, ArmorItem.Type.BOOTS);

    // ---- Cartero ----
    public static final RegistryObject<Item> MAIL_CARRIER_HELMET = armor("mail_carrier_helmet", ModArmorMaterials.MAIL_CARRIER, ArmorItem.Type.HELMET);
    public static final RegistryObject<Item> MAIL_CARRIER_CHESTPLATE = armor("mail_carrier_chestplate", ModArmorMaterials.MAIL_CARRIER, ArmorItem.Type.CHESTPLATE);
    public static final RegistryObject<Item> MAIL_CARRIER_LEGGINGS = armor("mail_carrier_leggings", ModArmorMaterials.MAIL_CARRIER, ArmorItem.Type.LEGGINGS);
    public static final RegistryObject<Item> MAIL_CARRIER_BOOTS = armor("mail_carrier_boots", ModArmorMaterials.MAIL_CARRIER, ArmorItem.Type.BOOTS);

    // ---- Cocinero ----
    public static final RegistryObject<Item> CHEF_HELMET = armor("chef_helmet", ModArmorMaterials.CHEF, ArmorItem.Type.HELMET);
    public static final RegistryObject<Item> CHEF_CHESTPLATE = armor("chef_chestplate", ModArmorMaterials.CHEF, ArmorItem.Type.CHESTPLATE);
    public static final RegistryObject<Item> CHEF_LEGGINGS = armor("chef_leggings", ModArmorMaterials.CHEF, ArmorItem.Type.LEGGINGS);
    public static final RegistryObject<Item> CHEF_BOOTS = armor("chef_boots", ModArmorMaterials.CHEF, ArmorItem.Type.BOOTS);

    // ---- Granjero ----
    public static final RegistryObject<Item> FARMER_HELMET = armor("farmer_helmet", ModArmorMaterials.FARMER, ArmorItem.Type.HELMET);
    public static final RegistryObject<Item> FARMER_CHESTPLATE = armor("farmer_chestplate", ModArmorMaterials.FARMER, ArmorItem.Type.CHESTPLATE);
    public static final RegistryObject<Item> FARMER_LEGGINGS = armor("farmer_leggings", ModArmorMaterials.FARMER, ArmorItem.Type.LEGGINGS);
    public static final RegistryObject<Item> FARMER_BOOTS = armor("farmer_boots", ModArmorMaterials.FARMER, ArmorItem.Type.BOOTS);

    // ---- Marinero ----
    public static final RegistryObject<Item> SAILOR_HELMET = armor("sailor_helmet", ModArmorMaterials.SAILOR, ArmorItem.Type.HELMET);
    public static final RegistryObject<Item> SAILOR_CHESTPLATE = armor("sailor_chestplate", ModArmorMaterials.SAILOR, ArmorItem.Type.CHESTPLATE);
    public static final RegistryObject<Item> SAILOR_LEGGINGS = armor("sailor_leggings", ModArmorMaterials.SAILOR, ArmorItem.Type.LEGGINGS);
    public static final RegistryObject<Item> SAILOR_BOOTS = armor("sailor_boots", ModArmorMaterials.SAILOR, ArmorItem.Type.BOOTS);

    // ---- Agricultor ----
    public static final RegistryObject<Item> AGRICULTURIST_HELMET = armor("agriculturist_helmet", ModArmorMaterials.AGRICULTURIST, ArmorItem.Type.HELMET);
    public static final RegistryObject<Item> AGRICULTURIST_CHESTPLATE = armor("agriculturist_chestplate", ModArmorMaterials.AGRICULTURIST, ArmorItem.Type.CHESTPLATE);
    public static final RegistryObject<Item> AGRICULTURIST_LEGGINGS = armor("agriculturist_leggings", ModArmorMaterials.AGRICULTURIST, ArmorItem.Type.LEGGINGS);
    public static final RegistryObject<Item> AGRICULTURIST_BOOTS = armor("agriculturist_boots", ModArmorMaterials.AGRICULTURIST, ArmorItem.Type.BOOTS);

    private static RegistryObject<Item> armor(String id, ModArmorMaterials material, ArmorItem.Type type) {
        return ITEMS.register(id, () -> new ArmorItem(material, type, new Item.Properties()));
    }

    public static void register(IEventBus eventBus) {
        ITEMS.register(eventBus);
    }
}
