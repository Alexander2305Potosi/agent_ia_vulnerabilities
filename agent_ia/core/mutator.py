import re
import os
from typing import List, Dict, Optional, Tuple, Union

class InfrastructureHealer:
    """Maneja la Regla 6: Auto-Sanación de Infraestructura (v.3.0.12)."""
    
    INFRA_TEMPLATE = """// Standardized Dependency Management - Centralized AI Security Rules
configurations.all {
    resolutionStrategy.eachDependency { DependencyResolveDetails details ->
    }
}
"""

    @staticmethod
    def heal_infrastructure(target_folder: str) -> bool:
        changed = False
        dep_mgmt_path = os.path.join(target_folder, "dependencyMgmt.gradle")
        
        if not os.path.exists(dep_mgmt_path):
            print(f"    🛠️ [AUTO-HEAL] Reconstruyendo infraestructura en {os.path.basename(target_folder)}...")
            with open(dep_mgmt_path, 'w') as f: f.write(InfrastructureHealer.INFRA_TEMPLATE)
            changed = True

        if InfrastructureHealer._link_infrastructure(target_folder):
            changed = True
        return changed

    @staticmethod
    def _link_infrastructure(target_folder: str) -> bool:
        main_gradle = os.path.join(target_folder, "main.gradle")
        build_gradle = os.path.join(target_folder, "build.gradle")
        orch = main_gradle if os.path.exists(main_gradle) else build_gradle
        if not os.path.exists(orch): return False

        with open(orch, 'r') as f: content = f.read()
        link_str = 'apply from: "${rootDir}/dependencyMgmt.gradle"'
        if link_str in content: return False

        print(f"    🔗 [SYNC] Vinculando infraestructura en {os.path.basename(orch)}...")
        if "allprojects" in content:
            match = re.search(r"allprojects\s*\{", content)
            if match:
                idx = match.end()
                new_content = content[:idx] + f"\n    {link_str}" + content[idx:]
                with open(orch, 'w') as f: f.write(new_content)
                return True
        
        new_all = f"\n\nallprojects {{\n    {link_str}\n    repositories {{ mavenCentral() }}\n}}\n"
        with open(orch, 'w') as f: f.write(content.rstrip() + new_all)
        return True


class VariableManager:
    """Gestiona variables ext y sustitución de literales (v.3.0.12 - Final Certified)."""
    FAMILIES = ["io.netty", "org.springframework", "com.fasterxml.jackson", "org.apache.logging.log4j"]

    @staticmethod
    def identify_variable(content: str, artifact_name: str, override_name: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        if override_name:
            pattern = rf"\b{re.escape(override_name)}\s*=\s*['\"]([^'\"]+)['\"]"
            match = re.search(pattern, content)
            return override_name, (match.group(1) if match else None)
        
        art_tokens = set(re.split(r'[\.\-\:]', artifact_name.lower()))
        best_var, max_score, cur_val = None, -1, None
        for m in re.finditer(r"(\w+)\s*=\s*['\"]([^'\"]+)['\"]", content):
            name, val = m.groups()
            tokens = {t.lower() for t in re.findall(r'[a-z]+|[A-Z][a-z]*', name)}
            score = len(art_tokens.intersection(tokens))
            if score > max_score and score > 0:
                max_score, best_var, cur_val = score, name, val
        return best_var, cur_val

    @staticmethod
    def update_variable(content: str, var_name: str, version: str) -> Tuple[str, bool]:
        pattern = rf"^\s*\b{var_name}\b\s*=\s*['\"][^'\"]+['\"]"
        new_content, count = re.subn(pattern, f"    {var_name} = '{version}'", content, flags=re.MULTILINE)
        if count == 0:
            if "ext {" in content:
                new_content = content.replace("ext {", f"ext {{\n    {var_name} = '{version}'")
            else:
                new_content = f"ext {{\n    {var_name} = '{version}'\n}}\n" + content
            return new_content, True
        return new_content, True

    @staticmethod
    def substitute_literals(content: str, package: str, var_name: str) -> Tuple[str, bool]:
        """Sustituye literales de versión forzando comillas dobles para interpolación (v.3.0.12)."""
        group = package.split(':')[0]
        is_fam = any(group.startswith(f) for f in VariableManager.FAMILIES)
        match_t = group if is_fam else package
        
        pattern = rf"(['\"]){re.escape(match_t)}:([^: \t'\"]+):[^: \t'\"]+(['\"])"
        
        def sub_fn(m):
            base = f"{match_t}:{m.group(2)}"
            return f'"{base}:${{{var_name}}}"'

        new_content, count = re.subn(pattern, sub_fn, content, flags=re.MULTILINE)
        return new_content, count > 0


class RuleInjector:
    """Motor de Inyección de Reglas (v.3.0.12)."""

    @staticmethod
    def inject_rule(content: str, package: str, var_name: str, reason: str) -> Tuple[str, bool]:
        families = ["io.netty", "org.springframework", "com.fasterxml.jackson", "org.apache.logging.log4j"]
        group = package.split(':')[0]
        match_field = "group" if any(group.startswith(f) for f in families) else "name"
        match_val = group if match_field == "group" else package.split(':')[-1]

        m_sec = re.search(r'CVE-\d{4}-\d+|GHSA-[a-z0-9-]+', reason, re.I)
        s_id = m_sec.group(0) if m_sec else 'Security Fix'
        final_reason = f"Fix: {s_id}"
        
        rule_code = f"if (details.requested.{match_field} == '{match_val}') {{\n            details.useVersion \"${{{var_name}}}\"\n            details.because \"{final_reason}\"\n        }}"

        pattern = rf"details\.requested\.{match_field}\s*==\s*['\"]{re.escape(match_val)}['\"]"
        match = re.search(pattern, content)
        
        if match:
            txt_before = content[:match.start()]
            if_matches = list(re.finditer(r"if\s*\(", txt_before))
            if if_matches:
                if_start = if_matches[-1].start()
                depth = 0
                idx_close = -1
                for i in range(if_start, len(content)):
                    if content[i] == '{': depth += 1
                    elif content[i] == '}':
                        depth -= 1
                        if depth == 0:
                            idx_close = i + 1
                            break
                if idx_close != -1:
                    print(f"    [AUDIT] Regla antigua para {match_val} reemplazada. (Regla 3.3 Success)")
                    return content[:if_start] + rule_code + content[idx_close:], True

        target = "resolutionStrategy.eachDependency"
        if target in content:
            start_search = content.find(target)
            brace_open = content.find("{", start_search)
            if brace_open != -1:
                depth = 1
                idx_close = -1
                for i in range(brace_open + 1, len(content)):
                    if content[i] == '{': depth += 1
                    elif content[i] == '}':
                        depth -= 1
                        if depth == 0:
                            idx_close = i
                            break
                if idx_close != -1:
                    return content[:idx_close].rstrip().replace("// Inject rules here", "") + f"\n        {rule_code}\n    " + content[idx_close:], True
        return content, False


class GradleMutator:
    """Fachada coordinada v.3.0.12 Stable Final."""

    @staticmethod
    def apply_coordinated_remediation(project_files: List[str], mode: str, artifact: str, safe_version_str: str, reason: str, override_var_name: Optional[str] = None) -> Union[bool, str]:
        has_changes = False
        gradles = [f for f in project_files if f.endswith(".gradle")]
        priority = {"build.gradle": 0, "main.gradle": 1}
        root_candidates = sorted(
            [f for f in gradles if os.path.basename(f) in priority],
            key=lambda x: (x.count(os.sep), priority.get(os.path.basename(x), 100))
        )
        root_gradle = root_candidates[0] if root_candidates else None
        if not root_gradle: return False

        if InfrastructureHealer.heal_infrastructure(os.path.dirname(root_gradle)):
            has_changes = True

        v_name, cur_v = None, None
        for f in root_candidates:
            with open(f, 'r') as file:
                v, val = VariableManager.identify_variable(file.read(), artifact, override_var_name)
                if v: 
                    v_name, cur_v = v, val
                    break

        def v_tup(v): 
            if not v: return (0,)
            parts = str(v).split(',')[0].split('-')[0].split('.')
            return tuple(int(p) if p.isdigit() else p for p in parts if p.isdigit())
        
        safe_versions = [s.strip() for s in str(safe_version_str).split(',')]
        is_fixed = False
        if cur_v:
            ct = v_tup(cur_v)
            is_fixed = any(ct[:2] == v_tup(sv)[:2] and ct >= v_tup(sv) for sv in safe_versions)
        
        safe_v = sorted(safe_versions, key=v_tup)[-1]
        if not is_fixed:
            if not v_name:
                parts = artifact.split(':')[-1].split('-')
                v_name = parts[0] + "".join(p.capitalize() for p in parts[1:]) + "Version"
            with open(root_gradle, 'r') as f: content = f.read()
            nc, ch = VariableManager.update_variable(content, v_name, safe_v)
            if ch:
                with open(root_gradle, 'w') as f: f.write(nc)
                has_changes = True

        dep_mgmt = os.path.join(os.path.dirname(root_gradle), "dependencyMgmt.gradle")
        if mode == "TRANSITIVE" and os.path.exists(dep_mgmt):
            with open(dep_mgmt, 'r') as f:
                nc, ch = RuleInjector.inject_rule(f.read(), artifact, v_name, reason)
                if ch: 
                    with open(dep_mgmt, 'w') as f: f.write(nc)
                    has_changes = True

        for f in gradles:
            with open(f, 'r') as file:
                nc, ch = VariableManager.substitute_literals(file.read(), artifact, v_name)
                if ch:
                    with open(f, 'w') as file: file.write(nc)
                    has_changes = True
        return True if has_changes else ("ALREADY_FIXED" if is_fixed else False)
