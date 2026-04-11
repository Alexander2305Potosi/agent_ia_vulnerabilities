import re
import os

class GradleMutator:
    @staticmethod
    def _version_to_tuple(v):
        """ Converts a version string to (1, 2, 3) for comparison. Handles dirty strings with commas by picking first item. """
        if not v: return (0,)
        clean_v = str(v).split(',')[0].strip()
        parts = []
        for p in re.split(r'[\.\-]', clean_v):
            if p.isdigit():
                parts.append(int(p))
        return tuple(parts)

    @staticmethod
    def is_already_fixed(current_version, safe_version_str):
        """ 
        DETERMINA si la versión actual cumple con los requisitos de seguridad.
        v2.0: Soporta MÚLTIPLES ramas seguras (ej: '4.1.132, 4.2.10').
        """
        curr_tup = GradleMutator._version_to_tuple(current_version)
        safe_versions = [s.strip() for s in str(safe_version_str).split(',')]
        
        # 1. Intentar encontrar una versión segura en la MISMA RAMA (Mismo Major.Minor)
        for sv in safe_versions:
            s_tup = GradleMutator._version_to_tuple(sv)
            # Si coinciden en Major y Minor (primeros 2 elementos)
            if len(curr_tup) >= 2 and len(s_tup) >= 2:
                if curr_tup[0] == s_tup[0] and curr_tup[1] == s_tup[1]:
                    return curr_tup >= s_tup
            elif len(curr_tup) >= 1 and len(s_tup) >= 1:
                # Solo Major coincidencia
                if curr_tup[0] == s_tup[0]:
                    return curr_tup >= s_tup

        # 2. Si no hay coincidencia de rama, comparar con la versión MÁS BAJA de la lista segura
        # para asegurar un mínimo de cumplimiento.
        min_safe = sorted(safe_versions, key=lambda x: GradleMutator._version_to_tuple(x))[0]
        return curr_tup >= GradleMutator._version_to_tuple(min_safe)

    @staticmethod
    def _pick_best_safe_version(current_version, safe_version_str):
        """
        ELIGE la mejor versión de la lista 'safe_version_str' para la rama actual.
        """
        curr_tup = GradleMutator._version_to_tuple(current_version)
        safe_versions = [s.strip() for s in str(safe_version_str).split(',')]
        
        # Buscar coincidencia exacta de rama
        for sv in safe_versions:
            s_tup = GradleMutator._version_to_tuple(sv)
            if len(curr_tup) >= 2 and len(s_tup) >= 2:
                if curr_tup[0] == s_tup[0] and curr_tup[1] == s_tup[1]:
                    return sv
            elif len(curr_tup) >= 1 and len(s_tup) >= 1:
                if curr_tup[0] == s_tup[0]:
                    return sv
        
        # Retornar la más alta por defecto si no hay rama coincidente
        return sorted(safe_versions, key=lambda x: GradleMutator._version_to_tuple(x))[-1]

    @staticmethod
    def _purge_redundant_variables(content, family_var_name):
        """ 
        ELIMINA variables obsoletas del bloque ext si son 'hijas' de una familia.
        Ej: Si inyectamos 'nettyCodecVersion', elimina 'nettyCodecHttpVersion'.
        """
        if not family_var_name.endswith("Version"): return content
        
        base_name = family_var_name.replace("Version", "")
        # Buscamos variables que:
        # 1. Empiecen por el base_name
        # 2. Sean diferentes a la original
        # 3. Estén en el bloque ext
        # Regex más flexible para capturar variables específicas con cualquier indentación
        pattern = rf"^\s*({base_name}\w+Version)\s*=\s*['\"].*?['\"]"
        
        lines = content.splitlines()
        new_lines = []
        for line in lines:
            match = re.search(pattern, line)
            if match:
                var_found = match.group(1)
                if var_found != family_var_name:
                    print(f"    [LIMPIEZA] Eliminando variable redundante: {var_found}")
                    continue
            new_lines.append(line)
        
        return "\n".join(new_lines)

    @staticmethod
    def update_ext_variable(content, var_name, actual_version):
        """
        Updates a variable definition in any ext block.
        Ensures the entire value is replaced.
        """
        actual_version = str(actual_version).strip()
        pattern = rf"({var_name}\s*=\s*['\"])([^'\"]+)(['\"])"
        
        def replace_fn(match):
            return f"{match.group(1)}{actual_version}{match.group(3)}"
            
        new_content, count = re.subn(pattern, replace_fn, content)
        return new_content, count > 0

    @staticmethod
    def substitute_literal_with_variable(content, package, var_name):
        """
        Replaces literal versions 'group:artifact:version' with 'group:artifact:$variableName'.
        v2.0: Ahora es FAMILY-AWARE. Si el paquete pertenece a una familia, sustituye TODO el grupo.
        """
        # Determinar si el paquete pertenece a una familia (solo el grupo)
        families = ["io.netty", "org.springframework", "com.fasterxml.jackson", "org.apache.logging.log4j"]
        group_to_match = package.split(':')[0] if ":" in package else package
        
        # Si el grupo NO está en las familias, usamos el string exacto si tiene dos puntos
        is_family = any(group_to_match.startswith(f) for f in families)
        match_regex = re.escape(group_to_match) + r":[^'\"]+" if is_family else re.escape(package)
        
        if ":" not in package and not is_family:
            return content, False

        verbs = "implementation|runtimeOnly|runtime|compileOnly|compile|api|testImplementation|testRuntimeOnly|testCompileOnly"
        
        # 1. Formato estándar: implementation 'group:artifact:version'
        pattern = rf"^(\s*)({verbs})(\s*)['\"]{match_regex}['\"]"
        
        def replace_literal_fn(match):
            # Extraer el ID completo (group:artifact) sin la versión
            full_line = match.group(0)
            # Reemplazar la parte de la versión ( :version ) por :${var_name}
            # Buscamos el segundo ':' que separa artifact de version
            if is_family:
                # En familias, buscamos la estructura 'group:artifact:version' -> 'group:artifact:${var_name}'
                return re.sub(rf"(['\"]{re.escape(group_to_match)}:[^: \t'\"]+):[^: \t'\"]+(['\"])", 
                              rf"\1:${{{var_name}}}\2", full_line)
            else:
                return re.sub(rf"(['\"]{re.escape(package)}):[^: \t'\"]+(['\"])", 
                              rf"\1:${{{var_name}}}\2", full_line)

        new_content, count = re.subn(pattern, replace_literal_fn, content, flags=re.MULTILINE)
        
        # 2. Formato de mapa: (group: '...', name: '...', version: '...')
        group = group_to_match
        artifact_pattern = r"[^'\"]+" if is_family else re.escape(package.split(':')[1])
        
        pattern_map = rf"(group:\s*['\"]{re.escape(group)}['\"],?\s*name:\s*['\"]{artifact_pattern}['\"],?\s*version:\s*['\"])([\d\.\-\w]+)(['\"])"
        
        def replace_map_fn(match):
            return f"{match.group(1)}${{{var_name}}}{match.group(3)}"
            
        new_content, count_map = re.subn(pattern_map, replace_map_fn, new_content)
        
        return new_content, (count + count_map) > 0

    @staticmethod
    def find_variable_name_in_ext(content, artifact_name):
        """ 
        Identifica qué variable en el bloque ext corresponde al artefacto usando PESOS.
        v2.0: Evita colisiones de prefijos (ej: springBoot vs springWebflux).
        """
        # Tokenizar el nombre del artefacto para scoring (ej: 'netty-codec-http' -> ['netty', 'codec', 'http'])
        art_tokens = set(re.split(r'[\.\-\:]', artifact_name.lower()))
        
        best_var = None
        max_score = -1
        
        pattern = r"(\w+)\s*=\s*['\"]([^'\"]+)['\"]"
        matches = re.finditer(pattern, content)
        for match in matches:
            var_name = match.group(1)
            # Tokenizar variable (ej: 'nettyCodecVersion' -> ['netty', 'codec', 'version'])
            var_tokens = set(re.findall(r'[a-z]+|[A-Z][a-z]*', var_name))
            var_tokens = {t.lower() for t in var_tokens}
            
            # Calcular intersección de tokens
            common = art_tokens.intersection(var_tokens)
            score = len(common)
            
            # Bonus por coincidencia exacta de tokens clave
            if any(t in var_tokens for t in art_tokens if len(t) > 3):
                score += 1

            if score > max_score and score > 0:
                max_score = score
                best_var = var_name
                
        return best_var

    @staticmethod
    def _accumulate_reason(existing_reason, new_reason):
        """ 
        PROCESA la razón de remediación (Whitelist). 
        v2.0: Solo mantiene la razón NUEVA, sin concatenar las anteriores.
        """
        prefix = "Fix: "
        
        # Patrones de IDs de seguridad válidos (CVE y GHSA)
        security_patterns = [
            r"CVE-\d{4}-\d+",
            r"GHSA-[a-z0-9-]+"
        ]
        
        def extract_valid_ids(text):
            if not text: return set()
            findings = set()
            for pattern in security_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                findings.update([m.upper() for m in matches])
            return findings

        # Ignorar la razón existente y procesar solo la nueva
        ids = extract_valid_ids(new_reason)
        
        if not ids:
            return f"{prefix}Security Fix"
            
        sorted_ids = sorted(list(ids))
        return f"{prefix}{', '.join(sorted_ids)}"

    @staticmethod
    def _find_balanced_block(content, start_index):
        """ 
        Encuentra el rango [start, end] de un bloque que empieza en { tras el start_index. 
        Retorna (start, end) o (None, None).
        """
        brace_start = content.find("{", start_index)
        if brace_start == -1: return None, None
        
        stack = 0
        for i in range(brace_start, len(content)):
            if content[i] == '{':
                stack += 1
            elif content[i] == '}':
                stack -= 1
                if stack == 0:
                    return brace_start, i + 1
        return None, None

    @staticmethod
    def inject_resolution_strategy_rule(content, package_or_name, var_name, reason):
        """
        Injects or updates a rule into dependencyMgmt.gradle with structural parsing.
        """
        # 0. Lógica de FAMILIAS
        families = ["io.netty", "org.springframework", "com.fasterxml.jackson", "org.apache.logging.log4j"]
        is_group = False
        group_id = None
        artifact_id = None

        if ":" in package_or_name:
            group_id, artifact_id = package_or_name.split(':')
            if any(group_id.startswith(f) for f in families):
                package_or_name = group_id
                is_group = True
        
        if not is_group:
            is_group = any(f in package_or_name.lower() for f in families)
        
        match_field = "group" if is_group else "name"
        
        # 1. Buscar si ya existe la regla específica
        search_pattern = f"details.requested.{match_field} == '{package_or_name}'"
        pos = content.find(search_pattern)
        
        existing_rule_range = (None, None)
        existing_reason = ""
        
        if pos != -1:
            # Buscar el inicio del 'if' retrocediendo
            if_start = content.rfind("if", 0, pos)
            if if_start != -1:
                block_start, block_end = GradleMutator._find_balanced_block(content, if_start)
                if block_start and block_end:
                    existing_rule_range = (if_start, block_end)
                    rule_text = content[if_start:block_end]
                    # Extraer reason
                    because_match = re.search(r"details\.because\s*['\"](.*?)['\"]", rule_text)
                    if because_match:
                        existing_reason = because_match.group(1)

        final_reason = GradleMutator._accumulate_reason(existing_reason, reason)
        
        # v2.0: Indentación estándar
        i4 = "    "
        i8 = "        "
        i12 = "            "
        
        new_rule_code = f"if (details.requested.{match_field} == '{package_or_name}') {{\n" + \
                         f"{i12}details.useVersion \"${{{var_name}}}\"\n" + \
                         f"{i12}details.because \"{final_reason}\"\n" + \
                         f"{i8}}}"

        # 2. Reemplazar o Inyectar
        if existing_rule_range[0] is not None:
            # Reemplazo atómico del bloque detectado
            start, end = existing_rule_range
            return content[:start] + new_rule_code + content[end:], True

        # 3. Consolidación: Borrar reglas por nombre si estamos inyectando un grupo
        if is_group and artifact_id:
            orphan_pattern = f"details.requested.name == '{artifact_id}'"
            o_pos = content.find(orphan_pattern)
            if o_pos != -1:
                o_if_start = content.rfind("if", 0, o_pos)
                if o_if_start != -1:
                    o_start, o_end = GradleMutator._find_balanced_block(content, o_if_start)
                    if o_start and o_end:
                        print(f"    [CONSOLIDACIÓN] Eliminando regla obsoleta '{artifact_id}'...")
                        content = content[:o_if_start] + content[o_end:]

        # 4. Inyectar en el bloque cadaDependency
        target_str = "resolutionStrategy.eachDependency"
        if target_str in content:
            # Encontrar el bloque del eachDependency
            ed_start = content.find(target_str)
            b_start, b_end = GradleMutator._find_balanced_block(content, ed_start)
            if b_start and b_end:
                # Insertar al final del bloque, antes de la última llave
                prefix = content[:b_end - 1].rstrip()
                suffix = content[b_end - 1:]
                if "// Inject rules here" in prefix:
                    prefix = prefix.replace("// Inject rules here", "").rstrip()
                return f"{prefix}\n{i8}{new_rule_code}\n{i4}{suffix}", True

        # 5. Crear desde cero si no existe el bloque
        wrapper = f"""// Standardized Dependency Management - Centralized AI Security Rules
configurations.all {{
    resolutionStrategy.eachDependency {{ DependencyResolveDetails details ->
        {new_rule_code}
    }}
}}
"""
        return wrapper.strip(), True

        # 3. Inyectar en bloque cadaDependency existente
        if "resolutionStrategy.eachDependency" in content:
            start_keyword = "resolutionStrategy.eachDependency"
            start_index = content.find(start_keyword)
            brace_index = content.find("{", start_index)
            
            if brace_index != -1:
                stack = 1
                end_index = -1
                for i in range(brace_index + 1, len(content)):
                    if content[i] == '{': stack += 1
                    elif content[i] == '}': stack -= 1
                    if stack == 0:
                        end_index = i
                        break
                
                if end_index != -1:
                    prefix = content[:end_index].rstrip()
                    suffix = content[end_index:].strip()
                    # Si ya hay reglas, asegurar un salto. Si es el marcador, reemplazarlo.
                    if "// Inject rules here" in prefix:
                        prefix = prefix.replace("// Inject rules here", "").rstrip()
                    
                    return f"{prefix}\n{new_rule}\n{i4}{suffix}\n", True

        # 4. Crear desde cero
        wrapper = f"""// Standardized Dependency Management - Centralized AI Security Rules
configurations.all {{
    resolutionStrategy.eachDependency {{ DependencyResolveDetails details ->
{new_rule}
    }}
}}
"""
        return wrapper.strip(), True

    INFRA_TEMPLATE = """configurations.all {
    resolutionStrategy.eachDependency { DependencyResolveDetails details ->
    }
}
"""

    @staticmethod
    def _link_infrastructure(project_files, target_folder):
        """
        Asegura que el archivo orquestador (main o build) tenga el vínculo a dependencyMgmt.gradle
        v2.0: Usa ${rootDir}, bloque allprojects y configuración de repositorios.
        INYECCIÓN INTELIGENTE: Evita duplicados analizando el contenido interno del bloque.
        """
        main_gradle = os.path.join(target_folder, "main.gradle")
        build_gradle = os.path.join(target_folder, "build.gradle")
        orchestrator = main_gradle if os.path.exists(main_gradle) else build_gradle

        if os.path.exists(orchestrator):
            with open(orchestrator, 'r') as f:
                content = f.read()
            
            # Limpieza de vínculos antiguos (fuera de bloque o relativos)
            old_link_pattern = r"apply\s+from:\s*['\"]dependencyMgmt\.gradle['\"]"
            content = re.sub(old_link_pattern, "", content).strip()

            new_link_line = 'apply from: "${rootDir}/dependencyMgmt.gradle"'
            repo_block = "repositories { mavenCentral() }"
            
            allprojects_pos = content.find("allprojects")
            if allprojects_pos != -1:
                # 1. Analizar el bloque existente
                start, end = GradleMutator._find_balanced_block(content, allprojects_pos)
                if start and end:
                    block_content = content[start:end]
                    needs_update = False
                    
                    # v2.2: Regex más permisiva para detectar el link sin importar formatos de variables
                    has_link = re.search(r"apply\s+from:.*dependencyMgmt\.gradle", block_content)
                    
                    if not has_link:
                        print(f"    🔗 [SYNC] Asegurando vínculo de infraestructura en {os.path.basename(orchestrator)}...")
                        
                        # Limpiar el cuerpo del bloque y asegurar multi-línea
                        lines = [line.strip() for line in block_content[1:-1].splitlines() if line.strip()]
                        
                        # Inyectar Link al inicio (Mandatorio)
                        lines.insert(0, new_link_line)
                        
                        # Ensamblaje final con indentación jerárquica exacta
                        final_lines = []
                        for line in lines:
                            # Estimación de indentación: si es parte de un bloque interno, darle 8
                            if "repositories" in line or "maven {" in line or "url " in line or (line == "}"):
                                # Si NO es la cabecera del bloque, indentar extra
                                if "repositories" not in line and "apply from" not in line:
                                    final_lines.append(f"        {line}")
                                    continue
                            final_lines.append(f"    {line}")
                        
                        new_block = " {\n" + "\n".join(final_lines) + "\n}"
                        
                        new_content = content[:start] + new_block + content[end:]
                        with open(orchestrator, 'w') as f:
                            f.write(new_content)
                        return True
                    return False

            # 2. Crear bloque completo si no existe
            print(f"    🔗 [LINK] Creando infraestructura global en {os.path.basename(orchestrator)}...")
            new_allprojects = f"\n\nallprojects {{\n    {new_link_line}\n    {repo_block}\n}}\n"
            new_content = content.rstrip() + new_allprojects
            
            with open(orchestrator, 'w') as f:
                f.write(new_content)
            return True
        return False

    @staticmethod
    def apply_coordinated_remediation(project_files, mode, artifact_name, version, reason, override_var_name=None):
        """
        Orquestador v2.0: Auto-Sanación + Remediación + Purga
        """
        # --- PASO 0: Normalización y Auto-Sanación ---
        project_files = [os.path.abspath(f) for f in project_files]
        has_changes = False
        
        constraint_files = [f for f in project_files if f.endswith("dependencyMgmt.gradle")]
        gradle_files = [f for f in project_files if f.endswith(".gradle")]
        build_gradles = sorted([f for f in project_files if f.endswith("build.gradle")], key=len)
        root_build_gradle = build_gradles[0] if build_gradles else None
        
        if not constraint_files and build_gradles:
            root_folder = os.path.dirname(root_build_gradle)
            new_path = os.path.join(root_folder, "dependencyMgmt.gradle")
            print(f"    🛠️ [AUTO-HEAL] Reconstruyendo infraestructura en {os.path.basename(root_folder)}...")
            with open(new_path, 'w') as f:
                f.write(GradleMutator.INFRA_TEMPLATE)
            
            constraint_files = [new_path]
            if new_path not in project_files:
                project_files.append(new_path)
            has_changes = True

        # v2.0: Asegurar VÍNCULO siempre
        if constraint_files and build_gradles:
            root_folder = os.path.dirname(root_build_gradle)
            if GradleMutator._link_infrastructure(project_files, root_folder):
                has_changes = True

        definer_file = None
        var_name = None
        current_version = None

        # --- PASO 1: Identificar Variable y Versión Actual ---
        # v2.5: Prioridad RAÍZ para detección
        for file_path in build_gradles:
            with open(file_path, 'r') as f:
                content = f.read()
            
            found_var = GradleMutator.find_variable_name_in_ext(content, artifact_name)
            is_root = (file_path == root_build_gradle)
            
            if override_var_name:
                var_name = override_var_name
                # Si es override, siempre preferimos definir en raíz
                definer_file = root_build_gradle
            elif found_var:
                var_name = found_var
                # Si se encuentra en raíz, perfecto. Si no, marcaremos para MIGRACIÓN a raíz.
                definer_file = root_build_gradle # v2.5: Forzamos que la definición final sea siempre en raíz
            
            if var_name:
                pattern = rf"{var_name}\s*=\s*['\"]([^'\"]+)['\"]"
                match = re.search(pattern, content)
                if match: 
                    current_version = match.group(1)
                    if is_root: break # Si encontramos en raíz, ya tenemos todo
                    
        # v2.0 NEW: Si no hay variable o no se encontró versión, buscar literal
        if not current_version:
            for file_path in build_gradles:
                with open(file_path, 'r') as f:
                    content = f.read()
                literal_pattern = rf"['\"]{re.escape(artifact_name)}:([\d\.\-\w]+)['\"]"
                l_match = re.search(literal_pattern, content)
                if l_match:
                    current_version = l_match.group(1)
                    print(f"    🔍 [INTELIGENCIA] Versión actual detectada desde literal: {current_version}")
                    break
        
        is_fixed = current_version and GradleMutator.is_already_fixed(current_version, version)
        safe_v = GradleMutator._pick_best_safe_version(current_version, version)

        # --- PASO 2: Definir/Actualizar Variable (SOLO EN RAÍZ) ---
        if not is_fixed:
            if not definer_file:
                if not root_build_gradle: return False
                definer_file = root_build_gradle
                if not override_var_name:
                    parts = artifact_name.split(':')[-1].split('-')
                    var_name = parts[0] + "".join(p.capitalize() for p in parts[1:]) + "Version"
                
                with open(definer_file, 'r') as f:
                    content = f.read()
                
                if "ext {" in content:
                    new_content = content.replace("ext {", f"ext {{\n        {var_name} = '{safe_v}'")
                else:
                    new_content = f"ext {{\n        {var_name} = '{safe_v}'\n}}\n" + content
                with open(definer_file, 'w') as f:
                    f.write(new_content)
                has_changes = True
            else:
                with open(definer_file, 'r') as f:
                    content = f.read()
                new_content, changed = GradleMutator.update_ext_variable(content, var_name, safe_v)
                if not changed:
                    if "ext {" in new_content:
                        new_content = new_content.replace("ext {", f"ext {{\n        {var_name} = '{safe_v}'")
                    else:
                        new_content = f"ext {{\n        {var_name} = '{safe_v}'\n}}\n" + new_content
                with open(definer_file, 'w') as f:
                    f.write(new_content)
                has_changes = True

        # --- PASO 3: Inyectar Regla de Restricción (si es Transitiva) ---
        if mode == "TRANSITIVE" and constraint_files:
            target_constraint = constraint_files[0]
            with open(target_constraint, 'r') as f:
                c_content = f.read()
            
            new_c_content, c_changed = GradleMutator.inject_resolution_strategy_rule(c_content, artifact_name, var_name, reason)
            if c_changed:
                with open(target_constraint, 'w') as f:
                    f.write(new_c_content)
                has_changes = True

        # --- PASO 4: Sustitución Activa de Literales en todos los archivos ---
        for file_path in gradle_files:
            with open(file_path, 'r') as f:
                content = f.read()
            # v2.0/2.5 logic: Reemplazar literales de la familia por la variable
            new_content, changed = GradleMutator.substitute_literal_with_variable(content, artifact_name, var_name)
            if changed:
                with open(file_path, 'w') as f:
                    f.write(new_content)
                has_changes = True

        # --- PASO 5: Purga Global de Subcarpetas (Centralización v2.5) ---
        if var_name:
            for file_path in build_gradles:
                is_root = (file_path == root_build_gradle)
                with open(file_path, 'r') as f:
                    p_content = f.read()
                
                # A. Si es raíz, hacer la purga normal de redundancia
                if is_root:
                    clean_content = GradleMutator._purge_redundant_variables(p_content, var_name)
                    if clean_content != p_content:
                        with open(file_path, 'w') as f:
                            f.write(clean_content)
                        has_changes = True
                else:
                    # B. Si NO es raíz, eliminar la variable de ESTA familia si existe en ext local
                    if f"{var_name} =" in p_content:
                        ext_pos = p_content.find("ext {")
                        if ext_pos != -1:
                            ext_start, ext_end = GradleMutator._find_balanced_block(p_content, ext_pos)
                            if ext_start and ext_end:
                                ext_block = p_content[ext_start:ext_end]
                                new_ext = re.sub(rf"^\s*{var_name}\s*=.*$\n?", "", ext_block, flags=re.MULTILINE)
                                
                                # Si el bloque queda vacío de asignaciones (=), eliminarlo COMPLETAMENTE (incluyendo 'ext')
                                if not re.search(r"=\s*", new_ext):
                                    actual_start = p_content.rfind("ext", 0, ext_start)
                                    if actual_start == -1: actual_start = ext_start
                                    final_p = p_content[:actual_start].rstrip() + "\n" + p_content[ext_end:].lstrip()
                                else:
                                    final_p = p_content[:ext_start] + new_ext + p_content[ext_end:]
                                
                                if final_p != p_content:
                                    with open(file_path, 'w') as f:
                                        f.write(final_p)
                                    print(f"    🧹 [PURGA] Limpiando definición redundante en {os.path.basename(os.path.dirname(file_path))}/build.gradle")
                                    has_changes = True

        if has_changes: return True
        return "ALREADY_FIXED" if is_fixed else False
