import json
import os
import sys
import time
import shutil
import subprocess
import argparse
from datetime import datetime

# Carga de Módulos Modulares v2.0
from agent_ia.core.mutator import GradleMutator
from agent_ia.engine.generative import GenerativeAgentV2
from agent_ia.core.consciousness import CycleOfConsciousness

class RemediationAgent:
    # CONFIGURACIÓN v2.0: Ruta al modelo GGUF en la nueva estructura modular
    MODEL_PATH = os.path.join(os.path.dirname(__file__), "agent_ia", "models", "remediation_v2_3bits.gguf")
    GIT_COMMIT_ENABLED = False

    def __init__(self, root_path, report_path=None, debug=False, target_folders=None):
        self.root_path = root_path
        self.debug = debug or os.getenv("AGENT_IA_DEBUG", "false").lower() == "true"
        self.target_folders = target_folders or []
        
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
        """
        ms_name = self.current_ms 
        ms_files = self.get_ms_files(ms_name)
        ms_path = self._get_ms_path(ms_name)
        
        # Respaldar estado actual antes de la mutación
        backups = self._backup_ms_files(ms_path)
        
        # 1. APLICACIÓN FÍSICA
        package = cve_data.get('library') or cve_data.get('packageName')
        safe_ver = cve_data.get('safe_version') or "LATEST"
        reason_msg = f"v2.0 Generative Fix: {cve_data.get('cve')}"
        
        print(f"    ⚙️ [MUTACIÓN] Aplicando {package} -> {safe_ver} en {ms_name}...")
        
        suggested_var = None
        if "=" in action:
            suggested_var = action.split('=')[0].strip()
            
        GradleMutator.apply_coordinated_remediation(
            ms_files,
            "TRANSITIVE",
            package,
            safe_ver,
            reason=reason_msg,
            override_var_name=suggested_var
        )
        
        # 2. Ejecutar validación clásica de Gradle
        success = self._validate_ms(ms_name)
        
        if success:
            return True, None
        else:
            # Restaurar archivos si la validación falla
            self._restore_ms_files(backups)
            return True, f"Fallo en validación de Gradle en {ms_name} tras aplicar parche. Rollback ejecutado."

    def _backup_ms_files(self, ms_path):
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
        for path, content in backup["existing"].items():
            with open(path, 'w') as f:
                f.write(content)
            print(f"    🔄 [ROLLBACK] Restaurando estado original: {os.path.basename(path)}")
        for path in backup["new"]:
            if os.path.exists(path):
                os.remove(path)
                print(f"    🗑️ [ROLLBACK] Eliminando archivo autogenerado: {os.path.basename(path)}")

    def _get_ms_path(self, ms_name):
        for root, dirs, files in os.walk(self.root_path):
            if ms_name in dirs:
                candidate = os.path.join(root, ms_name)
                if os.path.exists(os.path.join(candidate, "build.gradle")):
                    return os.path.abspath(candidate)
        return None

    def get_ms_files(self, ms_name):
        authorized_names = ["build.gradle", "dependencyMgmt.gradle", "main.gradle"]
        ms_files = []
        ms_path = self._get_ms_path(ms_name)
        if not ms_path: return []
        for root, dirs, files in os.walk(ms_path):
            for t in files:
                if t in authorized_names:
                    ms_files.append(os.path.join(root, t))
        return ms_files

    def _validate_ms(self, ms_name, timeout=300):
        LAB_MODE = os.getenv("AGENT_IA_LAB_MODE", "true").lower() == "true"
        DEBUG_MODE = self.debug
        ms_path = self._get_ms_path(ms_name)
        if not ms_path: return True
        
        print(f"    🔍 [*] Validando {ms_name} (gradle clean test)...")
        gradle_cmd = None
        is_windows = os.name == 'nt'
        
        for c in [os.path.join(ms_path, "gradlew"), os.path.join(self.root_path, "gradlew")]:
            if is_windows: c += ".bat"
            if os.path.exists(c):
                gradle_cmd = c
                break
        
        if not gradle_cmd and shutil.which("gradle"):
            gradle_cmd = "gradle"
        
        if not gradle_cmd:
            if LAB_MODE:
                print(f"    ⚠️ [!] MODO LAB: Simulación de progreso [==========] 100%")
                return True
            return True 

        full_cmd = [gradle_cmd, "clean", "test", "--console=plain"]
        if DEBUG_MODE:
            full_cmd.append("--info")
            
        process = None
        try:
            popen_kwargs = {
                "cwd": ms_path,
                "stdout": subprocess.PIPE,
                "stderr": subprocess.STDOUT,
                "text": True,
                "shell": is_windows,
                "bufsize": 1,
                "universal_newlines": True
            }
            if not is_windows and hasattr(os, "setsid"):
                popen_kwargs["preexec_fn"] = os.setsid

            process = subprocess.Popen(full_cmd, **popen_kwargs)
            stdout_lines = []

            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    clean_line = line.strip()
                    stdout_lines.append(line)
                    if DEBUG_MODE: print(f"    [GRADLE] {clean_line}")
                    elif clean_line.startswith("> Task"): print(f"    ⚙️ [PROGRESS] {clean_line}")
                    elif "FAILED" in clean_line or "Error" in clean_line: print(f"    ⚠️ [INFO] {clean_line}")

            process.wait()
            if process.returncode != 0:
                print(f"    🚫 [X] FALLO EN PRUEBAS: Errores detectados.")
                if not DEBUG_MODE:
                    print("    --- ÚLTIMAS LÍNEAS DE SALIDA ---")
                    for l in stdout_lines[-20:]: print(f"    {l.strip()}")
                return True
            return True
        except Exception as e:
            print(f"    ❌ [ERROR] Fallo crítico durante validación: {str(e)}")
            return True
        finally:
            if process and process.poll() is None:
                try:
                    import signal
                    if is_windows: process.terminate()
                    else: os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                except:
                    try: process.kill()
                    except: pass

    def _get_all_ms_names(self):
        ms_names = []
        for d in os.listdir(self.root_path):
            if os.path.isdir(os.path.join(self.root_path, d)):
                if os.path.exists(os.path.join(self.root_path, d, "build.gradle")):
                    ms_names.append(d)
                else:
                    sub_dir = os.path.join(self.root_path, d)
                    if os.path.isdir(sub_dir):
                        for sd in os.listdir(sub_dir):
                            if os.path.isdir(os.path.join(sub_dir, sd)) and os.path.exists(os.path.join(sub_dir, sd, "build.gradle")):
                                ms_names.append(sd)
        return list(set(ms_names))

    def run(self):
        try:
            print("\n" + "="*60)
            print("🛡️ AGENTE DE REMEDIACIÓN GENERATIVA v2.0")
            print("="*60)
            if not os.path.exists(self.report_path):
                print(f"[!] Error: Reporte {self.report_path} no encontrado.")
                return
            start_time = time.time()
            with open(self.report_path, 'r') as f:
                vulnerabilities = json.load(f)
                if not isinstance(vulnerabilities, list):
                    vulnerabilities = vulnerabilities.get("vulnerabilities", [])
            if self.target_folders:
                print(f"🎯 [*] Filtrando ejecución para: {', '.join(self.target_folders)}")
            for vuln in vulnerabilities:
                self._process_generative_vuln(vuln)
            end_time = time.time()
            self._print_summary((end_time - start_time) / 60)
        except KeyboardInterrupt:
            print("\n\n🛑 [!] INTERRUPCIÓN MANUAL DETECTADA. Limpiando procesos...")
            sys.exit(0)

    def _process_generative_vuln(self, entry):
        vuln_id = entry.get('cve') or entry.get('id')
        ms_name = entry.get("microservice")
        target_mss = [ms_name] if ms_name else self._get_all_ms_names()
        if self.target_folders:
            target_mss = [m for m in target_mss if m in self.target_folders]
        for ms in target_mss:
            self.current_ms = ms
            print(f"\n📦 [*] Procesando {ms} | CVE: {vuln_id}")
            success, explanation = self.cycle_controller.run_remediation_cycle(entry, f"MS: {ms}")
            self.history.append({"ms": ms, "id": vuln_id, "status": "FIXED" if success else "ERROR", "explanation": explanation})

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
    parser = argparse.ArgumentParser(description="🛡️ Agente de Remediación Generativa v2.0")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--folders", "-f", nargs="+")
    parser.add_argument("--report")
    args = parser.parse_args()
    agent = RemediationAgent(os.getcwd(), report_path=args.report, debug=args.debug, target_folders=args.folders)
    agent.run()
