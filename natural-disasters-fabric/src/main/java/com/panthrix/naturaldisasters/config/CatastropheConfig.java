package com.panthrix.naturaldisasters.config;

import com.panthrix.naturaldisasters.core.CatastropheType;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;

public final class CatastropheConfig {
    public static final ConfigSpec SPEC;
    public static final ConfigSpec.IntValue MIN_DAYS;
    public static final ConfigSpec.IntValue MAX_DAYS;
    public static final ConfigSpec.BooleanValue WARNINGS;
    public static final ConfigSpec.BooleanValue ALLOW_SIMULTANEOUS;
    public static final ConfigSpec.EnumValue<Intensity> INTENSITY;
    public static final ConfigSpec.EnumValue<Destruction> DESTRUCTION;
    public static final ConfigSpec.IntValue RADIUS;
    public static final ConfigSpec.IntValue MAX_BLOCKS_PER_EVENT;
    public static final ConfigSpec.BooleanValue DAMAGE_PLAYERS;
    public static final ConfigSpec.BooleanValue DAMAGE_MOBS;
    public static final ConfigSpec.IntValue WARNING_SECONDS;
    public static final ConfigSpec.IntValue PREPARATION_SECONDS;
    public static final ConfigSpec.IntValue ENDING_SECONDS;
    public static final ConfigSpec.IntValue RECOVERY_SECONDS;
    public static final ConfigSpec.BooleanValue SNOW_ACCUMULATION;
    public static final ConfigSpec.BooleanValue SNOW_TEMPORARY;
    public static final ConfigSpec.BooleanValue FREEZING;
    public static final ConfigSpec.BooleanValue LIGHTNING_FIRES;
    public static final ConfigSpec.BooleanValue HAIL_CROPS;
    public static final ConfigSpec.BooleanValue HAIL_GLASS;
    public static final ConfigSpec.BooleanValue DROUGHT_CROPS;
    public static final ConfigSpec.BooleanValue DROUGHT_DRY_FARMLAND;
    public static final ConfigSpec.DoubleValue TORNADO_SPEED;
    public static final ConfigSpec.IntValue TORNADO_PULL_RADIUS;
    public static final ConfigSpec.BooleanValue TORNADO_LIFTS_BLOCKS;
    public static final ConfigSpec.BooleanValue TORNADO_UPROOTS_TREES;
    public static final ConfigSpec.IntValue FLOOD_HEIGHT;
    public static final ConfigSpec.IntValue FLOOD_RADIUS;
    public static final ConfigSpec.BooleanValue FLOOD_TEMPORARY;
    public static final ConfigSpec.BooleanValue FLOOD_CURRENTS;
    public static final ConfigSpec.IntValue QUAKE_CRACK_DEPTH;
    public static final ConfigSpec.IntValue QUAKE_CRACK_LENGTH;
    public static final ConfigSpec.IntValue QUAKE_CRACK_WIDTH;
    public static final ConfigSpec.IntValue QUAKE_CRACK_COUNT;
    public static final ConfigSpec.BooleanValue QUAKE_CAVES;
    public static final ConfigSpec.BooleanValue QUAKE_COLLAPSES;
    public static final ConfigSpec.BooleanValue QUAKE_BUILDING_DAMAGE;
    public static final ConfigSpec.BooleanValue QUAKE_CAMERA_SHAKE;
    public static final ConfigSpec.IntValue QUAKE_BLOCKS_PER_TICK;
    public static final ConfigSpec.BooleanValue VOLCANO_NATURAL;
    public static final ConfigSpec.IntValue VOLCANO_RARITY;
    public static final ConfigSpec.BooleanValue VOLCANO_CREATE_IF_NONE;
    public static final ConfigSpec.IntValue VOLCANO_SEARCH_RADIUS;
    public static final ConfigSpec.IntValue VOLCANO_DANGER_RADIUS;
    public static final ConfigSpec.BooleanValue VOLCANO_BOMBS;
    public static final ConfigSpec.BooleanValue VOLCANO_LAVA_FLOWS;
    public static final ConfigSpec.BooleanValue VOLCANO_LAVA_TEMPORARY;
    public static final ConfigSpec.IntValue SLIDE_RADIUS;
    public static final ConfigSpec.IntValue SLIDE_MAX_BLOCKS;
    public static final ConfigSpec.IntValue SLIDE_DEPTH;
    public static final ConfigSpec.BooleanValue SLIDE_BUILDINGS;
    public static final ConfigSpec.IntValue METEORS_PER_MINUTE;
    public static final ConfigSpec.IntValue METEOR_CRATER_RADIUS;
    public static final ConfigSpec.BooleanValue METEOR_ORES;
    public static final ConfigSpec.IntValue METEOR_MAX_BLOCKS;
    public static final ConfigSpec.IntValue METEOR_BALL_RADIUS;
    public static final ConfigSpec.BooleanValue METEOR_SKY_TINT;
    public static final ConfigSpec.IntValue METEOR_BLOCKS_PER_TICK;
    public static final ConfigSpec.IntValue BLACK_HOLE_MAX_BLOCKS;
    public static final ConfigSpec.IntValue BLACK_HOLE_PULL_RADIUS;
    public static final ConfigSpec.IntValue BLACK_HOLE_MAX_RADIUS;
    public static final ConfigSpec.IntValue BLACK_HOLE_HEIGHT;
    public static final ConfigSpec.BooleanValue BLACK_HOLE_CONSUMES_ITEMS;
    public static final ConfigSpec.IntValue CRACKS_COUNT;
    public static final ConfigSpec.IntValue CRACKS_LENGTH;
    public static final ConfigSpec.IntValue CRACKS_DEPTH;
    public static final ConfigSpec.IntValue CRACKS_WIDTH;
    public static final ConfigSpec.IntValue CRACKS_SPEED;
    public static final ConfigSpec.BooleanValue CRACKS_BRANCHES;
    public static final ConfigSpec.BooleanValue CRACKS_LAVA;
    public static final ConfigSpec.IntValue CRACKS_MAX_BLOCKS;
    public static final ConfigSpec.ListValue PROTECTED_BLOCKS;
    public static final ConfigSpec.ListValue PROTECTED_ZONES;
    public static final Map<CatastropheType, ConfigSpec.BooleanValue> ENABLED;
    public static final Map<CatastropheType, ConfigSpec.IntValue> WEIGHT;
    public static final Map<CatastropheType, ConfigSpec.IntValue> DURATION_SECONDS;

    public static double intensityFactor() {
        return switch (INTENSITY.get()) {
            case SOFT -> 0.5;
            case MODERATE -> 1.0;
            case EXTREME -> 2.0;
        };
    }

    public static boolean destructionOff() {
        return DESTRUCTION.get() == Destruction.OFF;
    }

    private CatastropheConfig() {
    }

    static {
        ENABLED = new EnumMap<CatastropheType, ConfigSpec.BooleanValue>(CatastropheType.class);
        WEIGHT = new EnumMap<CatastropheType, ConfigSpec.IntValue>(CatastropheType.class);
        DURATION_SECONDS = new EnumMap<CatastropheType, ConfigSpec.IntValue>(CatastropheType.class);
        ConfigSpec.Builder b = new ConfigSpec.Builder();
        b.comment("Calendario de catastrofes (1 dia de Minecraft = 24000 ticks = 20 minutos reales)").push("calendario");
        MIN_DAYS = b.comment("Dias minimos entre catastrofes").defineInRange("diasMinimos", 5, 1, 1000);
        MAX_DAYS = b.comment("Dias maximos entre catastrofes (si es menor que el minimo, se usa el minimo)").defineInRange("diasMaximos", 20, 1, 1000);
        b.pop();
        b.comment("Opciones generales").push("general");
        WARNINGS = b.comment("Mostrar avisos de emergencia a los jugadores").define("avisos", true);
        ALLOW_SIMULTANEOUS = b.comment("Permitir varias catastrofes a la vez (aun no implementado: siempre hay como maximo una)").define("eventosSimultaneos", false);
        INTENSITY = b.comment("Intensidad: SOFT (suave), MODERATE (moderada), EXTREME (extrema)").defineEnum("intensidad", Intensity.MODERATE);
        DESTRUCTION = b.comment("Destruccion del terreno: OFF (desactivada), PARTIAL (parcial), INTENSE (intensa; puede afectar al rendimiento)").defineEnum("destruccion", Destruction.OFF);
        RADIUS = b.comment("Radio de los eventos en bloques").defineInRange("radio", 32, 8, 128);
        MAX_BLOCKS_PER_EVENT = b.comment("Maximo de bloques que un evento puede modificar").defineInRange("maxBloquesPorEvento", 1000, 0, 20000);
        DAMAGE_PLAYERS = b.comment("Los fenomenos pueden hacer dano a los jugadores").define("danoJugadores", true);
        DAMAGE_MOBS = b.comment("Los fenomenos pueden hacer dano a las criaturas").define("danoCriaturas", true);
        b.pop();
        b.comment("Duracion de las fases comunes, en segundos reales").push("fases");
        WARNING_SECONDS = b.defineInRange("segundosAviso", 30, 5, 600);
        PREPARATION_SECONDS = b.defineInRange("segundosPreparacion", 20, 0, 600);
        ENDING_SECONDS = b.defineInRange("segundosFinalizacion", 20, 0, 600);
        RECOVERY_SECONDS = b.defineInRange("segundosRecuperacion", 10, 0, 600);
        b.pop();
        b.comment("Fenomenos meteorologicos").push("meteorologia");
        SNOW_ACCUMULATION = b.comment("Ventisca: acumular capas de nieve en el suelo (cuenta para maxBloquesPorEvento)").define("acumularNieve", false);
        SNOW_TEMPORARY = b.comment("Ventisca: retirar la nieve acumulada al terminar").define("nieveTemporal", true);
        FREEZING = b.comment("Ventisca: congelar a los jugadores expuestos al cielo (necesita danoJugadores)").define("congelacion", true);
        LIGHTNING_FIRES = b.comment("Tormenta: los rayos pueden provocar incendios (necesita destruccion distinta de OFF)").define("incendiosPorRayos", false);
        HAIL_CROPS = b.comment("Granizada: dana los cultivos, reduce su crecimiento (necesita destruccion distinta de OFF)").define("granizoDanaCultivos", true);
        HAIL_GLASS = b.comment("Granizada: rompe cristales expuestos (solo con destruccion INTENSE)").define("granizoRompeCristales", false);
        DROUGHT_CROPS = b.comment("Sequia: los cultivos de la zona crecen mas despacio (efecto temporal)").define("sequiaFrenaCultivos", true);
        DROUGHT_DRY_FARMLAND = b.comment("Sequia: seca la tierra de cultivo (necesita destruccion distinta de OFF)").define("sequiaSecaTierras", false);
        b.pop();
        b.comment("Tornados").push("tornado");
        TORNADO_SPEED = b.comment("Velocidad de desplazamiento en bloques por segundo").defineInRange("velocidad", 2.0, 0.0, 10.0);
        TORNADO_PULL_RADIUS = b.comment("Radio en el que atrae a jugadores y criaturas").defineInRange("radioAtraccion", 8, 2, 24);
        TORNADO_LIFTS_BLOCKS = b.comment("Levantar tierra, arena, grava, hojas y plantas (necesita destruccion distinta de OFF)").define("levantaBloques", true);
        TORNADO_UPROOTS_TREES = b.comment("Arrancar troncos de arboles (solo con destruccion INTENSE)").define("arrancaArboles", false);
        b.pop();
        b.comment("Inundaciones (colocar agua necesita destruccion distinta de OFF)").push("inundacion");
        FLOOD_HEIGHT = b.comment("Cuantos bloques sube el agua como maximo").defineInRange("alturaMaxima", 3, 1, 10);
        FLOOD_RADIUS = b.comment("Radio de la zona inundada (nunca mayor que 'radio')").defineInRange("radioInundacion", 24, 4, 64);
        FLOOD_TEMPORARY = b.comment("Retirar el agua al terminar").define("aguaTemporal", true);
        FLOOD_CURRENTS = b.comment("Corrientes que arrastran a quien este en el agua").define("corrientes", true);
        b.pop();
        b.comment("Terremotos (las grietas, cuevas y derrumbes necesitan destruccion distinta de OFF)").push("terremoto");
        QUAKE_CRACK_DEPTH = b.comment("Profundidad maxima de las grietas en bloques").defineInRange("profundidadGrietas", 12, 2, 40);
        QUAKE_CRACK_LENGTH = b.comment("Longitud maxima de las grietas en bloques").defineInRange("longitudGrietas", 24, 5, 64);
        QUAKE_CRACK_WIDTH = b.comment("Anchura maxima de las grietas en bloques").defineInRange("anchoGrietas", 3, 1, 7);
        QUAKE_CRACK_COUNT = b.comment("Numero de grietas (con destruccion INTENSE se suman zanjas anchas)").defineInRange("numeroGrietas", 2, 1, 8);
        QUAKE_CAVES = b.comment("Abrir cuevas nuevas bajo tierra (solo con destruccion INTENSE)").define("cuevasNuevas", true);
        QUAKE_COLLAPSES = b.comment("Derrumbes de tierra y piedra en los bordes de las grietas").define("derrumbes", true);
        QUAKE_BUILDING_DAMAGE = b.comment("Hacer caer bloques de construcciones (madera, ladrillo...)").define("danoEdificios", false);
        QUAKE_CAMERA_SHAKE = b.comment("Vibracion de la camara de los jugadores (necesita el mod tambien en el cliente)").define("vibracionCamara", true);
        QUAKE_BLOCKS_PER_TICK = b.comment("Bloques que se excavan como maximo por tick (bajalo si el servidor va lento)").defineInRange("bloquesPorTick", 48, 8, 256);
        b.pop();
        b.comment("Volcanes").push("volcan");
        VOLCANO_NATURAL = b.comment("Generar volcanes naturales en chunks NUEVOS (badlands, sabanas, colinas, llanuras)").define("generacionNatural", true);
        VOLCANO_RARITY = b.comment("Rareza: de media 1 volcan cada N chunks aptos (mas alto = menos volcanes)").defineInRange("rareza", 400, 20, 100000);
        VOLCANO_CREATE_IF_NONE = b.comment("Si no hay volcan cerca, la erupcion crea uno pequeno (necesita destruccion distinta de OFF)").define("crearSiNoHay", true);
        VOLCANO_SEARCH_RADIUS = b.comment("Distancia maxima para buscar un volcan conocido cerca del jugador").defineInRange("radioBusqueda", 256, 32, 2048);
        VOLCANO_DANGER_RADIUS = b.comment("Radio de la zona de peligro por calor alrededor del crater").defineInRange("radioPeligro", 12, 4, 48);
        VOLCANO_BOMBS = b.comment("Lanzar rocas volcanicas que caen como bloques (necesita destruccion distinta de OFF)").define("rocasVolcanicas", true);
        VOLCANO_LAVA_FLOWS = b.comment("La lava desborda el crater y baja por la ladera (necesita destruccion distinta de OFF)").define("coladasDeLava", true);
        VOLCANO_LAVA_TEMPORARY = b.comment("Retirar las fuentes de lava de la erupcion al terminar").define("lavaTemporal", true);
        b.pop();
        b.comment("Deslizamientos de tierra (mover bloques necesita destruccion distinta de OFF)").push("deslizamiento");
        SLIDE_RADIUS = b.comment("Radio de la ladera que se desliza").defineInRange("radio", 10, 4, 32);
        SLIDE_MAX_BLOCKS = b.comment("Bloques que se mueven como maximo en un deslizamiento (ademas de maxBloquesPorEvento)").defineInRange("maxBloques", 300, 10, 5000);
        SLIDE_DEPTH = b.comment("Capas de la superficie que pueden deslizarse en cada punto").defineInRange("profundidad", 2, 1, 5);
        SLIDE_BUILDINGS = b.comment("Arrastrar tambien bloques de construcciones (madera, ladrillo...)").define("arrastraConstrucciones", false);
        b.pop();
        b.comment("Lluvia de meteoritos (los crateres necesitan destruccion distinta de OFF)").push("meteoritos");
        METEORS_PER_MINUTE = b.comment("Meteoritos que caen por minuto (con intensidad moderada)").defineInRange("meteoritosPorMinuto", 3, 1, 60);
        METEOR_CRATER_RADIUS = b.comment("Radio del crater de cada impacto").defineInRange("radioCrater", 8, 3, 20);
        METEOR_ORES = b.comment("Los meteoritos pueden dejar hierro en bruto en el crater").define("mineralesEnMeteoritos", true);
        METEOR_MAX_BLOCKS = b.comment("Bloques que puede modificar toda la lluvia (sustituye a maxBloquesPorEvento; alto = mas lag)").defineInRange("maxBloques", 40000, 100, 300000);
        METEOR_BLOCKS_PER_TICK = b.comment("Bloques que se excavan por tick en los crateres (bajalo si el juego va lento)").defineInRange("bloquesPorTick", 300, 20, 5000);
        METEOR_BALL_RADIUS = b.comment("Radio de la bola de roca de cada meteorito (mas grande = mas entidades, mas lag)").defineInRange("radioBola", 2, 1, 4);
        METEOR_SKY_TINT = b.comment("El cielo se vuelve naranja antes y durante la lluvia (necesita el mod en el cliente)").define("cieloNaranja", true);
        b.pop();
        b.comment("Agujero negro (absorber bloques necesita destruccion distinta de OFF)").push("agujeroNegro");
        BLACK_HOLE_PULL_RADIUS = b.comment("Radio en el que atrae jugadores, criaturas y objetos").defineInRange("radioAtraccion", 16, 4, 48);
        BLACK_HOLE_MAX_RADIUS = b.comment("Radio maximo que alcanza al crecer (se traga todo lo que no este protegido, casas incluidas)").defineInRange("radioAbsorcion", 20, 2, 40);
        BLACK_HOLE_MAX_BLOCKS = b.comment("Bloques que puede tragarse (sustituye a maxBloquesPorEvento; alto = mas lag)").defineInRange("maxBloques", 30000, 100, 300000);
        BLACK_HOLE_HEIGHT = b.comment("Altura sobre el suelo a la que aparece").defineInRange("altura", 10, 2, 30);
        BLACK_HOLE_CONSUMES_ITEMS = b.comment("Destruye los objetos tirados que llegan al centro (si no, solo giran)").define("destruyeObjetos", false);
        b.pop();
        b.comment("Agrietamiento del terreno (abrir las grietas necesita destruccion distinta de OFF)").push("agrietamientos");
        CRACKS_COUNT = b.comment("Grietas principales que salen del centro").defineInRange("numeroGrietas", 3, 1, 10);
        CRACKS_LENGTH = b.comment("Longitud de cada grieta principal en bloques").defineInRange("longitud", 40, 8, 120);
        CRACKS_DEPTH = b.comment("Profundidad maxima de las grietas").defineInRange("profundidad", 8, 2, 40);
        CRACKS_WIDTH = b.comment("Anchura maxima de las grietas (en el punto de inicio)").defineInRange("ancho", 3, 1, 9);
        CRACKS_SPEED = b.comment("Bloques que avanza cada grieta por segundo").defineInRange("velocidad", 4, 1, 20);
        CRACKS_BRANCHES = b.comment("Las grietas se ramifican mientras avanzan").define("ramificaciones", true);
        CRACKS_LAVA = b.comment("Lava en el fondo de las grietas mas profundas (solo con destruccion INTENSE)").define("lavaEnFondo", true);
        CRACKS_MAX_BLOCKS = b.comment("Bloques que puede quitar todo el agrietamiento (sustituye a maxBloquesPorEvento)").defineInRange("maxBloques", 8000, 100, 100000);
        b.pop();
        b.comment(new String[]{"Proteccion del mundo. Ademas de esta lista, NUNCA se modifican bloques con inventario", "o datos (cofres, hornos, maquinas de otros mods...) ni bloques irrompibles (roca madre...)."}).push("proteccion");
        PROTECTED_BLOCKS = b.comment("Bloques que nunca se modifican (id completo, por ejemplo minecraft:glass)").defineList("bloquesProtegidos", List.of("minecraft:spawner", "minecraft:beacon", "minecraft:respawn_anchor", "minecraft:end_portal_frame", "minecraft:nether_portal", "minecraft:obsidian", "minecraft:crying_obsidian", "minecraft:reinforced_deepslate", "minecraft:budding_amethyst"), o -> o instanceof String);
        PROTECTED_ZONES = b.comment(new String[]{"Zonas protegidas en el mundo normal: \"x1,z1,x2,z2\" (esquinas). Ejemplo: \"-100,-100,100,100\"", "Dentro de ellas ningun fenomeno modifica bloques."}).defineList("zonasProtegidas", List.of(), o -> o instanceof String);
        b.pop();
        b.comment("Ajustes de cada fenomeno").push("fenomenos");
        for (CatastropheType t : CatastropheType.values()) {
            b.comment(t.displayName).push(t.id);
            ENABLED.put(t, b.comment("Activar este fenomeno").define("activado", true));
            WEIGHT.put(t, b.comment("Probabilidad relativa (0 = nunca al azar)").defineInRange("peso", t.defaultWeight, 0, 1000));
            DURATION_SECONDS.put(t, b.comment("Duracion de la fase activa, en segundos").defineInRange("duracionSegundos", 120, 10, 3600));
            b.pop();
        }
        b.pop();
        SPEC = b.build();
    }

    public static enum Intensity {
        SOFT,
        MODERATE,
        EXTREME;

    }

    public static enum Destruction {
        OFF,
        PARTIAL,
        INTENSE;

    }
}

