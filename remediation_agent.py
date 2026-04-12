import json
import os
import sys
import time
import argparse
import re
from datetime import datetime
from typing import List, Dict, Optional

# Orquestador Final v.30.13 (Intelligent Lifecycle)
from agent_ia.core.mutator import GradleMutator
from agent_ia.engine.generative import GenerativeAgentV2
from agent_ia.core.consciousness import CycleOfConsciousness
from agent_ia.core.graph import DependencyGraph
from agent_ia.core.providers import FSProvider, GradleProvider, GitProvider
from agent_ia.models.vulnerability import Vulnerability, RemediationResult

class RemediationAgent:
    """Orquestador Principal v.30.13 (Adaptive Environment)."""
    
    MODEL_PATH = os.path.join(os.path.dirname(__file__), "agent_ia", "models", "remediation_v2_3bits.gguf")

    def __init__(self, root_path: str, report_path: str = None, debug: bool = False, target_folders: List[str] = None, commit_enabled: bool = False, gradle_path: str = None):
        self.root_path = root_path
        self.debug = debug or os.getenv("AGENT_IA_DEBUG", "false").lower() == "true" or os.getenv("AGENT_IA_LAB_MODE", "false").lower() == "true"
        self.target_folders = target_folders or []
        
        self.fs = FSProvider(root_path)
        self.gradle = GradleProvider(debug=self.debug, gradle_path=gradle_path)
        self.git = GitProvider(enabled=commit_enabled)
        
        self.report_path = report_path or os.path.join(os.path.dirname(__file__), "agent_ia", "data", "cve", "snyk_monorepo.json")
        self.history = []
        
        print(f"🚀 [*] Inicializando Cerebro Generativo v.30...")
        self.engine = GenerativeAgentV2(model_path=self.MODEL_PATH if os.path.exists(self.MODEL_PATH) else None)
        self.cycle_controller = CycleOfConsciousness(self.engine, self._validate_and_learn)
        self.current_ms = None

    def _validate_and_learn(self, action: str, attempt: int, cve_data: Dict):
        vuln = Vulnerability(cve_data)
        ms_name = self.current_ms
        ms_path = self.fs.get_ms_path(ms_name)
        if not ms_path: return False, f"Ruta para {ms_name} no encontrada en validación."
        ms_files = self.fs.get_ms_files(ms_path)
        
        backups = self.fs.backup_files(ms_files)
        
        safe_ver = vuln.safe_version.split(',')[0].strip()
        suggested_ver_match = re.search(r"=\s*['\"](.*?)['\"]", action)
        if suggested_ver_match:
            safe_ver = suggested_ver_match.group(1).strip()
            if self.debug: print(f"    🧠 [IA] Usando versión sugerida por el Cerebro: {safe_ver}")

        suggested_var = action.split('=')[0].strip() if "=" in action else None
        
        print(f"    ⚙️ [MUTACIÓN] [{vuln.id}] Aplicando {vuln.library} -> {safe_ver} en {ms_name}...")
        
        did_modify = GradleMutator.apply_coordinated_remediation(
            ms_files, "TRANSITIVE", vuln.library, safe_ver, 
            reason=f"Fix: {vuln.id}", override_var_name=suggested_var
        )
        
        gradle_bin = self.gradle.discover(ms_path, self.root_path)
        if not gradle_bin:
            return False, {"fatal": True, "message": "INFRA_ERROR: No se encontró el binario 'gradle' o 'gradlew'."}
            
        if self.debug: 
            print(f"    🔍 [DEBUG] Usando comando Gradle: {gradle_bin}")

        success, logs = self.gradle.validate(ms_path, gradle_bin)
        
        if success:
            return True, {"changed": did_modify is True}
        else:
            self.fs.restore_files(backups)
            
            # v.30.13: Detección de error fatal de infraestructura (JDK, etc.)
            if isinstance(logs, str) and "INFRA_ERROR" in logs:
                return False, {"fatal": True, "message": logs}

            if self.debug: 
                print(f"    [DEBUG] Fallo en Gradle. Logs resumidos: {logs[:100]}...")
            print(f"    🔄 [ROLLBACK] Validación fallida. Estado restaurado en {ms_name}.")
            return False, f"Fallo en validación de Gradle tras parche. Rollback ejecutado: {logs[:200]}"

    def run(self):
        try:
            print("\n" + "="*60)
            print("🛡️ AGENTE DE REMEDIACIÓN GENERATIVA v.30 (ADAPTIVE)")
            print("="*60)
            
            vulnerabilities = self._load_report()
            if not vulnerabilities: return
            
            if self.target_folders:
                print(f"🎯 [*] Filtrando ejecución para: {', '.join(self.target_folders)}")
            
            for vuln_entry in vulnerabilities:
                self._process_entry(vuln_entry)
            
            self.git.process_remediation(self.history)
            self._print_summary()
            
        except KeyboardInterrupt:
            print("\n\n🛑 [!] INTERRUPCIÓN MANUAL. Abortando...")
            sys.exit(0)

    def _load_report(self) -> List[Dict]:
        if not os.path.exists(self.report_path):
            print(f"[!] Error: Reporte {self.report_path} no encontrado.")
            return []
        with open(self.report_path, 'r') as f:
            data = json.load(f)
            return data if isinstance(data, list) else data.get("vulnerabilities", [])

    def _process_entry(self, entry: Dict):
        vuln = Vulnerability(entry)
        
        potential_mss = []
        if vuln.microservice:
            potential_mss = [vuln.microservice]
        else:
            potential_mss = self.fs.get_microservices()

        for ms in potential_mss:
            if self.target_folders and ms not in self.target_folders:
                continue

            ms_path = self.fs.get_ms_path(ms)
            if not ms_path:
                if self.debug: print(f"    [DEBUG] No se pudo encontrar ruta física para {ms}")
                continue

            self.current_ms = ms
            print(f"📦 [*] Procesando {ms} | CVE: {vuln.id}")

            # Inteligencia de Grafo JDK-Aware (v.30.13)
            lineage_info = "UNKNOWN"
            gradle_bin = self.gradle.discover(ms_path, self.root_path)
            if gradle_bin:
                graph = DependencyGraph(gradle_bin)
                if graph.build_for_project(ms_path):
                    target_id = vuln.id if ":" in vuln.id else vuln.library
                    lineage_info = " -> ".join(graph.get_lineage(target_id))
                    print(f"    🔍 [GRAPH] Paternidad: {lineage_info}")

            success, explanation, metadata = self.cycle_controller.run_remediation_cycle(entry, f"MS: {ms} | Lineage: {lineage_info}")
            
            self.history.append({
                "ms": ms, "id": vuln.id, 
                "status": "FIXED" if success else "ERROR", 
                "explanation": explanation,
                "changed": metadata.get("changed", False) if metadata else False
            })

    def _print_summary(self):
        print("\n" + "="*40)
        print("📊 RESUMEN DE REMEDIACIÓN v.30 (ADAPTIVE)")
        print("="*40)
        for e in self.history:
            icon = "✅" if e["status"] == "FIXED" else "❌"
            print(f"{icon} [{e['ms']}] {e['id']}: {e['status']}")
        print("="*40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="🛡️ Agente de Remediación Generativa v.30.13")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--folders", "-f", nargs="+")
    parser.add_argument("--report")
    parser.add_argument("--commit", "-c", action="store_true")
    parser.add_argument("--gradle-path")
    args = parser.parse_args()
    
    agent = RemediationAgent(os.getcwd(), report_path=args.report, debug=args.debug, target_folders=args.folders, commit_enabled=args.commit, gradle_path=args.gradle_path)
    agent.run()
