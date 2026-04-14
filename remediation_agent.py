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
from agent_ia.vulnerability_classifier import VulnerabilityClassifier
from agent_ia.long_term_memory import LongTermMemory, RemediationDecision
from agent_ia.smart_rollback import SmartRollbackManager
from agent_ia.dry_run_mode import DryRunMode
from agent_ia.config_manager import ConfigManager


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
    """Orquestador Principal v.3.0 (Adaptive Environment + Mejoras)."""

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
        dry_run: bool = False,
    ):
        self.root_path = root_path
        self.debug = (
            debug
            or os.getenv("AGENT_IA_DEBUG", "false").lower() == "true"
            or os.getenv("AGENT_IA_LAB_MODE", "false").lower() == "true"
        )
        self.dry_run = dry_run or os.getenv("AGENT_DRY_RUN", "false").lower() == "true"
        self.target_folders = target_folders or []
        self.report_path = report_path or self.DEFAULT_REPORT
        self.history: List[Dict] = []
        self.current_ms: Optional[str] = None

        # Configuración declarativa
        self.config = ConfigManager(root_path)
        print(f"🚀 [*] Agente v.3.0 | Proyecto: {self.config.config.project_name}")

        self.fs = FSProvider(root_path)
        self.gradle = GradleProvider(debug=self.debug, gradle_path=gradle_path)
        self.git = GitProvider(enabled=commit_enabled and not self.dry_run)
        self.rollback = RollbackManager(self.fs)
        self.smart_rollback = SmartRollbackManager()

        # Memoria a largo plazo
        self.memory = LongTermMemory(project_id=self.config.config.project_name)

        # Modo dry-run
        self.dry_run_mode = DryRunMode() if self.dry_run else None

        print("🚀 [*] Inicializando Cerebro Generativo v.3.0 (con Prompt Caching)...")
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

            # Diagnóstico inicial
            if self.debug:
                print(f"    [DEBUG] Directorio raíz: {self.root_path}")
                print(f"    [DEBUG] Reporte: {self.report_path}")
                all_ms = self.fs.get_microservices()
                print(f"    [DEBUG] Microservicios detectados: {all_ms}")

            vulnerabilities = self._load_report()
            if not vulnerabilities:
                print("[!] No se encontraron vulnerabilidades en el reporte.")
                return

            print(f"[*] Cargadas {len(vulnerabilities)} vulnerabilidades del reporte")

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

        # Clasificación de vulnerabilidad
        classified = VulnerabilityClassifier.classify(entry)
        if self.debug:
            print(f"    [CLASSIFIER] {vuln.id}: Score {classified.base_score:.1f}, "
                  f"Severity: {classified.severity.name}, "
                  f"Priority: {classified.remediation_priority:.1f}")

        # Determinar microservicios a procesar
        if self.target_folders:
            microservices = self.target_folders
        else:
            microservices = self.fs.get_microservices()

        if self.debug:
            print(f"    [DEBUG] Microservicios a procesar: {microservices}")

        for ms in microservices:
            # Verificar si debe ser ignorada para este microservicio
            if self.config.should_skip_vulnerability(ms, vuln.id):
                print(f"    [SKIP] {vuln.id} está en lista de exclusiones para {ms}")
                continue

            ms_path = self.fs.get_ms_path(ms)
            if not ms_path:
                print(f"    [ERROR] No se encontró ruta para microservicio: {ms}")
                print(f"            Buscando: '{_normalize_ms_name(ms)}'")
                continue

            self.current_ms = ms

            # Verificar si microservicio está habilitado
            if not self.config.is_microservice_enabled(ms):
                print(f"    [SKIP] {ms} está deshabilitado en la configuración")
                continue

            print(f"📦 [*] Procesando {ms} | CVE: {vuln.id} | Priority: {classified.severity.name}")
            print(f"    [PATH] Ruta: {ms_path}")

            lineage_info = self._build_lineage(ms_path, vuln)

            # Modo dry-run: preview de cambios
            if self.dry_run:
                self._preview_remediation(ms_path, vuln, classified)
                continue

            # Verificar versión actual antes de mutar
            ms_files = self.fs.get_ms_files(ms_path)
            if self.debug:
                print(f"    [DEBUG] Archivos del MS: {len(ms_files)} archivos")
                for f in ms_files[:3]:
                    print(f"            - {f}")

            success, explanation, metadata = self.cycle_controller.run_remediation_cycle(
                entry, f"MS: {ms} | Lineage: {lineage_info}"
            )

            # Verificar si realmente hubo cambios
            actually_changed = metadata.get("changed", False) if metadata else False
            already_fixed = metadata.get("already_fixed", False) if metadata else False

            # Determinar status más preciso
            if not success:
                status = "ERROR"
            elif already_fixed:
                status = "ALREADY_FIXED"
            elif actually_changed:
                status = "FIXED"
            else:
                status = "NO_CHANGE"

            if success and not actually_changed and not already_fixed:
                print(f"    [WARNING] {vuln.id} marcado como exitoso pero sin cambios aplicados")

            # Guardar en memoria
            decision = RemediationDecision(
                cve_id=vuln.id,
                library=vuln.library,
                microservice=ms,
                attempted_action=explanation if not success else "remediation_applied",
                success=success,
                error_message=explanation if not success else None
            )
            self.memory.record_decision(decision)

            self.history.append({
                "ms": ms,
                "id": vuln.id,
                "status": status,
                "explanation": explanation,
                "changed": actually_changed,
                "already_fixed": already_fixed,
            })

    def _preview_remediation(self, ms_path: str, vuln: Vulnerability, classified):
        """Modo dry-run: muestra preview sin aplicar cambios."""
        print(f"\n    [DRY-RUN] Preview para {vuln.id}")

        # Simular cambios
        ms_files = self.fs.get_ms_files(ms_path)
        files_before = {f: open(f).read() if os.path.exists(f) else "" for f in ms_files}
        files_after = files_before.copy()

        # Crear preview de cambios (simulado)
        previews = self.dry_run_mode.simulate_remediation(
            cve_id=vuln.id,
            library=vuln.library,
            safe_version=vuln.safe_version.split(',')[0] if ',' in vuln.safe_version else vuln.safe_version,
            project_files=files_before,
            proposed_changes=files_after  # En dry-run no hay cambios reales
        )

        self.dry_run_mode.print_full_report(
            vuln.id, vuln.library, vuln.safe_version, previews
        )

    def _validate_target_folders(self) -> bool:
        """Valida que las carpetas solicitadas por el usuario existan físicamente."""
        print(f"🎯 [*] Filtrando ejecución para: {', '.join(self.target_folders)}")
        valid_folders = []
        not_found = []

        for folder in self.target_folders:
            path = self.fs.get_ms_path(folder)
            if path:
                valid_folders.append(folder)
            else:
                not_found.append(folder)

        if not_found:
            print(f"    [!] WARNING: Las siguientes carpetas no fueron encontradas: {', '.join(not_found)}")
            print(f"    [!] Microservicios disponibles: {', '.join(self.fs.get_microservices())}")
            return False

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

        # Aplicar remediación y verificar si hubo cambios reales
        remediation_result = GradleMutator.apply_coordinated_remediation(
            ms_files, "TRANSITIVE", vuln.library, safe_ver,
            reason=f"Fix: {vuln.id}", override_var_name=suggested_var,
        )

        # Analizar resultado de la remediación
        if remediation_result == "ALREADY_FIXED":
            print(f"        [INFO] {vuln.id} ya estaba corregido, no se requieren cambios")
            return True, {"changed": False, "already_fixed": True}
        elif remediation_result == False:
            print(f"        [ERROR] No se pudo aplicar la remediación para {vuln.id}")
            return False, {"fatal": False, "message": "No se pudo aplicar la remediación"}

        # Solo si hubo cambios reales, validar el build
        has_changes = remediation_result == True

        if self.debug:
            print(f"    [DEBUG] Cambios aplicados: {has_changes}")

        gradle_bin = self.gradle.discover(ms_path, self.root_path)
        if not gradle_bin:
            return False, {"fatal": True, "message": "INFRA_ERROR: No se encontró el binario 'gradle' o 'gradlew'."}

        if self.debug:
            print(f"    🔍 [DEBUG] Usando comando Gradle: {gradle_bin}")

        success, logs = self.gradle.validate(ms_path, gradle_bin)
        if success:
            return True, {"changed": has_changes}

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
        print("\n" + "=" * 50)
        print("📊 RESUMEN DE REMEDIACIÓN v.3.0 (ADAPTIVE)")
        print("=" * 50)

        # Agrupar por estado
        fixed = [e for e in self.history if e["status"] == "FIXED"]
        already_fixed = [e for e in self.history if e["status"] == "ALREADY_FIXED"]
        errors = [e for e in self.history if e["status"] == "ERROR"]

        if fixed:
            print("\n✅ REPARADOS (cambios aplicados):")
            for e in fixed:
                print(f"   • [{e['ms']}] {e['id']}")

        if already_fixed:
            print("\n✓ YA ESTABAN REPARADOS (sin cambios):")
            for e in already_fixed:
                print(f"   • [{e['ms']}] {e['id']}")

        if errors:
            print("\n❌ ERRORES:")
            for e in errors:
                print(f"   • [{e['ms']}] {e['id']}: {e.get('explanation', 'Unknown error')[:50]}")

        # Estadísticas
        total = len(self.history)
        if total > 0:
            print(f"\n📈 Estadísticas:")
            print(f"   Total procesados: {total}")
            print(f"   Reparados ahora: {len(fixed)}")
            print(f"   Ya reparados: {len(already_fixed)}")
            print(f"   Errores: {len(errors)}")

        print("=" * 50)


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
    parser.add_argument("--dry-run", "-n", action="store_true", help="Modo simulación - mostrar cambios sin aplicar")
    parser.add_argument("--learning-summary", action="store_true", help="Mostrar resumen de aprendizaje y salir")
    parser.add_argument("--generate-config", action="store_true", help="Generar archivo .remediation.yaml por defecto")
    args = parser.parse_args()

    # Generar configuración por defecto si se solicita
    if args.generate_config:
        config_mgr = ConfigManager(os.getcwd())
        config_mgr.save_default_config()
        exit(0)

    agent = RemediationAgent(
        root_path=os.getcwd(),
        report_path=args.report,
        debug=args.debug,
        target_folders=args.folders,
        commit_enabled=args.commit,
        gradle_path=args.gradle_path,
        dry_run=args.dry_run,
    )

    # Mostrar resumen de aprendizaje si se solicita
    if args.learning_summary:
        summary = agent.memory.get_learning_summary()
        print("\n" + "=" * 60)
        print("🧠 RESUMEN DE APRENDIZAJE DEL AGENTE")
        print("=" * 60)
        print(f"Total decisiones: {summary['total_decisions']}")
        print(f"Tasa de éxito: {summary['success_rate']:.1f}%")
        print(f"Patrones de éxito: {summary['success_patterns']}")
        print(f"Patrones de fallo: {summary['failure_patterns']}")
        print("\nTipos de fallo más comunes:")
        for failure in summary['common_failure_types']:
            print(f"  • {failure['type']}: {failure['count']} ocurrencias")
        print("=" * 60)
        exit(0)

    agent.run()
