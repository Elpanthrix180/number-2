package com.panthrix.naturaldisasters.client;

import com.panthrix.naturaldisasters.network.ModNetwork;
import com.panthrix.naturaldisasters.network.ShakePacket;
import com.panthrix.naturaldisasters.network.SkyTintPacket;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

@Environment(EnvType.CLIENT)
public class NaturalDisastersClient implements ClientModInitializer {
    @Override
    public void onInitializeClient() {
        ClientPlayNetworking.registerGlobalReceiver(ModNetwork.SHAKE, (client, handler, buf, responseSender) -> {
            ShakePacket p = new ShakePacket(buf);
            float s = p.clampedStrength();
            int t = p.clampedTicks();
            client.execute(() -> ClientShake.start(s, t));
        });
        ClientPlayNetworking.registerGlobalReceiver(ModNetwork.SKY_TINT, (client, handler, buf, responseSender) -> {
            SkyTintPacket p = new SkyTintPacket(buf);
            float s = p.clampedStrength();
            int t = p.clampedTicks();
            client.execute(() -> ClientSkyTint.set(s, t));
        });
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            ClientShake.onClientTick(client);
            ClientSkyTint.onClientTick(client);
        });
    }
}
