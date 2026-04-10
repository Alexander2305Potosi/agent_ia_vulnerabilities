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

        # Match pattern: "group:artifact:version"
        # We look for the exact group:artifact followed by a version string
        pattern = rf"(['\"]{re.escape(package)}:)([\d\.\-\w]+)(['\"])"
        
        def replace_fn(match):
            # We enforce double-quoted interpolation for variables to be safe in Gradle
            return f"{match.group(1)}${{{var_name}}}{match.group(3)}"
            
        new_content, count = re.subn(pattern, replace_fn, content)
        
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
            if group_candidate in families:
                package_or_name = group_candidate
                is_group = True
        
        # Detect si es un grupo (ej. io.netty) o nombre
        if not is_group:
            is_group = any(f in package_or_name.lower() or package_or_name in f for f in families)
        
        match_field = "group" if is_group else "name"
        
        new_rule_full = "if (details.requested." + match_field + " == '" + package_or_name + "') {\n" + \
                        "        details.useVersion \"${" + var_name + "}\"\n" + \
                        "        details.because \"" + reason + "\"\n" + \
                        "    }"
        
        # 1. Update existing rule if it exists (check both name and group patterns)
        pattern_existing = rf"if\s*\(\s*details\.requested\.({match_field})\s*==\s*['\"]{re.escape(package_or_name)}['\"]\s*\)\s*\{{.*?\n\s*\}}"
        if re.search(pattern_existing, content, re.DOTALL):
            return re.sub(pattern_existing, lambda m: new_rule_full, content, flags=re.DOTALL), True

        # 2. Inject into existing eachDependency block
        if "resolutionStrategy.eachDependency" in content:
            # Find the start of the eachDependency closure
            start_keyword = "resolutionStrategy.eachDependency"
            start_index = content.find(start_keyword)
            brace_index = content.find("{", start_index)
            
            if brace_index != -1:
                # Find matching closing brace using stack
                stack = 1
                end_index = -1
                for i in range(brace_index + 1, len(content)):
                    if content[i] == '{': stack += 1
                    elif content[i] == '}': stack -= 1
                    
                    if stack == 0:
                        end_index = i
                        break
                
                if end_index != -1:
                    # Inject BEFORE the closing brace
                    prefix = content[:end_index].rstrip()
                    suffix = content[end_index:]
                    new_content = prefix + "\n    " + new_rule_full + "\n" + suffix
                    return new_content, True

        # 3. Create block from scratch with proper configuration wrapper
        wrapper = """
// Standardized Dependency Management - Centralized AI Security Rules
configurations.all {
    resolutionStrategy.eachDependency { DependencyResolveDetails details ->
        """ + new_rule_full + """
    }
}
"""
        return wrapper.strip(), True

    @staticmethod
    def apply_coordinated_remediation(project_files, strategy, package, version, reason=None):
        artifact_name = package.split(':')[-1]
        
        definer_file = None
        var_name = None
        current_version = None
        dep_mgmt_gradle = next((f for f in project_files if f.endswith("dependencyMgmt.gradle")), None)
        
        # 1. Identify/Update variable
        for file_path in project_files:
            if file_path.endswith("build.gradle"):
                with open(file_path, 'r') as f:
                    content = f.read()
                found_var = GradleMutator.find_variable_name_in_ext(content, artifact_name)
                if found_var:
                    var_name = found_var
                    definer_file = file_path
                    pattern = rf"{var_name}\s*=\s*['\"]([^'\"]+)['\"]"
                    match = re.search(pattern, content)
                    if match: current_version = match.group(1)
                    break
        
        is_fixed = current_version and GradleMutator.is_already_fixed(current_version, version)

        if not is_fixed:
            if not definer_file:
                build_gradles = [f for f in project_files if f.endswith("build.gradle")]
                if not build_gradles: return False
                definer_file = min(build_gradles, key=len)
                parts = artifact_name.split('-')
                var_name = parts[0] + "".join(p.capitalize() for p in parts[1:]) + "Version"
                
                with open(definer_file, 'r') as f:
                    content = f.read()
                if "ext {" in content:
                    new_content = content.replace("ext {", f"ext {{\n        {var_name} = '{version}'")
                else:
                    new_content = f"ext {{\n        {var_name} = '{version}'\n}}\n" + content
                with open(definer_file, 'w') as f:
                    f.write(new_content)
            else:
                with open(definer_file, 'r') as f:
                    content = f.read()
                new_content, _ = GradleMutator.update_ext_variable(content, var_name, version)
                with open(definer_file, 'w') as f:
                    f.write(new_content)
        
        # 2. ACTIVE SUBSTITUTION in all build files
        # We run this even if is_fixed, to ensure hardcoded literals are replaced by the variable
        has_changes = not is_fixed
        for file_path in project_files:
            if file_path.endswith("build.gradle"):
                with open(file_path, 'r') as f:
                    content = f.read()
                content, changed = GradleMutator.substitute_literal_with_variable(content, package, var_name)
                if changed:
                    with open(file_path, 'w') as f:
                        f.write(content)
                        has_changes = True

        # 3. Transitive strategy 
        if strategy == "TRANSITIVE" and dep_mgmt_gradle:
            with open(dep_mgmt_gradle, 'r') as f:
                dmg_content = f.read()
            # v2.0: Pasamos el 'package' completo para permitir detección de familias (groups)
            dmg_content, success = GradleMutator.inject_resolution_strategy_rule(
                dmg_content, package, var_name, reason
            )
            if success:
                # Compare content to avoid false 'mutated' signal
                with open(dep_mgmt_gradle, 'r') as f:
                    old_dmg = f.read()
                if dmg_content != old_dmg:
                    with open(dep_mgmt_gradle, 'w') as f:
                        f.write(dmg_content)
                    has_changes = True

        if has_changes:
            return True
        if is_fixed:
            return "ALREADY_FIXED"
        return False
