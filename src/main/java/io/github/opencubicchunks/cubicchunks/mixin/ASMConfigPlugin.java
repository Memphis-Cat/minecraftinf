package io.github.opencubicchunks.cubicchunks.mixin;

import static org.objectweb.asm.Opcodes.*;

import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.Set;

import javax.annotation.Nullable;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import io.github.notstirred.dasm.util.CachingClassProvider;
import io.github.opencubicchunks.cc_core.annotation.Public;
import io.github.opencubicchunks.cubicchunks.util.asm.FactoryFromConstructor;
import io.github.opencubicchunks.cubicchunks.util.dasm.FabricDasmRuntime;
import org.objectweb.asm.Type;
import org.objectweb.asm.tree.AnnotationNode;
import org.objectweb.asm.tree.ClassNode;
import org.objectweb.asm.tree.MethodNode;
import org.spongepowered.asm.mixin.extensibility.IMixinConfigPlugin;
import org.spongepowered.asm.mixin.extensibility.IMixinInfo;
import org.spongepowered.asm.service.IMixinService;
import org.spongepowered.asm.service.MixinService;

public class ASMConfigPlugin implements IMixinConfigPlugin {
    private static final String DASM_CONFIG = "cubicchunks.dasm.json";

    public ASMConfigPlugin() {}

    @Override public void onLoad(String mixinPackage) {
        IMixinService mixinService = MixinService.getService();
        CachingClassProvider classProvider = new CachingClassProvider(className -> {
            String resource = className.replace('.', '/') + ".class";
            try (InputStream stream = mixinService.getResourceAsStream(resource)) {
                if (stream == null) {
                    return Optional.empty();
                }
                return Optional.of(stream.readAllBytes());
            } catch (IOException exception) {
                throw new IllegalStateException("Unable to read DASM class resource " + resource, exception);
            }
        });

        FabricDasmRuntime.RuntimeExtension extension = FabricDasmRuntime.initialize(classProvider);
        try (InputStream stream = mixinService.getResourceAsStream(DASM_CONFIG)) {
            if (stream == null) {
                throw new IllegalStateException("Missing required DASM config " + DASM_CONFIG);
            }
            JsonObject config = JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8)).getAsJsonObject();
            JsonArray classes = config.getAsJsonArray("dasm");
            if (classes == null || classes.isEmpty()) {
                throw new IllegalStateException("DASM config contains no transform classes: " + DASM_CONFIG);
            }
            for (JsonElement element : classes) {
                extension.register(element.getAsString());
            }
        } catch (IOException exception) {
            throw new IllegalStateException("Unable to read DASM config " + DASM_CONFIG, exception);
        }
    }

    @Override public String getRefMapperConfig() {
        return null;
    }

    @Override public boolean shouldApplyMixin(String targetClassName, String mixinClassName) {
        return true;
    }

    @Override public void acceptTargets(Set<String> myTargets, Set<String> otherTargets) {}

    @Override public @Nullable List<String> getMixins() {
        return null;
    }

    @Override public void preApply(String targetClassName, ClassNode targetClass, String mixinClassName, IMixinInfo mixinInfo) {}

    @Override public void postApply(String targetClassName, ClassNode targetClass, String mixinClassName, IMixinInfo mixinInfo) {
        doPublicAnnotation(targetClass);
        doFactoryFromConstructorAnnotation(targetClass);
    }

    private void doPublicAnnotation(ClassNode targetClass) {
        // Making any methods annotated as @Public public
        for (MethodNode method : targetClass.methods) {
            List<AnnotationNode> visibleAnnotations = method.visibleAnnotations;
            if (visibleAnnotations != null) {
                if (visibleAnnotations.stream()
                        .anyMatch(annotationNode -> annotationNode.desc.equals("L" + Public.class.getName().replace('.', '/') + ";"))) {
                    method.access &= ~(ACC_PRIVATE | ACC_PROTECTED);
                    method.access |= ACC_PUBLIC;
                }
            }
        }
    }

    private void doFactoryFromConstructorAnnotation(ClassNode targetClass) {
        // Generate constructor calls matching the signature of methods annotated with @FactoryFromConstructor
        for (MethodNode method : targetClass.methods) {
            List<AnnotationNode> annotations = method.invisibleAnnotations;
            if (annotations != null) {
                if (annotations.stream().anyMatch(
                        annotationNode -> annotationNode.desc.equals("L" + FactoryFromConstructor.class.getName().replace('.', '/') + ";"))) {
                    if ((method.access & ACC_STATIC) == 0) {
                        throw new IllegalStateException("Tried to generate a factory method on a non-static dst");
                    }
                    transformStubToFactory(method);
                }
            }
        }
    }

    private static void transformStubToFactory(MethodNode method) {
        method.access &= ~ACC_NATIVE;
        Type methodType = Type.getMethodType(method.desc);
        Type returnType = methodType.getReturnType();
        Type[] argumentTypes = methodType.getArgumentTypes();

        method.instructions.clear();
        method.visitTypeInsn(NEW, returnType.getInternalName());
        method.visitInsn(DUP);
        for (int i = 0; i < argumentTypes.length; i++) {
            Type argumentType = argumentTypes[i];
            switch (argumentType.getSort()) {
                case Type.OBJECT, Type.ARRAY -> method.visitVarInsn(ALOAD, i);
                case Type.LONG -> method.visitVarInsn(LLOAD, i);
                case Type.INT, Type.SHORT, Type.BYTE, Type.BOOLEAN, Type.CHAR -> method.visitVarInsn(ILOAD, i);
                case Type.DOUBLE -> method.visitVarInsn(DLOAD, i);
                case Type.FLOAT -> method.visitVarInsn(FLOAD, i);
                default -> throw new IllegalStateException("Unexpected sort: " + argumentType.getSort());
            }
        }
        method.visitMethodInsn(INVOKESPECIAL, returnType.getInternalName(), "<init>",
                method.desc.substring(0, method.desc.lastIndexOf(')') + 1) + "V", false);
        method.visitInsn(ARETURN);
    }
}
