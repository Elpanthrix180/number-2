package com.panthrix.naturaldisasters.config;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.google.gson.JsonPrimitive;
import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Predicate;

/**
 * Sustituto sencillo de ForgeConfigSpec para Fabric. Guarda la configuracion en un archivo JSON
 * con la misma estructura de secciones que la version de Forge.
 */
public final class ConfigSpec {
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create();

    private final List<ConfigValue<?>> values;
    private final Map<String, String> sectionComments;

    private ConfigSpec(List<ConfigValue<?>> values, Map<String, String> sectionComments) {
        this.values = values;
        this.sectionComments = sectionComments;
    }

    /** Lee el archivo (si existe), corrige valores invalidos y vuelve a guardarlo con todos los campos. */
    public void load(Path file) {
        JsonObject root = new JsonObject();
        if (Files.exists(file)) {
            try (Reader r = Files.newBufferedReader(file, StandardCharsets.UTF_8)) {
                JsonElement e = JsonParser.parseReader(r);
                if (e != null && e.isJsonObject()) {
                    root = e.getAsJsonObject();
                }
            } catch (Exception ex) {
                com.panthrix.naturaldisasters.NaturalDisastersMod.LOGGER.warn("[Panthrix's Natural Disasters] No se pudo leer {}; se usan valores por defecto.", file, ex);
            }
        }
        for (ConfigValue<?> v : this.values) {
            JsonObject section = root;
            for (int i = 0; i < v.path.length - 1; ++i) {
                JsonElement child = section.get(v.path[i]);
                if (child == null || !child.isJsonObject()) {
                    section = null;
                    break;
                }
                section = child.getAsJsonObject();
            }
            JsonElement raw = section == null ? null : section.get(v.path[v.path.length - 1]);
            v.read(raw);
        }
        this.save(file);
    }

    public void save(Path file) {
        JsonObject root = new JsonObject();
        for (ConfigValue<?> v : this.values) {
            JsonObject section = root;
            StringBuilder key = new StringBuilder();
            for (int i = 0; i < v.path.length - 1; ++i) {
                if (key.length() > 0) key.append('.');
                key.append(v.path[i]);
                JsonElement child = section.get(v.path[i]);
                if (child == null) {
                    JsonObject created = new JsonObject();
                    String c = this.sectionComments.get(key.toString());
                    if (c != null) created.addProperty("_comentario", c);
                    section.add(v.path[i], created);
                    child = created;
                }
                section = child.getAsJsonObject();
            }
            String name = v.path[v.path.length - 1];
            if (v.comment != null) section.addProperty("_" + name, v.comment);
            section.add(name, v.write());
        }
        try {
            Files.createDirectories(file.getParent());
            try (Writer w = Files.newBufferedWriter(file, StandardCharsets.UTF_8)) {
                GSON.toJson(root, w);
            }
        } catch (IOException ex) {
            com.panthrix.naturaldisasters.NaturalDisastersMod.LOGGER.warn("[Panthrix's Natural Disasters] No se pudo guardar {}.", file, ex);
        }
    }

    public static class ConfigValue<T> {
        final String[] path;
        final String comment;
        final T defaultValue;
        T value;

        ConfigValue(String[] path, String comment, T defaultValue) {
            this.path = path;
            this.comment = comment;
            this.defaultValue = defaultValue;
            this.value = defaultValue;
        }

        public T get() {
            return this.value;
        }

        public void set(T value) {
            this.value = value;
        }

        void read(JsonElement e) {
            this.value = this.defaultValue;
        }

        JsonElement write() {
            return GSON.toJsonTree(this.value);
        }
    }

    public static class BooleanValue extends ConfigValue<Boolean> {
        BooleanValue(String[] p, String c, boolean d) { super(p, c, d); }

        @Override
        void read(JsonElement e) {
            this.value = e != null && e.isJsonPrimitive() && e.getAsJsonPrimitive().isBoolean() ? e.getAsBoolean() : this.defaultValue;
        }
    }

    public static class IntValue extends ConfigValue<Integer> {
        final int min;
        final int max;

        IntValue(String[] p, String c, int d, int min, int max) {
            super(p, c, d);
            this.min = min;
            this.max = max;
        }

        @Override
        void read(JsonElement e) {
            try {
                int v = e.getAsInt();
                this.value = v < this.min || v > this.max ? this.defaultValue : v;
            } catch (Exception ex) {
                this.value = this.defaultValue;
            }
        }
    }

    public static class DoubleValue extends ConfigValue<Double> {
        final double min;
        final double max;

        DoubleValue(String[] p, String c, double d, double min, double max) {
            super(p, c, d);
            this.min = min;
            this.max = max;
        }

        @Override
        void read(JsonElement e) {
            try {
                double v = e.getAsDouble();
                this.value = v < this.min || v > this.max || Double.isNaN(v) ? this.defaultValue : v;
            } catch (Exception ex) {
                this.value = this.defaultValue;
            }
        }
    }

    public static class EnumValue<E extends Enum<E>> extends ConfigValue<E> {
        EnumValue(String[] p, String c, E d) { super(p, c, d); }

        @Override
        void read(JsonElement e) {
            try {
                this.value = Enum.valueOf(this.defaultValue.getDeclaringClass(), e.getAsString().trim().toUpperCase(java.util.Locale.ROOT));
            } catch (Exception ex) {
                this.value = this.defaultValue;
            }
        }

        @Override
        JsonElement write() {
            return new JsonPrimitive(this.value.name());
        }
    }

    public static class ListValue extends ConfigValue<List<? extends String>> {
        final Predicate<Object> validator;

        ListValue(String[] p, String c, List<? extends String> d, Predicate<Object> validator) {
            super(p, c, List.copyOf(d));
            this.validator = validator;
        }

        @Override
        void read(JsonElement e) {
            if (e == null || !e.isJsonArray()) {
                this.value = this.defaultValue;
                return;
            }
            List<String> out = new ArrayList<>();
            for (JsonElement x : e.getAsJsonArray()) {
                if (x.isJsonPrimitive() && x.getAsJsonPrimitive().isString() && this.validator.test(x.getAsString())) {
                    out.add(x.getAsString());
                }
            }
            this.value = List.copyOf(out);
        }

        @Override
        JsonElement write() {
            JsonArray a = new JsonArray();
            for (String s : this.value) a.add(s);
            return a;
        }
    }

    public static class Builder {
        private final Deque<String> stack = new ArrayDeque<>();
        private final List<ConfigValue<?>> values = new ArrayList<>();
        private final Map<String, String> sectionComments = new LinkedHashMap<>();
        private String pendingComment;

        public Builder comment(String comment) {
            this.pendingComment = comment;
            return this;
        }

        public Builder comment(String... lines) {
            this.pendingComment = String.join(" ", lines);
            return this;
        }

        public Builder push(String name) {
            this.stack.addLast(name);
            if (this.pendingComment != null) {
                this.sectionComments.put(String.join(".", this.stack), this.pendingComment);
            }
            this.pendingComment = null;
            return this;
        }

        public Builder pop() {
            this.stack.removeLast();
            return this;
        }

        private String[] path(String name) {
            List<String> p = new ArrayList<>(this.stack);
            p.add(name);
            return p.toArray(new String[0]);
        }

        private String takeComment() {
            String c = this.pendingComment;
            this.pendingComment = null;
            return c;
        }

        private <V extends ConfigValue<?>> V add(V v) {
            this.values.add(v);
            return v;
        }

        public BooleanValue define(String name, boolean def) {
            return this.add(new BooleanValue(this.path(name), this.takeComment(), def));
        }

        public IntValue defineInRange(String name, int def, int min, int max) {
            return this.add(new IntValue(this.path(name), this.takeComment(), def, min, max));
        }

        public DoubleValue defineInRange(String name, double def, double min, double max) {
            return this.add(new DoubleValue(this.path(name), this.takeComment(), def, min, max));
        }

        public <E extends Enum<E>> EnumValue<E> defineEnum(String name, E def) {
            return this.add(new EnumValue<>(this.path(name), this.takeComment(), def));
        }

        public ListValue defineList(String name, List<? extends String> def, Predicate<Object> validator) {
            return this.add(new ListValue(this.path(name), this.takeComment(), def, validator));
        }

        public ConfigSpec build() {
            return new ConfigSpec(List.copyOf(this.values), Map.copyOf(this.sectionComments));
        }
    }
}
