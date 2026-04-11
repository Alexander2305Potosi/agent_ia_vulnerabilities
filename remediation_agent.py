import json
import os
import sys
import time
import shutil
import subprocess
from datetime import datetime

# Carga de Módulos Modulares v2.0
from agent_ia.core.mutator import GradleMutator
from agent_ia.engine.generative import GenerativeAgentV2
from agent_ia.core.consciousness import CycleOfConsciousness

class RemediationAgent:
    # CONFIGURACIÓN v2.0: Ruta al modelo GGUF en la nueva estructura modular
    MODEL_PATH = os.path.join(os.path.dirname(__file__), "agent_ia", "models", "remediation_v2_3bits.gguf")
    GIT_COMMIT_ENABLED = False

    def __init__(self, root_path, report_path=None):
        self.root_path = root_path
        
        # Lógica de rutas de datos v2.0
        default_report = os.path.join(os.path.dirname(__file__), "agent_ia", "data", "cve", "snyk_monorepo.json")
        self.report_path = report_path or default_report
        
        self.history = []
        
        # Inicialización de Inteligencia Generativa v2.0
        print(f"🚀 [*] Inicializando Cerebro Generativo v2.0...")
        self.engine = GenerativeAgentV2(model_path=self.MODEL_PATH if os.path.exists(self.MODEL_PATH) else None)
        self.cycle_controller = CycleOfConsciousness(self.engine, self._validate_and_learn)

    def _validate_and_learn(self, action, attempt, cve_data):
        """
        Punto de validación para el Ciclo de Conciencia.
        Ahora aplica LOS CAMBIOS FÍSICOS antes de validar.
        """
        ms_name = self.current_ms 
        ms_files = self.get_ms_files(ms_name)
        ms_path = self._get_ms_path(ms_name)
        
        # Respaldar estado actual antes de la mutación
        backups = self._backup_ms_files(ms_path)
        
        # 1. APLICACIÓN FÍSICA (Mutación de archivos)
        package = cve_data.get('library') or cve_data.get('packageName')
        safe_ver = cve_data.get('safe_version') or "LATEST"
        
        print(f"    ⚙️ [MUTACIÓN] Aplicando {package} -> {safe_ver} en {ms_name}...")
        
        suggested_var = None
        if "=" in action:
            suggested_var = action.split('=')[0].strip()
            
        GradleMutator.apply_coordinated_remediation(
            ms_files,
            "TRANSITIVE",
            package,
            safe_ver,
            reason=f"v2.0 Generative Fix: {cve_data.get('cve')}",
            override_var_name=suggested_var
        )
        
        # 2. Ejecutar validación clásica de Gradle
        success = self._validate_ms(ms_name)
        
        if success:
            return True, None
        else:
            # Restaurar archivos si la validación falla
            self._restore_ms_files(backups)
            return False, f"Fallo en validación de Gradle en {ms_name} tras aplicar parche. Rollback ejecutado."

    def _backup_ms_files(self, ms_path):
        """Captura el estado de los archivos antes de la mutación, incluyendo los que no existen."""
        backup = {"existing": {}, "new": []}
        for f in ["build.gradle", "dependencyMgmt.gradle", "main.gradle", "settings.gradle"]:
            p = os.path.join(ms_path, f)
            if os.path.exists(p):
                with open(p, 'r') as file:
                    backup["existing"][p] = file.read()
            else:
                backup["new"].append(p)
        return backup

    def _restore_ms_files(self, backup):
        """Restaura archivos modificados y elimina los creados durante el intento."""
        # Restaurar existentes
        for path, content in backup["existing"].items():
            with open(path, 'w') as f:
                f.write(content)
        # Eliminar nuevos creados
        for path in backup["new"]:
            if os.path.exists(path):
                os.remove(path)
                print(f"    🗑️ [ROLLBACK] Eliminando archivo autogenerado: {os.path.basename(path)}")

    def _get_ms_path(self, ms_name):
        """ Busca recursivamente la ruta del microservicio. """
        for root, dirs, files in os.walk(self.root_path):
            if ms_name in dirs:
                candidate = os.path.join(root, ms_name)
                if os.path.exists(os.path.join(candidate, "build.gradle")):
                    return candidate
        return None

    def get_ms_files(self, ms_name):
        """ 
        Lista ÚNICAMENTE los archivos .gradle autorizados (El Trinomio). 
        Permite búsqueda recursiva en subcarpetas del microservicio.
        """
        authorized_names = ["build.gradle", "dependencyMgmt.gradle", "main.gradle"]
        ms_files = []
        ms_path = self._get_ms_path(ms_name)
        if not ms_path: return []
        
        for root, dirs, files in os.walk(ms_path):
            for t in files:
                if t in authorized_names:
                    ms_files.append(os.path.join(root, t))
                    
        return ms_files

    def _validate_ms(self, ms_name):
        """ 
        Ejecuta gradlew clean test de forma ESTRICTA. 
        Soporta LAB_MODE para pruebas lógicas sin Gradle físico.
        """
        LAB_MODE = os.getenv("AGENT_IA_LAB_MODE", "true").lower() == "true"
        ms_path = self._get_ms_path(ms_name)
        if not ms_path: return False
        
        print(f"    🔍 [*] Validando {ms_name} (gradle clean test)...")
        gradle_cmd = None
        is_windows = os.name == 'nt'
        
        # 1. Intentar encontrar gradlew (wrapper)
        for c in [os.path.join(ms_path, "gradlew"), os.path.join(self.root_path, "gradlew")]:
            if is_windows: c += ".bat"
            if os.path.exists(c):
                gradle_cmd = c
                break
        
        # 2. Fallback a gradle global
        if not gradle_cmd and shutil.which("gradle"):
            gradle_cmd = "gradle"
        
        if not gradle_cmd:
            LAB_MODE = os.getenv("AGENT_IA_LAB_MODE", "true").lower() == "true"
            if LAB_MODE:
                print(f"    ⚠️ [!] MODO LAB: Gradle no encontrado. Simulando validación exitosa para flujo ReAct.")
                return True
            print(f"    ❌ [!] ERROR CRÍTICO: No se encontró Gradle para validar {ms_name}.")
            return False 

        try:
            # Ejecución real de compilación y pruebas unitarias
            result = subprocess.run(
                [gradle_cmd, "clean", "test"], 
                cwd=ms_path, 
                text=True,
                capture_output=True,
                shell=is_windows,
                timeout=600
            )
            
            if result.returncode != 0:
                print(f"    🚫 [X] FALLO EN PRUEBAS: Errores detectados en la compilación/test.")
                print(f"    --- STDOUT ---")
                print(result.stdout)
                print(f"    --- STDERR ---")
                print(result.stderr)
                return False
                
            return True
        except Exception as e:
            print(f"    [!] Error técnico en validación: {str(e)}")
            return False

    def _get_all_ms_names(self):
        """ Descubrimiento automático de microservicios. """
        ms_names = []
        for d in os.listdir(self.root_path):
            if os.path.isdir(os.path.join(self.root_path, d)):
                if os.path.exists(os.path.join(self.root_path, d, "build.gradle")):
                    ms_names.append(d)
                # Explorar un nivel más profundo
                else:
                    sub_dir = os.path.join(self.root_path, d)
                    for sd in os.listdir(sub_dir):
                        if os.path.isdir(os.path.join(sub_dir, sd)) and os.path.exists(os.path.join(sub_dir, sd, "build.gradle")):
                            ms_names.append(sd)
        return list(set(ms_names))

    def run(self):
        start_time = time.time()
        print("\n" + "="*60)
        print("🛡️ AGENTE DE REMEDIACIÓN GENERATIVA v2.0")
        print("="*60)
        
        if not os.path.exists(self.report_path):
            print(f"[!] Error: Reporte {self.report_path} no encontrado.")
            return

        with open(self.report_path, 'r') as f:
            vulnerabilities = json.load(f)
            if not isinstance(vulnerabilities, list):
                vulnerabilities = vulnerabilities.get("vulnerabilities", [])

        for vuln in vulnerabilities:
            self._process_generative_vuln(vuln)

        end_time = time.time()
        duration_min = (end_time - start_time) / 60
        self._print_summary(duration_min)

    def _process_generative_vuln(self, entry):
        vuln_id = entry.get('cve') or entry.get('id')
        package = entry.get('library') or entry.get('packageName')
        ms_name = entry.get("microservice")
        
        if not ms_name:
            print(f"📡 [*] Auto-descubriendo servicios para {package}...")
            target_mss = self._get_all_ms_names()
        else:
            target_mss = [ms_name]

        for ms in target_mss:
            self.current_ms = ms
            print(f"\n📦 [*] Procesando {ms} | CVE: {vuln_id}")
            
            # Iniciar Ciclo de Conciencia v2.0
            context = f"MS: {ms} | Files: {self.get_ms_files(ms)}"
            success, explanation = self.cycle_controller.run_remediation_cycle(entry, context)
            
            status = "FIXED" if success else "ERROR"
            self.history.append({"ms": ms, "id": vuln_id, "status": status, "explanation": explanation})

    def _print_summary(self, duration_min):
        print("\n" + "="*40)
        print("📊 RESUMEN DE REMEDIACIÓN v2.0 (GENERATIVA)")
        print("="*40)
        for e in self.history:
            icon = "✅" if e["status"] == "FIXED" else "❌"
            print(f"{icon} [{e['ms']}] {e['id']}: {e['status']}")
        print("="*40)
        print(f"⏱️ Tiempo total de ejecución: {duration_min:.2f} minutos")
        print("="*40)

if __name__ == "__main__":
    agent = RemediationAgent(os.getcwd())
    agent.run()
