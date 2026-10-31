package com.panthrix.naturaldisasters.core;

public enum CatastropheType {
    TORNADO("tornado", "Tornado", "\u00a1PELIGRO! Un tornado se acerca a esta zona."),
    BLIZZARD("blizzard", "Ventisca", "\u00a1ALERTA! Se aproxima una ventisca muy fuerte."),
    EARTHQUAKE("earthquake", "Terremoto", "\u00a1ALERTA! Se aproxima un terremoto."),
    FLOOD("flood", "Inundaci\u00f3n", "\u00a1ALERTA! Riesgo de inundaci\u00f3n en esta zona."),
    VOLCANO("volcano", "Erupci\u00f3n volc\u00e1nica", "\u00a1ALERTA VOLC\u00c1NICA! Se ha detectado actividad volc\u00e1nica cerca."),
    THUNDERSTORM("thunderstorm", "Tormenta el\u00e9ctrica extrema", "\u00a1ALERTA! Se aproxima una tormenta el\u00e9ctrica extrema."),
    LANDSLIDE("landslide", "Deslizamiento de tierra", "\u00a1PELIGRO! Riesgo de deslizamiento de tierra en las laderas."),
    HAILSTORM("hailstorm", "Granizada", "\u00a1ALERTA! Se aproxima una granizada. Buscad refugio."),
    DROUGHT("drought", "Sequ\u00eda", "\u00a1AVISO! Comienza un periodo de sequ\u00eda."),
    METEOR_SHOWER("meteor_shower", "Lluvia de meteoritos", "\u00a1ALERTA! Se aproxima una lluvia de meteoritos. Buscad refugio.", 6),
    BLACK_HOLE("black_hole", "Agujero negro", "\u00a1PELIGRO EXTREMO! Se est\u00e1 formando un agujero negro en esta zona.", 3),
    GROUND_CRACKS("ground_cracks", "Agrietamiento del terreno", "\u00a1PELIGRO! El terreno empieza a agrietarse en esta zona. Alejaos de las grietas.", 8);

    public final String id;
    public final String displayName;
    public final String warningMessage;
    public final int defaultWeight;

    private CatastropheType(String id, String displayName, String warningMessage) {
        this(id, displayName, warningMessage, 10);
    }

    private CatastropheType(String id, String displayName, String warningMessage, int defaultWeight) {
        this.id = id;
        this.displayName = displayName;
        this.warningMessage = warningMessage;
        this.defaultWeight = defaultWeight;
    }

    public static CatastropheType byId(String id) {
        for (CatastropheType t : CatastropheType.values()) {
            if (!t.id.equalsIgnoreCase(id)) continue;
            return t;
        }
        return null;
    }
}

