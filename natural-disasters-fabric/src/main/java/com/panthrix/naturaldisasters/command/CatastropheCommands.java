package com.panthrix.naturaldisasters.command;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.ArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.suggestion.SuggestionsBuilder;
import com.panthrix.naturaldisasters.config.CatastropheConfig;
import com.panthrix.naturaldisasters.core.CatastropheEvents;
import com.panthrix.naturaldisasters.core.CatastropheManager;
import com.panthrix.naturaldisasters.core.CatastrophePhase;
import com.panthrix.naturaldisasters.core.CatastropheSavedData;
import com.panthrix.naturaldisasters.core.CatastropheType;
import com.panthrix.naturaldisasters.core.VolcanoRegistry;
import com.panthrix.naturaldisasters.worldgen.VolcanoBuilder;
import java.util.Arrays;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Position;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.phys.Vec3;

public final class CatastropheCommands {
    private CatastropheCommands() {
    }

    public static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register((LiteralArgumentBuilder)((LiteralArgumentBuilder)((LiteralArgumentBuilder)((LiteralArgumentBuilder)((LiteralArgumentBuilder)((LiteralArgumentBuilder)((LiteralArgumentBuilder)((LiteralArgumentBuilder)((LiteralArgumentBuilder)((LiteralArgumentBuilder)Commands.literal((String)"pnd").executes(CatastropheCommands::help)).then(Commands.literal((String)"help").executes(CatastropheCommands::help))).then(Commands.literal((String)"status").executes(CatastropheCommands::status))).then(Commands.literal((String)"next").executes(CatastropheCommands::next))).then(((LiteralArgumentBuilder)Commands.literal((String)"start").requires(s -> s.hasPermission(2))).then(Commands.argument((String)"fenomeno", (ArgumentType)StringArgumentType.word()).suggests((ctx, builder) -> SharedSuggestionProvider.suggest(Arrays.stream(CatastropheType.values()).map(t -> t.id), (SuggestionsBuilder)builder)).executes(CatastropheCommands::start)))).then(((LiteralArgumentBuilder)Commands.literal((String)"stop").requires(s -> s.hasPermission(2))).executes(CatastropheCommands::stop))).then(((LiteralArgumentBuilder)Commands.literal((String)"enable").requires(s -> s.hasPermission(2))).executes(ctx -> CatastropheCommands.setEnabled((CommandContext<CommandSourceStack>)ctx, true)))).then(((LiteralArgumentBuilder)Commands.literal((String)"disable").requires(s -> s.hasPermission(2))).executes(ctx -> CatastropheCommands.setEnabled((CommandContext<CommandSourceStack>)ctx, false)))).then(((LiteralArgumentBuilder)Commands.literal((String)"config").requires(s -> s.hasPermission(2))).executes(CatastropheCommands::config))).then(((LiteralArgumentBuilder)((LiteralArgumentBuilder)Commands.literal((String)"volcano").requires(s -> s.hasPermission(2))).executes(CatastropheCommands::volcanoInfo)).then(Commands.literal((String)"create").executes(CatastropheCommands::volcanoCreate))));
    }

    private static void reply(CommandContext<CommandSourceStack> ctx, String text, ChatFormatting color) {
        ((CommandSourceStack)ctx.getSource()).sendSuccess(() -> Component.literal((String)text).withStyle(color), false);
    }

    private static String formatTicks(long ticks) {
        if (ticks < 0L) {
            ticks = 0L;
        }
        long days = ticks / 24000L;
        long hours = ticks % 24000L / 1000L;
        long realMinutes = ticks / 1200L;
        return days + " d\u00edas y " + hours + " horas de Minecraft (unos " + realMinutes + " minutos reales)";
    }

    private static int help(CommandContext<CommandSourceStack> ctx) {
        CatastropheCommands.reply(ctx, "=== Panthrix's Natural Disasters ===", ChatFormatting.GOLD);
        CatastropheCommands.reply(ctx, "/pnd help - muestra esta ayuda", ChatFormatting.YELLOW);
        CatastropheCommands.reply(ctx, "/pnd status - estado del sistema y cat\u00e1strofe activa", ChatFormatting.YELLOW);
        CatastropheCommands.reply(ctx, "/pnd next - cu\u00e1ndo ser\u00e1 la pr\u00f3xima cat\u00e1strofe", ChatFormatting.YELLOW);
        CatastropheCommands.reply(ctx, "/pnd start <fen\u00f3meno> - inicia un fen\u00f3meno (admin)", ChatFormatting.YELLOW);
        CatastropheCommands.reply(ctx, "/pnd stop - detiene la cat\u00e1strofe actual (admin)", ChatFormatting.YELLOW);
        CatastropheCommands.reply(ctx, "/pnd enable | disable - activa o desactiva las cat\u00e1strofes aleatorias (admin)", ChatFormatting.YELLOW);
        CatastropheCommands.reply(ctx, "/pnd config - muestra la configuraci\u00f3n (admin)", ChatFormatting.YELLOW);
        CatastropheCommands.reply(ctx, "/pnd volcano - volc\u00e1n conocido m\u00e1s cercano (admin)", ChatFormatting.YELLOW);
        CatastropheCommands.reply(ctx, "/pnd volcano create - crea un volc\u00e1n peque\u00f1o donde est\u00e1s (admin, modifica el terreno)", ChatFormatting.YELLOW);
        StringBuilder ids = new StringBuilder("Fen\u00f3menos: ");
        for (CatastropheType t : CatastropheType.values()) {
            ids.append(t.id).append(' ');
        }
        CatastropheCommands.reply(ctx, ids.toString().trim(), ChatFormatting.GRAY);
        return 1;
    }

    private static int status(CommandContext<CommandSourceStack> ctx) {
        MinecraftServer server = ((CommandSourceStack)ctx.getSource()).getServer();
        CatastropheSavedData d = CatastropheManager.data(server);
        CatastropheCommands.reply(ctx, "Cat\u00e1strofes aleatorias: " + (d.randomEnabled ? "ACTIVADAS" : "DESACTIVADAS"), d.randomEnabled ? ChatFormatting.GREEN : ChatFormatting.RED);
        if (d.phase == CatastrophePhase.CALM) {
            CatastropheCommands.reply(ctx, "Fase: Calma. No hay ninguna cat\u00e1strofe activa.", ChatFormatting.GREEN);
        } else {
            long left = d.phaseEndTick - CatastropheManager.now(server);
            CatastropheCommands.reply(ctx, "Cat\u00e1strofe activa: " + d.activeType.displayName + " en X " + d.centerX + ", Z " + d.centerZ, ChatFormatting.RED);
            CatastropheCommands.reply(ctx, "Fase: " + d.phase.displayName + " (quedan " + Math.max(0L, left / 20L) + " segundos)", ChatFormatting.YELLOW);
        }
        return 1;
    }

    private static int next(CommandContext<CommandSourceStack> ctx) {
        MinecraftServer server = ((CommandSourceStack)ctx.getSource()).getServer();
        CatastropheSavedData d = CatastropheManager.data(server);
        if (!d.randomEnabled) {
            CatastropheCommands.reply(ctx, "Las cat\u00e1strofes aleatorias est\u00e1n desactivadas.", ChatFormatting.RED);
        } else if (d.nextEventTick < 0L) {
            CatastropheCommands.reply(ctx, "La pr\u00f3xima cat\u00e1strofe a\u00fan no est\u00e1 programada.", ChatFormatting.YELLOW);
        } else {
            CatastropheCommands.reply(ctx, "Pr\u00f3xima cat\u00e1strofe dentro de " + CatastropheCommands.formatTicks(d.nextEventTick - CatastropheManager.now(server)) + ".", ChatFormatting.YELLOW);
        }
        return 1;
    }

    private static int start(CommandContext<CommandSourceStack> ctx) {
        String id = StringArgumentType.getString(ctx, (String)"fenomeno");
        CatastropheType type = CatastropheType.byId(id);
        if (type == null) {
            ((CommandSourceStack)ctx.getSource()).sendFailure((Component)Component.literal((String)("Fen\u00f3meno desconocido: " + id + ". Usa /pnd help para ver la lista.")));
            return 0;
        }
        String error = CatastropheManager.start(((CommandSourceStack)ctx.getSource()).getServer(), type);
        if (error != null) {
            ((CommandSourceStack)ctx.getSource()).sendFailure((Component)Component.literal((String)error));
            return 0;
        }
        ((CommandSourceStack)ctx.getSource()).sendSuccess(() -> Component.literal((String)("Iniciado: " + type.displayName)).withStyle(ChatFormatting.GREEN), true);
        if (!CatastropheEvents.isImplemented(type)) {
            CatastropheCommands.reply(ctx, "Aviso: este fen\u00f3meno a\u00fan no tiene efectos (llegar\u00e1 en una fase posterior). Solo se mostrar\u00e1n los avisos.", ChatFormatting.GRAY);
        }
        return 1;
    }

    private static int stop(CommandContext<CommandSourceStack> ctx) {
        if (!CatastropheManager.stop(((CommandSourceStack)ctx.getSource()).getServer())) {
            ((CommandSourceStack)ctx.getSource()).sendFailure((Component)Component.literal((String)"No hay ninguna cat\u00e1strofe activa."));
            return 0;
        }
        ((CommandSourceStack)ctx.getSource()).sendSuccess(() -> Component.literal((String)"Cat\u00e1strofe detenida.").withStyle(ChatFormatting.GREEN), true);
        return 1;
    }

    private static int setEnabled(CommandContext<CommandSourceStack> ctx, boolean enabled) {
        CatastropheManager.setRandomEnabled(((CommandSourceStack)ctx.getSource()).getServer(), enabled);
        ((CommandSourceStack)ctx.getSource()).sendSuccess(() -> Component.literal((String)(enabled ? "Cat\u00e1strofes aleatorias ACTIVADAS." : "Cat\u00e1strofes aleatorias DESACTIVADAS.")).withStyle(ChatFormatting.GREEN), true);
        return 1;
    }

    private static int volcanoInfo(CommandContext<CommandSourceStack> ctx) {
        ServerLevel overworld = ((CommandSourceStack)ctx.getSource()).getServer().overworld();
        VolcanoRegistry reg = VolcanoRegistry.get(overworld);
        Vec3 pos = ((CommandSourceStack)ctx.getSource()).getPosition();
        BlockPos near = reg.nearest((int)pos.x, (int)pos.z, 100000);
        CatastropheCommands.reply(ctx, "Volcanes conocidos: " + reg.size(), ChatFormatting.GOLD);
        if (near != null) {
            CatastropheCommands.reply(ctx, "El m\u00e1s cercano: X " + near.getX() + ", Y " + near.getY() + ", Z " + near.getZ(), ChatFormatting.YELLOW);
        }
        return 1;
    }

    private static int volcanoCreate(CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack src = (CommandSourceStack)ctx.getSource();
        if (src.getLevel() != src.getServer().overworld()) {
            src.sendFailure((Component)Component.literal((String)"Solo se pueden crear volcanes en el mundo normal (Overworld)."));
            return 0;
        }
        BlockPos at = BlockPos.containing((Position)src.getPosition());
        BlockPos crater = VolcanoBuilder.build((WorldGenLevel)src.getLevel(), at, src.getLevel().getRandom(), true);
        if (crater == null) {
            src.sendFailure((Component)Component.literal((String)"Aqu\u00ed no se puede crear un volc\u00e1n (\u00bfhay agua debajo?)."));
            return 0;
        }
        VolcanoRegistry.get(src.getLevel()).add(crater);
        src.sendSuccess(() -> Component.literal((String)("Volc\u00e1n creado. Cr\u00e1ter en X " + crater.getX() + ", Y " + crater.getY() + ", Z " + crater.getZ())).withStyle(ChatFormatting.GREEN), true);
        return 1;
    }

    private static int config(CommandContext<CommandSourceStack> ctx) {
        CatastropheCommands.reply(ctx, "=== Configuraci\u00f3n ===", ChatFormatting.GOLD);
        CatastropheCommands.reply(ctx, "Intervalo: " + String.valueOf(CatastropheConfig.MIN_DAYS.get()) + " a " + String.valueOf(CatastropheConfig.MAX_DAYS.get()) + " d\u00edas", ChatFormatting.YELLOW);
        CatastropheCommands.reply(ctx, "Intensidad: " + String.valueOf(CatastropheConfig.INTENSITY.get()) + " | Destrucci\u00f3n: " + String.valueOf(CatastropheConfig.DESTRUCTION.get()), ChatFormatting.YELLOW);
        CatastropheCommands.reply(ctx, "Radio: " + String.valueOf(CatastropheConfig.RADIUS.get()) + " | M\u00e1x. bloques por evento: " + String.valueOf(CatastropheConfig.MAX_BLOCKS_PER_EVENT.get()), ChatFormatting.YELLOW);
        CatastropheCommands.reply(ctx, "Avisos: " + String.valueOf(CatastropheConfig.WARNINGS.get()) + " | Da\u00f1o a jugadores: " + String.valueOf(CatastropheConfig.DAMAGE_PLAYERS.get()) + " | Da\u00f1o a criaturas: " + String.valueOf(CatastropheConfig.DAMAGE_MOBS.get()), ChatFormatting.YELLOW);
        for (CatastropheType t : CatastropheType.values()) {
            CatastropheCommands.reply(ctx, " - " + t.id + ": " + ((Boolean)CatastropheConfig.ENABLED.get((Object)t).get() != false ? "s\u00ed" : "no") + ", peso " + String.valueOf(CatastropheConfig.WEIGHT.get((Object)t).get()) + ", " + String.valueOf(CatastropheConfig.DURATION_SECONDS.get((Object)t).get()) + " s", ChatFormatting.GRAY);
        }
        CatastropheCommands.reply(ctx, "Archivo: config/panthrixsnaturaldisasters-common.toml", ChatFormatting.GRAY);
        return 1;
    }
}

