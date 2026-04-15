#!/usr/bin/env python3
"""
Procesador Paralelo de Microservicios para el Agente de Remediación v.3.1

Ejecuta múltiples microservicios en paralelo para cada CVE,
manteniendo la secuencia CVE por CVE.

Ejemplo:
- CVE-1: MS-1, MS-2, MS-3, MS-4, MS-5, MS-6 (todos en paralelo)
- CVE-2: MS-1, MS-2, MS-3, MS-4, MS-5, MS-6 (todos en paralelo)
"""

import concurrent.futures
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from agent_ia.core.logging_utils import logger


@dataclass
class ParallelProcessingConfig:
    """Configuración para procesamiento paralelo."""
    max_workers: int = 4  # Número máximo de MS en paralelo
    timeout_per_ms: int = 300  # 5 minutos por MS
    fail_fast: bool = False  # Si True, detener al primer error
    preserve_order: bool = False  # Si True, mantener orden de resultados


@dataclass
class MicroserviceResult:
    """Resultado del procesamiento de un microservicio."""
    ms_name: str
    cve_id: str
    success: bool
    status: str  # FIXED, ALREADY_FIXED, ERROR, NO_CHANGE
    explanation: str
    changed: bool
    already_fixed: bool
    error_message: Optional[str] = None
    duration_seconds: float = 0.0
    metadata: Dict = field(default_factory=dict)


class ParallelMicroserviceProcessor:
    """
    Procesa múltiples microservicios en paralelo para un CVE dado.

    Thread-safe: cada hilo procesa un MS independiente sin conflictos.
    """

    def __init__(self, config: ParallelProcessingConfig = None):
        self.config = config or ParallelProcessingConfig()
        self._lock = threading.Lock()
        self._active_tasks: Dict[str, threading.Thread] = {}

    def process_cve_parallel(
        self,
        cve_id: str,
        library: str,
        severity: str,
        microservices: List[str],
        process_func: Callable[[str], Tuple[bool, str, Dict]]
    ) -> List[MicroserviceResult]:
        """
        Procesa un CVE en múltiples microservicios en paralelo.

        Args:
            cve_id: ID del CVE a procesar
            library: Librería afectada
            severity: Severidad del CVE
            microservices: Lista de nombres de microservicios
            process_func: Función que procesa un MS y retorna (success, explanation, metadata)

        Returns:
            Lista de resultados por microservicio
        """
        if not microservices:
            logger.warning(f"[{cve_id}] No hay microservicios para procesar")
            return []

        total_ms = len(microservices)
        workers = min(self.config.max_workers, total_ms)

        logger.start(f"CVE: {cve_id} | Procesando {total_ms} microservicio(s) en paralelo ({workers} workers)")
        logger.info(f"Librería: {library} | Severidad: {severity}")

        start_time = time.time()
        results: List[MicroserviceResult] = []
        completed = 0
        errors = 0

        # Usar ThreadPoolExecutor para paralelismo
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix=f"CVE-{cve_id}") as executor:
            # Enviar todas las tareas
            future_to_ms = {
                executor.submit(self._process_single_ms, ms, cve_id, process_func): ms
                for ms in microservices
            }

            # Procesar resultados a medida que completan
            for future in as_completed(future_to_ms):
                ms_name = future_to_ms[future]
                try:
                    result = future.result(timeout=self.config.timeout_per_ms)
                    results.append(result)
                    completed += 1

                    # Log de progreso
                    self._log_progress(cve_id, completed, total_ms, result)

                    # Si fail_fast y hay error, cancelar resto
                    if self.config.fail_fast and not result.success:
                        logger.error(f"[{cve_id}] Fallo en {ms_name}. Cancelando resto (fail_fast=True)")
                        for f in future_to_ms:
                            if not f.done():
                                f.cancel()
                        break

                except concurrent.futures.TimeoutError:
                    logger.error(f"[{cve_id}] Timeout procesando {ms_name}")
                    results.append(MicroserviceResult(
                        ms_name=ms_name,
                        cve_id=cve_id,
                        success=False,
                        status="ERROR",
                        explanation=f"Timeout después de {self.config.timeout_per_ms}s",
                        changed=False,
                        already_fixed=False,
                        error_message="TIMEOUT"
                    ))
                    errors += 1

                except Exception as e:
                    logger.error(f"[{cve_id}] Error procesando {ms_name}: {e}")
                    results.append(MicroserviceResult(
                        ms_name=ms_name,
                        cve_id=cve_id,
                        success=False,
                        status="ERROR",
                        explanation=str(e),
                        changed=False,
                        already_fixed=False,
                        error_message=str(e)
                    ))
                    errors += 1

        elapsed = time.time() - start_time

        # Resumen del CVE
        self._log_cve_summary(cve_id, results, elapsed)

        return results

    def _process_single_ms(
        self,
        ms_name: str,
        cve_id: str,
        process_func: Callable[[str], Tuple[bool, str, Dict]]
    ) -> MicroserviceResult:
        """
        Procesa un único microservicio (ejecutado en thread separado).
        """
        ms_start = time.time()

        try:
            # Ejecutar la función de procesamiento
            success, explanation, metadata = process_func(ms_name)

            # Determinar estado
            actually_changed = metadata.get("changed", False)
            already_fixed = metadata.get("already_fixed", False)

            if not success:
                status = "ERROR"
            elif already_fixed:
                status = "ALREADY_FIXED"
            elif actually_changed:
                status = "FIXED"
            else:
                status = "NO_CHANGE"

            return MicroserviceResult(
                ms_name=ms_name,
                cve_id=cve_id,
                success=success,
                status=status,
                explanation=explanation,
                changed=actually_changed,
                already_fixed=already_fixed,
                error_message=explanation if not success else None,
                duration_seconds=time.time() - ms_start,
                metadata=metadata
            )

        except Exception as e:
            return MicroserviceResult(
                ms_name=ms_name,
                cve_id=cve_id,
                success=False,
                status="ERROR",
                explanation=f"Excepción: {str(e)}",
                changed=False,
                already_fixed=False,
                error_message=str(e),
                duration_seconds=time.time() - ms_start
            )

    def _log_progress(self, cve_id: str, completed: int, total: int, result: MicroserviceResult):
        """Log de progreso de procesamiento."""
        percentage = (completed / total) * 100

        status_icon = {
            "FIXED": "✅",
            "ALREADY_FIXED": "✓",
            "ERROR": "❌",
            "NO_CHANGE": "⚠️"
        }.get(result.status, "•")

        logger.info(
            f"[{cve_id}] Progreso: {completed}/{total} ({percentage:.0f}%) | "
            f"{status_icon} {result.ms_name}: {result.status} ({result.duration_seconds:.1f}s)"
        )

    def _log_cve_summary(self, cve_id: str, results: List[MicroserviceResult], elapsed: float):
        """Log de resumen del CVE."""
        fixed = sum(1 for r in results if r.status == "FIXED")
        already = sum(1 for r in results if r.status == "ALREADY_FIXED")
        errors = sum(1 for r in results if r.status == "ERROR")
        no_change = sum(1 for r in results if r.status == "NO_CHANGE")

        logger.complete(f"CVE: {cve_id} completado en {elapsed:.1f}s")
        logger.info(f"  ✅ Reparados: {fixed} | ✓ Ya reparados: {already} | ❌ Errores: {errors} | ⚠️ Sin cambios: {no_change}")


class SequentialCVEProcessor:
    """
    Procesa CVEs secuencialmente, pero cada CVE procesa sus MS en paralelo.

    Patrón: CVE-1 (MS en paralelo) → CVE-2 (MS en paralelo) → CVE-3 (MS en paralelo)
    """

    def __init__(self, parallel_config: ParallelProcessingConfig = None):
        self.parallel_processor = ParallelMicroserviceProcessor(parallel_config)
        self._results_by_cve: Dict[str, List[MicroserviceResult]] = {}

    def process_all_cves(
        self,
        vulnerabilities: List[Dict],
        get_microservices_func: Callable[[], List[str]],
        process_ms_func: Callable[[str, Dict], Tuple[bool, str, Dict]],
        skip_check_func: Optional[Callable[[str, str], bool]] = None
    ) -> Dict[str, List[MicroserviceResult]]:
        """
        Procesa todos los CVEs secuencialmente, pero cada CVE procesa MS en paralelo.

        Args:
            vulnerabilities: Lista de diccionarios de vulnerabilidades
            get_microservices_func: Función que retorna lista de MS
            process_ms_func: Función (ms_name, cve_data) -> (success, explanation, metadata)
            skip_check_func: Función opcional (ms, cve_id) -> bool para saltar MS

        Returns:
            Dict: {cve_id: [MicroserviceResult, ...]}
        """
        total_cves = len(vulnerabilities)
        logger.start(f"INICIANDO PROCESAMIENTO DE {total_cves} CVE(s)")
        logger.info(f"Configuración: {self.parallel_processor.config.max_workers} workers por CVE")

        global_start = time.time()

        for idx, cve_data in enumerate(vulnerabilities, 1):
            cve_id = cve_data.get("cve", cve_data.get("id", "UNKNOWN"))
            library = cve_data.get("library", "unknown")
            severity = cve_data.get("severity", "unknown")

            logger.info(f"\n{'='*60}")
            logger.start(f"[{idx}/{total_cves}] Procesando CVE: {cve_id}")
            logger.info(f"{'='*60}")

            # Obtener microservicios
            microservices = get_microservices_func()

            # Filtrar si hay función de skip
            if skip_check_func:
                microservices = [
                    ms for ms in microservices
                    if not skip_check_func(ms, cve_id)
                ]

            if not microservices:
                logger.warning(f"[{cve_id}] No hay microservicios para procesar (todos excluidos o deshabilitados)")
                continue

            # Crear wrapper de process_func que incluye cve_data
            def process_func(ms_name: str) -> Tuple[bool, str, Dict]:
                return process_ms_func(ms_name, cve_data)

            # Procesar en paralelo
            results = self.parallel_processor.process_cve_parallel(
                cve_id=cve_id,
                library=library,
                severity=severity,
                microservices=microservices,
                process_func=process_func
            )

            self._results_by_cve[cve_id] = results

        total_elapsed = time.time() - global_start

        # Resumen global
        self._log_global_summary(total_elapsed)

        return self._results_by_cve

    def _log_global_summary(self, elapsed: float):
        """Log de resumen global de todos los CVEs."""
        logger.complete(f"PROCESAMIENTO COMPLETADO EN {elapsed:.1f}s")
        logger.info("="*60)

        total_fixed = 0
        total_already = 0
        total_errors = 0

        for cve_id, results in self._results_by_cve.items():
            fixed = sum(1 for r in results if r.status == "FIXED")
            already = sum(1 for r in results if r.status == "ALREADY_FIXED")
            errors = sum(1 for r in results if r.status == "ERROR")
            total_fixed += fixed
            total_already += already
            total_errors += errors

        total_ms_processed = sum(len(r) for r in self._results_by_cve.values())

        logger.info(f"Total CVEs procesados: {len(self._results_by_cve)}")
        logger.info(f"Total Microservicios: {total_ms_processed}")
        logger.info(f"✅ Reparados: {total_fixed} | ✓ Ya reparados: {total_already} | ❌ Errores: {total_errors}")
        logger.info(f"Tiempo promedio por CVE: {elapsed/len(self._results_by_cve):.1f}s" if self._results_by_cve else "N/A")
        logger.info("="*60)


# Instancia global para uso en el agente
parallel_processor = ParallelMicroserviceProcessor()
sequential_processor = SequentialCVEProcessor()
