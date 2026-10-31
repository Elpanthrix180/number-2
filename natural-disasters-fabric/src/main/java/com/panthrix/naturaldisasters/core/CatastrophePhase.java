package com.panthrix.naturaldisasters.core;

public enum CatastrophePhase {
    CALM("Calma"),
    WARNING("Aviso"),
    PREPARATION("Preparaci\u00f3n"),
    ACTIVE("Activo"),
    ENDING("Finalizaci\u00f3n"),
    RECOVERY("Recuperaci\u00f3n");

    public final String displayName;

    private CatastrophePhase(String displayName) {
        this.displayName = displayName;
    }

    public CatastrophePhase next() {
        return this == RECOVERY ? CALM : CatastrophePhase.values()[this.ordinal() + 1];
    }
}

