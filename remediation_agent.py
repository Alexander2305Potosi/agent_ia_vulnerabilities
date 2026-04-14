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
from agent_ia.core.logging_utils import logger, set_log_context, clear_log_context
from agent_ia.core.shutdown_manager import shutdown_manager, setup_graceful_shutdown, ProcessContext


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
        logger.warning(f"Rollback ejecutado: Estado restaurado en {ms_name}", indent=2)


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
        logger.info(f"Agente v.3.0 | Proyecto: {self.config.config.project_name}")

        self.fs = FSProvider(root_path)
        self.gradle = GradleProvider(debug=self.debug, gradle_path=gradle_path)
        self.git = GitProvider(enabled=commit_enabled and not self.dry_run)
        self.rollback = RollbackManager(self.fs)
        self.smart_rollback = SmartRollbackManager()

        # Memoria a largo plazo
        self.memory = LongTermMemory(project_id=self.config.config.project_name)

        # Modo dry-run
        self.dry_run_mode = DryRunMode() if self.dry_run else None

        logger.start("Inicializando Cerebro Generativo v.3.0 (con Prompt Caching)...")
        self.engine = GenerativeAgentV2(
            model_path=self.MODEL_PATH if os.path.exists(self.MODEL_PATH) else None
        )
        self.cycle_controller = CycleOfConsciousness(self.engine, self._validate_and_learn)

    # ------------------------------------------------------------------
    # Ciclo Principal
    # ------------------------------------------------------------------

    def run(self):
        # Configurar manejo graceful de señales
        setup_graceful_shutdown()

        # Registrar funciones de limpieza
        shutdown_manager.register_cleanup_function(self._cleanup_resources)

        try:
            self._print_header()

            # Diagnóstico inicial
            if self.debug:
                logger.debug(f"Directorio raíz: {self.root_path}")
                logger.debug(f"Reporte: {self.report_path}")
                all_ms = self.fs.get_microservices()
                logger.debug(f"Microservicios detectados: {all_ms}")

            vulnerabilities = self._load_report()
            if not vulnerabilities:
                logger.warning("No se encontraron vulnerabilidades en el reporte.")
                return

            logger.info(f"Cargadas {len(vulnerabilities)} vulnerabilidades del reporte")

            if self.target_folders:
                if not self._validate_target_folders():
                    logger.error("Ninguna de las carpetas especificadas existe en el workspace.")
                    logger.info("Asegúrate de que los nombres coincidan exactamente con las carpetas en el disco.")
                    return

            for entry in vulnerabilities:
                # Verificar si se solicitó interrupción
                if shutdown_manager.is_shutting_down():
                    logger.warning("Interrupción detectada. Deteniendo procesamiento...")
                    break

                self._process_entry(entry)

            self.git.process_remediation(self.history)
            self._print_summary()

        except KeyboardInterrupt:
            # El manejador de señales se encargará del cierre graceful
            pass
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            raise

    def _cleanup_resources(self):
        """Limpia recursos al cerrar la aplicación."""
        try:
            logger.info("Limpiando recursos...")

            # Cerrar conexiones de Gradle si existen
            if hasattr(self, 'gradle') and self.gradle:
                logger.debug("Cerrando conexiones de Gradle...")
                # No hay método explícito de cierre, pero podemos limpiar referencias
                self.gradle = None

            # Liberar referencias a objetos grandes
            if hasattr(self, 'cycle_controller'):
                self.cycle_controller = None

            if hasattr(self, 'engine'):
                self.engine = None

            logger.info("Recursos liberados correctamente")

        except Exception as e:
            logger.error(f"Error durante la limpieza de recursos: {e}")

    # ------------------------------------------------------------------
    # Procesamiento por Entrada
    # ------------------------------------------------------------------

    def _process_entry(self, entry: Dict):
        vuln = Vulnerability(entry)

        # Clasificación de vulnerabilidad
        classified = VulnerabilityClassifier.classify(entry)
        if self.debug:
            logger.debug(f"{vuln.id}: Score {classified.base_score:.1f}, Severity: {classified.severity.name}, Priority: {classified.remediation_priority:.1f}")

        # Determinar microservicios a procesar
        if self.target_folders:
            microservices = self.target_folders
        else:
            microservices = self.fs.get_microservices()

        if self.debug:
            logger.debug(f"Microservicios a procesar: {microservices}")

        for ms in microservices:
            # Establecer contexto para logs
            set_log_context(ms=ms, cve=vuln.id)
            logger.start_cve(vuln.id, vuln.library, classified.severity.name)

            # Verificar si debe ser ignorada para este microservicio
            if self.config.should_skip_vulnerability(ms, vuln.id):
                logger.warning(f"{vuln.id} está en lista de exclusiones para {ms}")
                clear_log_context()
                continue

            ms_path = self.fs.get_ms_path(ms)
            if not ms_path:
                logger.error(f"No se encontró ruta para microservicio: {ms}")
                logger.info(f"Buscando: '{_normalize_ms_name(ms)}'")
                clear_log_context()
                continue

            self.current_ms = ms

            # Verificar si microservicio está habilitado
            if not self.config.is_microservice_enabled(ms):
                logger.warning(f"{ms} está deshabilitado en la configuración")
                clear_log_context()
                continue

            logger.info(f"Procesando {ms} | CVE: {vuln.id} | Priority: {classified.severity.name}")
            logger.step("Ruta del MS", "INFO", ms_path)

            lineage_info = self._build_lineage(ms_path, vuln)

            # Modo dry-run: preview de cambios
            if self.dry_run:
                self._preview_remediation(ms_path, vuln, classified)
                clear_log_context()
                continue

            # Verificar versión actual antes de mutar
            ms_files = self.fs.get_ms_files(ms_path)
            if self.debug:
                logger.debug(f"Archivos del MS: {len(ms_files)} archivos", indent=2)
                for f in ms_files[:3]:
                    logger.debug(f"  - {f}", indent=3)

            # Ejecutar ciclo de remediación
            logger.step("Ciclo de Remediación", "START")
            success, explanation, metadata = self.cycle_controller.run_remediation_cycle(
                entry, f"MS: {ms} | Lineage: {lineage_info}"
            )

            # Verificar si realmente hubo cambios
            actually_changed = metadata.get("changed", False) if metadata else False
            already_fixed = metadata.get("already_fixed", False) if metadata else False

            # Determinar status más preciso
            if not success:
                status = "ERROR"
                logger.step("Ciclo de Remediación", "FAIL", explanation[:50])
                logger.fail_cve(vuln.id, explanation)
            elif already_fixed:
                status = "ALREADY_FIXED"
                logger.step("Ciclo de Remediación", "DONE", "Ya estaba corregido")
                logger.success(f"{vuln.id} ya estaba corregido")
            elif actually_changed:
                status = "FIXED"
                logger.step("Ciclo de Remediación", "DONE", "Cambios aplicados exitosamente")
                logger.success_cve(vuln.id, "remediado")
            else:
                status = "NO_CHANGE"
                logger.step("Ciclo de Remediación", "SKIP", "Sin cambios detectados")
                logger.warning(f"{vuln.id} marcado como exitoso pero sin cambios aplicados")

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

            clear_log_context()

    def _preview_remediation(self, ms_path: str, vuln: Vulnerability, classified):
        """Modo dry-run: muestra preview sin aplicar cambios."""
        logger.info(f"Preview de cambios para {vuln.id}", indent=2)

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
        logger.start(f"Filtrando ejecución para: {', '.join(self.target_folders)}")
        valid_folders = []
        not_found = []

        for folder in self.target_folders:
            path = self.fs.get_ms_path(folder)
            if path:
                valid_folders.append(folder)
            else:
                not_found.append(folder)

        if not_found:
            logger.warning(f"Carpetas no encontradas: {', '.join(not_found)}")
            logger.info(f"Microservicios disponibles: {', '.join(self.fs.get_microservices())}")
            return False

        logger.success(f"Carpetas validadas: {', '.join(valid_folders)}")
        return True

    def _build_lineage(self, ms_path: str, vuln: Vulnerability) -> str:
        logger.step("Análisis de Dependencias", "START")
        gradle_bin = self.gradle.discover(ms_path, self.root_path)
        if not gradle_bin:
            logger.warning("No se encontró binario de Gradle", indent=2)
            return "UNKNOWN"
        graph = DependencyGraph(gradle_bin)
        if not graph.build_for_project(ms_path):
            logger.warning("No se pudo construir grafo de dependencias", indent=2)
            return "UNKNOWN_ORIGIN"
        target_id = vuln.id if ":" in vuln.id else vuln.library
        lineage = " -> ".join(graph.get_lineage(target_id))
        logger.step("Análisis de Dependencias", "DONE", f"Lineage: {lineage}")
        return lineage

    # ------------------------------------------------------------------
    # Callback de Validación (invocado por CycleOfConsciousness)
    # ------------------------------------------------------------------

    def _validate_and_learn(self, action: str, attempt: int, cve_data: Dict):
        vuln = Vulnerability(cve_data)
        ms_path = self.fs.get_ms_path(self.current_ms)
        if not ms_path:
            logger.error(f"Ruta para {self.current_ms} no encontrada en validación.", indent=2)
            return False, f"Ruta para {self.current_ms} no encontrada en validación."

        logger.step("Preparando Remediación", "START", f"Intento {attempt}")
        ms_files = self.fs.get_ms_files(ms_path)
        backups = self.rollback.snapshot(ms_files)

        safe_ver = self._extract_version(action, vuln)
        suggested_var = action.split('=')[0].strip() if "=" in action else None

        logger.processing(f"Aplicando {vuln.library} -> {safe_ver}", indent=2)

        # Aplicar remediación y verificar si hubo cambios reales
        remediation_result = GradleMutator.apply_coordinated_remediation(
            ms_files, "TRANSITIVE", vuln.library, safe_ver,
            reason=f"Fix: {vuln.id}", override_var_name=suggested_var,
        )

        # Analizar resultado de la remediación
        if remediation_result == "ALREADY_FIXED":
            logger.info(f"{vuln.id} ya estaba corregido", indent=2)
            return True, {"changed": False, "already_fixed": True}
        elif remediation_result == False:
            logger.error(f"No se pudo aplicar la remediación para {vuln.id}", indent=2)
            return False, {"fatal": False, "message": "No se pudo aplicar la remediación"}

        # Solo si hubo cambios reales, validar el build
        has_changes = remediation_result == True

        if self.debug:
            logger.debug(f"Cambios aplicados: {has_changes}", indent=2)

        logger.step("Validación de Build", "START")
        gradle_bin = self.gradle.discover(ms_path, self.root_path)
        if not gradle_bin:
            logger.error("No se encontró binario de Gradle", indent=2)
            return False, {"fatal": True, "message": "INFRA_ERROR: No se encontró el binario 'gradle' o 'gradlew'."}

        if self.debug:
            logger.debug(f"Usando comando Gradle: {gradle_bin}", indent=2)

        success, logs = self.gradle.validate(ms_path, gradle_bin)
        if success:
            logger.step("Validación de Build", "DONE", "BUILD SUCCESSFUL")
            return True, {"changed": has_changes}

        logger.step("Validación de Build", "FAIL", "BUILD FAILED")
        logger.warning("Ejecutando rollback...", indent=2)
        self.rollback.restore(backups, self.current_ms)
        if isinstance(logs, str) and "INFRA_ERROR" in logs:
            return False, {"fatal": True, "message": logs}
        if self.debug:
            logger.debug(f"Fallo en Gradle. Logs: {logs[:100]}...", indent=2)
        return False, f"Fallo en validación de Gradle tras parche. Rollback ejecutado: {logs[:200]}"

    def _extract_version(self, action: str, vuln: Vulnerability) -> str:
        match = re.search(r"=\s*['\"](.*?)['\"]", action)
        if match:
            version = match.group(1).strip()
            if self.debug:
                logger.debug(f"Usando versión sugerida por el Cerebro: {version}", indent=2)
            return version
        return vuln.safe_version.split(',')[0].strip()

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------

    def _load_report(self) -> List[Dict]:
        if not os.path.exists(self.report_path):
            logger.error(f"Reporte {self.report_path} no encontrado.")
            return []
        logger.info(f"Cargando reporte: {self.report_path}")
        with open(self.report_path, 'r') as f:
            data = json.load(f)
        vulnerabilities = data if isinstance(data, list) else data.get("vulnerabilities", [])
        logger.success(f"Reporte cargado: {len(vulnerabilities)} vulnerabilidades encontradas")
        return vulnerabilities

    def _print_header(self):
        print("\n" + "=" * 70)
        print("🛡️  AGENTE DE REMEDIACIÓN GENERATIVA v.3.0 (ADAPTIVE)")
        print("=" * 70)
        logger.start("Iniciando ciclo de remediación")
        logger.info(f"Modo debug: {'Activado' if self.debug else 'Desactivado'}")
        logger.info(f"Modo dry-run: {'Activado' if self.dry_run else 'Desactivado'}")
        if self.target_folders:
            logger.info(f"Carpetas objetivo: {', '.join(self.target_folders)}")
        print("=" * 70 + "\n")

    def _print_summary(self):
        # Agrupar por estado
        fixed = [e for e in self.history if e["status"] == "FIXED"]
        already_fixed = [e for e in self.history if e["status"] == "ALREADY_FIXED"]
        errors = [e for e in self.history if e["status"] == "ERROR"]
        no_change = [e for e in self.history if e["status"] == "NO_CHANGE"]

        total = len(self.history)
        success_count = len(fixed) + len(already_fixed)
        failed_count = len(errors)
        skipped_count = len(no_change)

        logger.summary(total, success_count, failed_count, skipped_count)

        if fixed:
            logger.info("\nDetalle de reparados:", indent=0)
            for e in fixed:
                logger.success(f"[{e['ms']}] {e['id']}")

        if already_fixed:
            logger.info("\nDetalle de ya reparados:", indent=0)
            for e in already_fixed:
                logger.info(f"[{e['ms']}] {e['id']} - Ya estaba corregido")

        if errors:
            logger.error("\nDetalle de errores:", indent=0)
            for e in errors:
                logger.error(f"[{e['ms']}] {e['id']}: {e.get('explanation', 'Unknown error')[:50]}")


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
