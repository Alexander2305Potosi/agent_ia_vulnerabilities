import re
import os

class GradleMutator:
    @staticmethod
    def _version_to_tuple(v):
        """ Converts a version string to (1, 2, 3) for comparison. Handles dirty strings with commas. """
        if not v: return (0,)
        # Remove anything after a comma if exists (we compare single versions)
        clean_v = str(v).split(',')[0].strip()
        parts = []
        for p in re.split(r'[\.\-]', clean_v):
            if p.isdigit():
                parts.append(int(p))
        return tuple(parts)

    @staticmethod
    def is_already_fixed(current_version, safe_version):
        """ Returns True if current_version >= safe_version. """
        return GradleMutator._version_to_tuple(current_version) >= GradleMutator._version_to_tuple(safe_version)

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
        # Regex más flexible para capturar variables específicas
        pattern = rf"\s*({base_name}\w+Version)\s*=\s*['\"].*?['\"]"
        
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
    def update_ext_variable(content, var_name, new_version):
        """
        Updates a variable definition in any ext block.
        Ensures the entire value is replaced to avoid version accumulation.
        Uses lambda to avoid special character interpretation.
        """
        # Pick the first version if list provided
        actual_version = str(new_version).split(',')[0].strip()
        pattern = rf"({var_name}\s*=\s*['\"])([^'\"]+)(['\"])"
        
        def replace_fn(match):
            return f"{match.group(1)}{actual_version}{match.group(3)}"
            
        new_content, count = re.subn(pattern, replace_fn, content)
        return new_content, count > 0

    @staticmethod
    def substitute_literal_with_variable(content, package, var_name):
        """
        Replaces literal versions 'group:artifact:version' with 'group:artifact:$variableName'.
        Handles implementation, testImplementation, api, etc.
        Uses lambda for safe replacement.
        """
        # If package is just a group (no colon), skip substitution as it requires full ID
        if ":" not in package:
            return content, False

        # Match pattern: Any line containing implementation/runtimeOnly etc + group:artifact
        # v2.1: Ahora preservamos la línea y sustituimos la versión por una variable
        verbs = "implementation|runtimeOnly|runtime|compileOnly|compile|api|testImplementation|testRuntimeOnly|testCompileOnly"
        pattern = rf"^(\s*)({verbs})(\s*)['\"]{re.escape(package)}(?::[^'\"]+)?['\"]"
        
        def replace_literal_fn(match):
            return f"{match.group(1)}{match.group(2)}{match.group(3)}\"{package}:${{{var_name}}}\""
            
        new_content, count = re.subn(pattern, replace_literal_fn, content, flags=re.MULTILINE)
        
        # Also handle map style if needed: (group: '...', name: '...', version: '...')
        group, artifact = package.split(':')
        pattern_map = rf"(group:\s*['\"]{re.escape(group)}['\"],?\s*name:\s*['\"]{re.escape(artifact)}['\"],?\s*version:\s*['\"])([\d\.\-\w]+)(['\"])"
        
        def replace_map_fn(match):
            return f"{match.group(1)}${{{var_name}}}{match.group(3)}"
            
        new_content, count_map = re.subn(pattern_map, replace_map_fn, new_content)
        
        return new_content, (count + count_map) > 0

    @staticmethod
    def find_variable_name_in_ext(content, artifact_name):
        """ Tries to find which variable in the ext block likely corresponds to an artifact. """
        clean_name = artifact_name.replace("-", "").replace(".", "").lower()
        # Also try a prefix match (e.g., 'nettycodec' for 'netty-codec-http')
        prefix_name = artifact_name.split('-')[0].lower() + "codec" if "codec" in artifact_name else artifact_name.split('-')[0].lower()
        
        pattern = r"(\w+)\s*=\s*['\"]([^'\"]+)['\"]"
        matches = re.finditer(pattern, content)
        for match in matches:
            var_name = match.group(1)
            var_name_lower = var_name.lower()
            if clean_name in var_name_lower or var_name_lower.startswith(prefix_name):
                return var_name
        return None

    @staticmethod
    def inject_resolution_strategy_rule(content, package_or_name, var_name, reason):
        """
        Injects or updates a rule into dependencyMgmt.gradle.
        Supports both artifact name and group-level pinning.
        """
        # 0. Lógica de FAMILIAS (v2.0): Priorizar agrupación por grupo para Netty, Spring, Jackson
        families = ["io.netty", "org.springframework", "com.fasterxml.jackson"]
        is_group = False
        
        # Si recibimos un paquete completo, intentamos extraer el grupo
        if ":" in package_or_name:
            group_candidate = package_or_name.split(':')[0]
            # v2.0: Detección inteligente por inicio de grupo (startswith)
            if any(group_candidate.startswith(f) for f in families):
                package_or_name = group_candidate
                is_group = True
        
        # Detect si es un grupo (ej. io.netty) o nombre
        if not is_group:
            is_group = any(f in package_or_name.lower() or package_or_name in f for f in families)
        
        match_field = "group" if is_group else "name"
        
        # v2.1: Estándar de indentación estricto (4 espacios por nivel)
        i4 = "    "
        i8 = "        "
        i12 = "            "
        
        new_rule = f"{i8}if (details.requested.{match_field} == '{package_or_name}') {{\n" + \
                   f"{i12}details.useVersion \"${{{var_name}}}\"\n" + \
                   f"{i12}details.because \"{reason or 'Security Fix'}\"\n" + \
                   f"{i8}}}"
        
        # 1. Update existing rule if it exists (check both name and group patterns)
        # v2.2: Regex más robusta para capturar el bloque completo y sus saltos de línea
        pattern_existing = rf"\n?\s*if\s*\(\s*details\.requested\.({match_field})\s*==\s*['\"]{re.escape(package_or_name)}['\"]\s*\)\s*\{{.*?\n\s*\}}\n?"
        if re.search(pattern_existing, content, re.DOTALL):
            # Reemplazo limpio con saltos de línea garantizados
            return re.sub(pattern_existing, f"\n{new_rule}\n", content, count=1, flags=re.DOTALL), True

        # 2. Inject into existing eachDependency block
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
                    # Inyección limpia: eliminar espacios en blanco previos y asegurar un solo salto
                    prefix = content[:end_index].rstrip()
                    suffix = content[end_index:].strip()
                    
                    # Limpiamos el marcador temporal si existe
                    if "// Inject rules here" in prefix:
                        prefix = prefix.replace("// Inject rules here", "").rstrip()
                    
                    return f"{prefix}\n{new_rule}\n    {suffix}\n", True

        # 3. Create from scratch
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
        """
        main_gradle = os.path.join(target_folder, "main.gradle")
        build_gradle = os.path.join(target_folder, "build.gradle")
        orchestrator = main_gradle if os.path.exists(main_gradle) else build_gradle

        if os.path.exists(orchestrator):
            with open(orchestrator, 'r') as f:
                content = f.read()
            
            # v2.0: Búsqueda robusta con regex para evitar duplicados por comillas o espacios
            link_pattern = r"apply\s+from:\s*['\"]dependencyMgmt\.gradle['\"]"
            if not re.search(link_pattern, content):
                print(f"    🔗 [LINK] Vinculando infraestructura en {os.path.basename(orchestrator)}...")
                with open(orchestrator, 'a') as f:
                    if not content.endswith('\n'): f.write('\n')
                    f.write("apply from: 'dependencyMgmt.gradle'\n")

    @staticmethod
    def apply_coordinated_remediation(project_files, mode, artifact_name, version, reason, override_var_name=None):
        """
        Orquestador v2.0: Auto-Sanación + Remediación + Purga
        """
        # --- PASO 0: Auto-Sanación de Infraestructura ---
        constraint_files = [f for f in project_files if f.endswith("dependencyMgmt.gradle")]
        build_gradles = [f for f in project_files if f.endswith("build.gradle")]
        
        if not constraint_files and build_gradles:
            root_folder = os.path.dirname(os.path.abspath(build_gradles[0]))
            new_path = os.path.join(root_folder, "dependencyMgmt.gradle")
            print(f"    🛠️ [AUTO-HEAL] Reconstruyendo infraestructura en {os.path.basename(root_folder)}...")
            with open(new_path, 'w') as f:
                f.write(GradleMutator.INFRA_TEMPLATE)
            
            # Asegurar que el nuevo archivo sea el objetivo de la remediación
            constraint_files = [new_path]
            project_files.append(new_path)
            GradleMutator._link_infrastructure(project_files, root_folder)

        has_changes = False
        definer_file = None
        var_name = None
        current_version = None

        # --- PASO 1: Identificar Variable y Versión Actual ---
        for file_path in project_files:
            if file_path.endswith("build.gradle"):
                with open(file_path, 'r') as f:
                    content = f.read()
                found_var = GradleMutator.find_variable_name_in_ext(content, artifact_name)
                if override_var_name:
                    var_name, definer_file = override_var_name, file_path
                elif found_var:
                    var_name, definer_file = found_var, file_path
                
                if var_name:
                    pattern = rf"{var_name}\s*=\s*['\"]([^'\"]+)['\"]"
                    match = re.search(pattern, content)
                    if match: current_version = match.group(1)
                    break
        
        is_fixed = current_version and GradleMutator.is_already_fixed(current_version, version)
        safe_v = str(version).split(',')[0].strip()

        # --- PASO 2: Definir/Actualizar Variable ---
        if not is_fixed:
            if not definer_file:
                if not build_gradles: return False
                definer_file = min(build_gradles, key=len)
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
                new_content, changed = GradleMutator.update_ext_variable(content, var_name, version)
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

        # --- PASO 4: Sustitución Activa de Literales en todos los build.gradle ---
        for file_path in project_files:
            if file_path.endswith("build.gradle"):
                with open(file_path, 'r') as f:
                    content = f.read()
                content, changed = GradleMutator.substitute_literal_with_variable(content, artifact_name, var_name)
                if changed:
                    with open(file_path, 'w') as f:
                        f.write(content)
                    has_changes = True

        # --- PASO 5: Purga de Variables Redundantes ---
        if definer_file and var_name:
            with open(definer_file, 'r') as f:
                purge_content = f.read()
            clean_content = GradleMutator._purge_redundant_variables(purge_content, var_name)
            if clean_content != purge_content:
                with open(definer_file, 'w') as f:
                    f.write(clean_content)
                has_changes = True

        if has_changes: return True
        return "ALREADY_FIXED" if is_fixed else False
