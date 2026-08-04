package io.github.opencubicchunks.cubicchunks.util.dasm;

import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import io.github.notstirred.dasm.annotation.AnnotationParser;
import io.github.notstirred.dasm.annotation.AnnotationUtil;
import io.github.notstirred.dasm.annotation.parse.RefImpl;
import io.github.notstirred.dasm.api.annotations.Dasm;
import io.github.notstirred.dasm.api.provider.MappingsProvider;
import io.github.notstirred.dasm.data.DasmContext;
import io.github.notstirred.dasm.exception.NoSuchTypeExists;
import io.github.notstirred.dasm.notify.Notification;
import io.github.notstirred.dasm.transformer.Transformer;
import io.github.notstirred.dasm.transformer.data.ClassTransform;
import io.github.notstirred.dasm.transformer.data.MethodTransform;
import io.github.notstirred.dasm.util.ClassNodeProvider;
import io.github.notstirred.dasm.util.Pair;
import io.github.notstirred.dasm.util.TypeUtil;
import org.objectweb.asm.Type;
import org.objectweb.asm.tree.AnnotationNode;
import org.objectweb.asm.tree.ClassNode;
import org.objectweb.asm.tree.MethodNode;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.MixinEnvironment;
import org.spongepowered.asm.mixin.transformer.ClassInfo;
import org.spongepowered.asm.mixin.transformer.IMixinTransformer;
import org.spongepowered.asm.mixin.transformer.ext.Extensions;
import org.spongepowered.asm.mixin.transformer.ext.IExtension;
import org.spongepowered.asm.mixin.transformer.ext.ITargetClassContext;

/**
 * Fabric bootstrap for DASM method/class transforms.
 *
 * <p>This is a compact Fabric 26.2 adapter based on the MIT-licensed design in
 * NotStirred/dasm-mod. It uses the published DASM core library and registers its
 * transformer as a Mixin extension before CubicChunks mixins are prepared.</p>
 */
public final class FabricDasmRuntime {
    private static RuntimeExtension extension;

    private FabricDasmRuntime() {}

    public static synchronized RuntimeExtension initialize(ClassNodeProvider classProvider) {
        if (extension != null) {
            return extension;
        }
        RuntimeExtension created = new RuntimeExtension(MappingsProvider.IDENTITY, classProvider);
        install(created);
        extension = created;
        return created;
    }

    private static void install(RuntimeExtension runtimeExtension) {
        IMixinTransformer transformer = (IMixinTransformer) MixinEnvironment.getDefaultEnvironment().getActiveTransformer();
        Extensions extensions = (Extensions) transformer.getExtensions();
        try {
            Field field = Extensions.class.getDeclaredField("extensions");
            field.setAccessible(true);
            @SuppressWarnings("unchecked")
            List<IExtension> registered = (List<IExtension>) field.get(extensions);
            registered.add(runtimeExtension);
        } catch (ReflectiveOperationException exception) {
            throw new IllegalStateException("Unable to register the DASM Mixin extension", exception);
        }
    }

    public static final class RuntimeExtension implements IExtension {
        private final ClassNodeProvider classProvider;
        private final AnnotationParser annotationParser;
        private final Transformer transformer;
        private final Map<String, TransformBundle> transformsByTarget = new HashMap<>();
        private final Set<String> scannedClasses = new HashSet<>();

        private RuntimeExtension(MappingsProvider mappingsProvider, ClassNodeProvider classProvider) {
            this.classProvider = classProvider;
            this.annotationParser = new AnnotationParser(classProvider);
            this.transformer = new Transformer(classProvider, mappingsProvider);
        }

        public synchronized void register(String dasmClassName) {
            if (!this.scannedClasses.add(dasmClassName)) {
                return;
            }
            try {
                ClassNode dasmClass = this.classProvider.classNode(Type.getObjectType(TypeUtil.classNameToInternalName(dasmClassName)));
                AnnotationNode dasmAnnotation = AnnotationUtil.getAnnotationIfPresent(dasmClass.invisibleAnnotations, Dasm.class);
                Optional<Type> targetType = Optional.empty();
                if (dasmAnnotation != null) {
                    Object targetValue = AnnotationUtil.getAnnotationValues(dasmAnnotation, Dasm.class).get("target");
                    if (targetValue instanceof AnnotationNode targetAnnotation) {
                        targetType = RefImpl.parseOptionalRefAnnotation(targetAnnotation);
                    }
                }

                ClassNode primary = dasmClass;
                Optional<ClassNode> secondary = Optional.empty();
                if (targetType.isPresent() && !targetType.get().equals(Type.getObjectType(dasmClass.name))) {
                    primary = this.classProvider.classNode(targetType.get());
                    secondary = Optional.of(dasmClass);
                }

                check(this.annotationParser.findDasmAnnotations(primary));
                DasmContext context = this.annotationParser.buildContext();
                Pair<Optional<Collection<MethodTransform>>, List<Notification>> primaryMethods = context.buildMethodTargets(primary, "");
                Pair<Optional<ClassTransform>, List<Notification>> classTransform = context.buildClassTarget(primary);
                check(primaryMethods.second());
                check(classTransform.second());

                Optional<Collection<MethodTransform>> secondaryMethods = Optional.empty();
                if (secondary.isPresent()) {
                    check(this.annotationParser.findDasmAnnotations(secondary.get()));
                    context = this.annotationParser.buildContext();
                    Pair<Optional<Collection<MethodTransform>>, List<Notification>> parsed = context.buildMethodTargets(secondary.get(), "");
                    check(parsed.second());
                    secondaryMethods = parsed.first();
                }

                List<MethodTransform> methods = Stream.of(primaryMethods.first(), secondaryMethods)
                        .filter(Optional::isPresent)
                        .map(Optional::get)
                        .flatMap(Collection::stream)
                        .collect(Collectors.toCollection(ArrayList::new));
                String targetName = primary.name.replace('/', '.');
                TransformBundle bundle = this.transformsByTarget.computeIfAbsent(targetName, ignored -> new TransformBundle());
                bundle.methods.addAll(methods);
                classTransform.first().ifPresent(transform -> {
                    if (bundle.classTransform != null) {
                        throw new IllegalStateException("Multiple DASM class transforms target " + targetName);
                    }
                    bundle.classTransform = transform;
                });
            } catch (NoSuchTypeExists exception) {
                throw new IllegalStateException("Unable to register DASM class " + dasmClassName, exception);
            }
        }

        @Override public boolean checkActive(MixinEnvironment environment) {
            return true;
        }

        @Override public void preApply(ITargetClassContext context) {
            String targetName = context.getClassInfo().getClassName();
            TransformBundle bundle = this.transformsByTarget.get(targetName);
            if (bundle == null) {
                return;
            }

            ClassNode target = context.getClassNode();
            if (bundle.classTransform != null) {
                try {
                    check(this.transformer.transform(target, bundle.classTransform).notifications());
                } catch (NoSuchTypeExists exception) {
                    throw new IllegalStateException("DASM class transform failed for " + targetName, exception);
                }
            }
            if (!bundle.methods.isEmpty()) {
                Transformer.TransformResult<List<MethodNode>> result = this.transformer.transform(target, bundle.methods);
                check(result.notifications());
                for (MethodNode method : result.changed()) {
                    if (method.visibleAnnotations == null) {
                        method.visibleAnnotations = new ArrayList<>();
                    }
                    method.visibleAnnotations.add(new AnnotationNode(Type.getDescriptor(Final.class)));
                }
            }
            refreshMixinMetadata(target);
        }

        @Override public void postApply(ITargetClassContext context) {}

        @Override public void export(MixinEnvironment environment, String name, boolean force, ClassNode classNode) {}

        private static void refreshMixinMetadata(ClassNode target) {
            try {
                Method addMethod = ClassInfo.class.getDeclaredMethod("addMethod", MethodNode.class, boolean.class);
                addMethod.setAccessible(true);
                ClassInfo info = ClassInfo.forName(target.name);
                Set<String> known = info.getMethods().stream().map(method -> method.getName() + method.getDesc()).collect(Collectors.toSet());
                for (MethodNode method : target.methods) {
                    if (known.add(method.name + method.desc)) {
                        addMethod.invoke(info, method, false);
                    }
                }
            } catch (NoSuchMethodException | IllegalAccessException | InvocationTargetException exception) {
                throw new IllegalStateException("Unable to refresh Mixin metadata after DASM transformation", exception);
            }
        }

        private static void check(io.github.notstirred.dasm.util.NotifyStack notifications) {
            check(notifications.notifications());
        }

        private static void check(List<Notification> notifications) {
            String errors = notifications.stream()
                    .filter(notification -> notification.kind == Notification.Kind.ERROR)
                    .map(notification -> notification.message)
                    .collect(Collectors.joining("; "));
            if (!errors.isEmpty()) {
                throw new IllegalStateException("DASM transform registration failed: " + errors);
            }
        }
    }

    private static final class TransformBundle {
        private final List<MethodTransform> methods = new ArrayList<>();
        private ClassTransform classTransform;
    }
}
