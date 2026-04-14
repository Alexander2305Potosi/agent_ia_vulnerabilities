import json
import os
import sys
import argparse
import re
from typing import List, Dict, Optional

# Agente de Remediación v.3.0 — Módulos consolidados
from agent_ia.core import (
    GradleMutator, Vulnerability,
    FSProvider, GradleProvider, GitProvider,
    DependencyGraph, CycleOfConsciousness,
    _normalize_ms_name
)
from agent_ia.brain import GenerativeAgentV2


# ---------------------------------------------------------------------------
# RollbackManager — Protección de Estado (Zero-Risk)
# ---------------------------------------------------------------------------

class RollbackManager:
    """Encapsula las operaciones de Backup y Restore para Rollback Zero-Risk."""

    def __init__(self, fs: FSProvider):
        self.fs = fs

    def snapshot(self, ms_files: List[str]) -> Dict[str, str]:
        return self.fs.backup_files(ms_files)

    def restore(self, backups: Dict[str, str], ms_name: str) -> None:
        self.fs.restore_files(backups)
        print(f"    🔄 [ROLLBACK] Validación fallida. Estado restaurado en {ms_name}.")


# ---------------------------------------------------------------------------
# RemediationAgent — Orquestador Principal v.3.0
# ---------------------------------------------------------------------------

class RemediationAgent:
    """Orquestador Principal v.3.0 (Adaptive Environment)."""

    MODEL_PATH = os.path.join(os.path.dirname(__file__), "agent_ia", "models", "remediation_v2_3bits.gguf")
    DEFAULT_REPORT = os.path.join(os.path.dirname(__file__), "agent_ia", "data", "cve", "snyk_monorepo.json")

    def __init__(
        self,
        root_path: str,
        report_path: str = None,
        debug: bool = False,
        target_folders: List[str] = None,
        commit_enabled: bool = False,
        gradle_path: str = None,
    ):
        self.root_path = root_path
        self.debug = (
            debug
            or os.getenv("AGENT_IA_DEBUG", "false").lower() == "true"
            or os.getenv("AGENT_IA_LAB_MODE", "false").lower() == "true"
        )
        self.target_folders = target_folders or []
        self.report_path = report_path or self.DEFAULT_REPORT
        self.history: List[Dict] = []
        self.current_ms: Optional[str] = None

        self.fs = FSProvider(root_path)
        self.gradle = GradleProvider(debug=self.debug, gradle_path=gradle_path)
        self.git = GitProvider(enabled=commit_enabled)
        self.rollback = RollbackManager(self.fs)

        print("🚀 [*] Inicializando Cerebro Generativo v.3.0...")
        self.engine = GenerativeAgentV2(
            model_path=self.MODEL_PATH if os.path.exists(self.MODEL_PATH) else None
        )
        self.cycle_controller = CycleOfConsciousness(self.engine, self._validate_and_learn)

    # ------------------------------------------------------------------
    # Ciclo Principal
    # ------------------------------------------------------------------

    def run(self):
        try:
            self._print_header()
            vulnerabilities = self._load_report()
            if not vulnerabilities:
                return

            if self.target_folders:
                if not self._validate_target_folders():
                    print("\n🛑 [!] ERROR: Ninguna de las carpetas especificadas existe en el workspace.")
                    print("    Asegúrate de que los nombres coincidan exactamente con las carpetas en el disco.")
                    return

            for entry in vulnerabilities:
                self._process_entry(entry)

            self.git.process_remediation(self.history)
            self._print_summary()

        except KeyboardInterrupt:
            print("\n\n🛑 [!] INTERRUPCIÓN MANUAL. Abortando...")
            sys.exit(0)

    # ------------------------------------------------------------------
    # Procesamiento por Entrada
    # ------------------------------------------------------------------

    def _process_entry(self, entry: Dict):
        vuln = Vulnerability(entry)
        microservices = [vuln.microservice] if vuln.microservice else self.fs.get_microservices()

        for ms in microservices:
            # Normalización para matching adaptativo
            ms_norm = _normalize_ms_name(ms)
            targets_norm = [_normalize_ms_name(t) for t in self.target_folders]
            
            if self.target_folders and ms_norm not in targets_norm:
                continue

            ms_path = self.fs.get_ms_path(ms)
            if not ms_path:
                if self.debug:
                    print(f"    [DEBUG] No se pudo encontrar ruta física para {ms}")
                continue

            self.current_ms = ms
            print(f"📦 [*] Procesando {ms} | CVE: {vuln.id}")

            lineage_info = self._build_lineage(ms_path, vuln)
            success, explanation, metadata = self.cycle_controller.run_remediation_cycle(
                entry, f"MS: {ms} | Lineage: {lineage_info}"
            )

            self.history.append({
                "ms": ms,
                "id": vuln.id,
                "status": "FIXED" if success else "ERROR",
                "explanation": explanation,
                "changed": metadata.get("changed", False) if metadata else False,
            })

    def _validate_target_folders(self) -> bool:
        """Valida que las carpetas solicitadas por el usuario existan físicamente."""
        print(f"🎯 [*] Filtrando ejecución para: {', '.join(self.target_folders)}")
        valid_folders = []
        # Normalizar para permitir flexibilidad en la verificación inicial
        for folder in self.target_folders:
            path = self.fs.get_ms_path(folder)
            if path:
                valid_folders.append(folder)
            else:
                print(f"    [!] WARNING: La carpeta '{folder}' no fue encontrada en el workspace.")
        
        return len(valid_folders) > 0

    def _build_lineage(self, ms_path: str, vuln: Vulnerability) -> str:
        gradle_bin = self.gradle.discover(ms_path, self.root_path)
        if not gradle_bin:
            return "UNKNOWN"
        graph = DependencyGraph(gradle_bin)
        if not graph.build_for_project(ms_path):
            return "UNKNOWN_ORIGIN"
        target_id = vuln.id if ":" in vuln.id else vuln.library
        lineage = " -> ".join(graph.get_lineage(target_id))
        print(f"    🔍 [GRAPH] Paternidad: {lineage}")
        return lineage

    # ------------------------------------------------------------------
    # Callback de Validación (invocado por CycleOfConsciousness)
    # ------------------------------------------------------------------

    def _validate_and_learn(self, action: str, attempt: int, cve_data: Dict):
        vuln = Vulnerability(cve_data)
        ms_path = self.fs.get_ms_path(self.current_ms)
        if not ms_path:
            return False, f"Ruta para {self.current_ms} no encontrada en validación."

        ms_files = self.fs.get_ms_files(ms_path)
        backups = self.rollback.snapshot(ms_files)

        safe_ver = self._extract_version(action, vuln)
        suggested_var = action.split('=')[0].strip() if "=" in action else None

        print(f"        ⚙️ [MUTACIÓN] [{vuln.id}] Aplicando {vuln.library} -> {safe_ver} en {self.current_ms}...")

        GradleMutator.apply_coordinated_remediation(
            ms_files, "TRANSITIVE", vuln.library, safe_ver,
            reason=f"Fix: {vuln.id}", override_var_name=suggested_var,
        )

        gradle_bin = self.gradle.discover(ms_path, self.root_path)
        if not gradle_bin:
            return False, {"fatal": True, "message": "INFRA_ERROR: No se encontró el binario 'gradle' o 'gradlew'."}

        if self.debug:
            print(f"    🔍 [DEBUG] Usando comando Gradle: {gradle_bin}")

        success, logs = self.gradle.validate(ms_path, gradle_bin)
        if success:
            return True, {"changed": True}

        self.rollback.restore(backups, self.current_ms)
        if isinstance(logs, str) and "INFRA_ERROR" in logs:
            return False, {"fatal": True, "message": logs}
        if self.debug:
            print(f"    [DEBUG] Fallo en Gradle. Logs resumidos: {logs[:100]}...")
        return False, f"Fallo en validación de Gradle tras parche. Rollback ejecutado: {logs[:200]}"

    def _extract_version(self, action: str, vuln: Vulnerability) -> str:
        match = re.search(r"=\s*['\"](.*?)['\"]", action)
        if match:
            version = match.group(1).strip()
            if self.debug:
                print(f"    🧠 [IA] Usando versión sugerida por el Cerebro: {version}")
            return version
        return vuln.safe_version.split(',')[0].strip()

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------

    def _load_report(self) -> List[Dict]:
        if not os.path.exists(self.report_path):
            print(f"[!] Error: Reporte {self.report_path} no encontrado.")
            return []
        with open(self.report_path, 'r') as f:
            data = json.load(f)
        return data if isinstance(data, list) else data.get("vulnerabilities", [])

    def _print_header(self):
        print("\n" + "=" * 60)
        print("🛡️ AGENTE DE REMEDIACIÓN GENERATIVA v.3.0 (ADAPTIVE)")
        print("=" * 60)

    def _print_summary(self):
        print("\n" + "=" * 40)
        print("📊 RESUMEN DE REMEDIACIÓN v.3.0 (ADAPTIVE)")
        print("=" * 40)
        for e in self.history:
            icon = "✅" if e["status"] == "FIXED" else "❌"
            print(f"{icon} [{e['ms']}] {e['id']}: {e['status']}")
        print("=" * 40)


# ---------------------------------------------------------------------------
# Punto de Entrada CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="🛡️ Agente de Remediación Generativa v.3.0")
    parser.add_argument("--debug", action="store_true", help="Habilitar modo de depuración")
    parser.add_argument("--folders", "-f", nargs="+", help="Filtrar microservicios por nombre")
    parser.add_argument("--report", help="Ruta alternativa al reporte JSON de vulnerabilidades")
    parser.add_argument("--commit", "-c", action="store_true", help="Activar commits automáticos post-remediación")
    parser.add_argument("--gradle-path", help="Ruta explícita al binario de Gradle")
    args = parser.parse_args()

    agent = RemediationAgent(
        root_path=os.getcwd(),
        report_path=args.report,
        debug=args.debug,
        target_folders=args.folders,
        commit_enabled=args.commit,
        gradle_path=args.gradle_path,
    )
    agent.run()
