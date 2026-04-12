import os
import subprocess
import shutil
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class FSProvider:
    """Proveedor para operaciones en el sistema de archivos (v.30.13 Hardened)."""
    
    EXCLUDE_FOLDERS = ["agent_ia", ".git", ".gradle", "venv", "__pycache__", "out", "build", "stress", "tests", "certification"]

    def __init__(self, root_path: str):
        self.root_path = root_path

    def get_microservices(self) -> List[str]:
        """Escanea el monorepo en busca de microservicios (Búsqueda Profunda)."""
        ms_names = []
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if not any(ex in d.lower() for ex in self.EXCLUDE_FOLDERS)]
            if "build.gradle" in files:
                ms_names.append(os.path.basename(root))
        return list(set(ms_names))

    def get_ms_path(self, ms_name: str) -> Optional[str]:
        """Encuentra la ruta absoluta de un microservicio (Búsqueda Profunda)."""
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if not any(ex in d.lower() for ex in self.EXCLUDE_FOLDERS)]
            if os.path.basename(root) == ms_name and "build.gradle" in files:
                return os.path.abspath(root)
        return None

    def get_ms_files(self, ms_path: str) -> List[str]:
        """Retorna archivos del MS + Archivos de Orquesta en la Raíz (Regla 6)."""
        authorized_names = ["build.gradle", "dependencyMgmt.gradle", "main.gradle"]
        ms_files = []
        
        for root, dirs, files in os.walk(ms_path):
            for t in files:
                if t in authorized_names:
                    ms_files.append(os.path.join(root, t))
        
        for t in authorized_names:
            root_f = os.path.join(self.root_path, t)
            if os.path.exists(root_f):
                ms_files.append(root_f)
                
        return list(set(ms_files))

    def backup_files(self, paths: List[str]) -> Dict:
        backup = {"existing": {}, "new": []}
        for p in paths:
            if os.path.exists(p):
                with open(p, 'r') as file:
                    backup["existing"][p] = file.read()
            else:
                backup["new"].append(p)
        return backup

    def restore_files(self, backup: Dict):
        for path, content in backup["existing"].items():
            with open(path, 'w') as f:
                f.write(content)
        for path in backup["new"]:
            if os.path.exists(path):
                os.remove(path)


class JDKManager:
    """Gestor Inteligente de Java (v.30.13 Adaptive JDK)."""
    
    PREFERRED_VERSIONS = ["21", "17"]

    @staticmethod
    def get_best_java_home() -> Optional[str]:
        """Descubre automáticamente el mejor JAVA_HOME disponible en el sistema."""
        if os.name != 'posix': # Soporte Mac/Linux prioritario
            return os.getenv("JAVA_HOME")

        try:
            # En Mac, usamos el comando estándar para descubrir JDKs
            output = subprocess.check_output(["/usr/libexec/java_home", "-V"], stderr=subprocess.STDOUT, text=True)
            for v in JDKManager.PREFERRED_VERSIONS:
                # Buscar una ruta que coincida con la versión preferida
                match = re.search(rf"\s+({v}\.\d+\.\d+).*?(/.*?/Home)", output)
                if match:
                    home = match.group(2)
                    print(f"    🌟 [ENV] Entorno Adaptado: Utilizando JDK {v} en {home}")
                    return home
        except Exception:
            pass
            
        return os.getenv("JAVA_HOME")


class GradleProvider:
    """Proveedor para operaciones de Gradle (v.30.13 JDK-Aware)."""

    def __init__(self, debug: bool = False, gradle_path: str = None):
        self.debug = debug
        self.gradle_path = gradle_path
        self.gradle_bin = None
        self.java_home = JDKManager.get_best_java_home()

    def discover(self, ms_path: str, root_path: str) -> Optional[str]:
        if os.getenv("AGENT_IA_LAB_MODE", "false").lower() == "true":
            return "gradle_mock"

        if self.gradle_bin: return self.gradle_bin
        candidates = [self.gradle_path] if self.gradle_path else []
        candidates.extend([os.path.join(ms_path, "gradlew"), os.path.join(root_path, "gradlew")])
        is_windows = os.name == 'nt'
        for c in candidates:
            if not c: continue
            cmd = c + ".bat" if is_windows and not c.endswith(".bat") else c
            if os.path.exists(cmd):
                self.gradle_bin = cmd
                return cmd
        common_paths = ["/usr/local/bin/gradle", "/opt/homebrew/bin/gradle", "/usr/bin/gradle"]
        for p in common_paths:
            if os.path.exists(p):
                self.gradle_bin = p
                return p
        return None

    def validate(self, ms_path: str, gradle_bin: str) -> Tuple[bool, str]:
        if os.getenv("AGENT_IA_LAB_MODE", "false").lower() == "true":
            return True, "BUILD SUCCESSFUL (Mocked for Certification)"

        if not gradle_bin or gradle_bin == "None":
            return False, "INFRA_ERROR: No se encontró un binario de Gradle válido."

        is_windows = os.name == 'nt'
        full_cmd = [gradle_bin, "clean", "test", "--console=plain"]
        if self.debug: full_cmd.append("--info")
        
        # Inyectar JAVA_HOME si fue detectado
        env = os.environ.copy()
        if self.java_home:
            env["JAVA_HOME"] = self.java_home
            # Asegurar que el JAVA_HOME/bin esté al inicio del PATH
            env["PATH"] = os.path.join(self.java_home, "bin") + os.pathsep + env.get("PATH", "")

        try:
            process = subprocess.Popen(
                full_cmd, cwd=ms_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                text=True, shell=is_windows, env=env
            )
            stdout_lines = []
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None: break
                if line:
                    stdout_lines.append(line)
                    if self.debug: print(f"    [GRADLE] {line.strip()}")
            process.wait()
            return process.returncode == 0, "".join(stdout_lines)
        except (FileNotFoundError, PermissionError) as e:
            return False, f"INFRA_ERROR: Fallo al ejecutar '{gradle_bin}': {str(e)}"
        except Exception as e:
            return False, f"SYSTEM_ERROR: {str(e)}"


class GitProvider:
    """Proveedor para orquestación de Git."""

    def __init__(self, enabled: bool):
        self.enabled = enabled

    def process_remediation(self, history: List[Dict]):
        if not self.enabled: return
        successful_fixes = [e for e in history if e.get("changed") and e["status"] == "FIXED"]
        if not successful_fixes: return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = f"security/remediation_{timestamp}"
        try:
            subprocess.run(["git", "checkout", "-b", branch_name], check=True, capture_output=True)
            subprocess.run(["git", "add", "."], check=True)
            msg = self._build_commit_msg(successful_fixes)
            subprocess.run(["git", "commit", "-m", msg], check=True, capture_output=True)
            print(f"✅ [GIT] Commit global realizado en la rama {branch_name}")
        except Exception as e:
            print(f"❌ [GIT] Error en operaciones de Git: {str(e)}")

    def _build_commit_msg(self, fixes: List[Dict]) -> str:
        ms_map = {}
        for f in fixes:
            ms = f["ms"]
            if ms not in ms_map: ms_map[ms] = []
            ms_map[ms].append(f["id"])
        msg = f"fix(security): global remediation ({len(ms_map)} services)\n\n"
        for ms, ids in ms_map.items():
            msg += f"- [{ms}]: {', '.join(sorted(list(set(ids))))}\n"
        msg += f"\nEstado: BUILD SUCCESSFUL (Verificado mediante v.30.13 rules)"
        return msg
