#!/usr/bin/env python3
"""
Shutdown Manager - Manejo Graceful de Interrupciones y Cierre

Proporciona mecanismos para:
- Capturar señales de interrupción (SIGINT, SIGTERM)
- Limpiar recursos antes de cerrar
- Terminar procesos hijos pendientes
- Cerrar conexiones y archivos abiertos
"""

import atexit
import os
import signal
import sys
import threading
import time
from typing import List, Callable, Optional

from agent_ia.core.logging_utils import logger


class ShutdownManager:
    """
    Gestiona el cierre graceful de la aplicación.

    Uso:
        shutdown_manager = ShutdownManager()
        shutdown_manager.register_cleanup_function(cleanup_function)
        shutdown_manager.setup_signal_handlers()
    """

    _instance: Optional['ShutdownManager'] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._cleanup_functions: List[Callable] = []
        self._is_shutting_down = False
        self._shutdown_timeout = 5  # segundos
        self._active_processes: List = []
        self._original_sigint = None
        self._original_sigterm = None

    def setup_signal_handlers(self):
        """Configura los manejadores de señales para SIGINT y SIGTERM."""
        # Guardar handlers originales
        self._original_sigint = signal.signal(signal.SIGINT, self._signal_handler)
        self._original_sigterm = signal.signal(signal.SIGTERM, self._signal_handler)

        # Configurar atexit para limpieza adicional
        atexit.register(self._atexit_cleanup)

        logger.debug("Manejadores de señales configurados")

    def _signal_handler(self, signum, frame):
        """Manejador de señales que inicia el cierre graceful."""
        signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        logger.info(f"\n[{signal_name}] Señal de interrupción recibida. Iniciando cierre graceful...")

        self.shutdown()

    def _atexit_cleanup(self):
        """Limpieza adicional al salir del programa."""
        if not self._is_shutting_down:
            logger.debug("Ejecutando limpieza de atexit")
            self.shutdown()

    def shutdown(self, exit_code: int = 0):
        """
        Inicia el proceso de cierre graceful.

        Args:
            exit_code: Código de salida del programa
        """
        if self._is_shutting_down:
            logger.warning("Cierre ya en progreso...")
            return

        self._is_shutting_down = True

        try:
            logger.info("=" * 60)
            logger.info("INICIANDO CIERRE GRACEFUL...")
            logger.info("=" * 60)

            # 1. Cancelar procesos activos
            self._terminate_active_processes()

            # 2. Ejecutar funciones de limpieza registradas
            self._run_cleanup_functions()

            # 3. Esperar un momento para que los logs se escriban
            time.sleep(0.5)

            logger.info("✅ Cierre completado. Hasta luego!")

        except Exception as e:
            logger.error(f"Error durante el cierre: {e}")
        finally:
            # Forzar salida limpia
            self._force_exit(exit_code)

    def _terminate_active_processes(self):
        """Termina procesos hijos activos."""
        if not self._active_processes:
            return

        logger.info(f"Terminando {len(self._active_processes)} proceso(s) activo(s)...")

        for process in self._active_processes:
            try:
                if hasattr(process, 'terminate'):
                    process.terminate()
                    logger.debug(f"Proceso {process} terminado")
                elif hasattr(process, 'kill'):
                    process.kill()
                    logger.debug(f"Proceso {process} terminado (kill)")
            except Exception as e:
                logger.warning(f"No se pudo terminar proceso {process}: {e}")

        self._active_processes.clear()

    def _run_cleanup_functions(self):
        """Ejecuta todas las funciones de limpieza registradas."""
        if not self._cleanup_functions:
            return

        logger.info(f"Ejecutando {len(self._cleanup_functions)} función(es) de limpieza...")

        for func in self._cleanup_functions:
            try:
                func()
            except Exception as e:
                logger.error(f"Error en función de limpieza {func.__name__}: {e}")

    def _force_exit(self, exit_code: int = 0):
        """Fuerza la salida del programa de forma limpia."""
        # Restaurar handlers originales para evitar recursión
        if self._original_sigint:
            signal.signal(signal.SIGINT, signal.SIG_DFL)
        if self._original_sigterm:
            signal.signal(signal.SIGTERM, signal.SIG_DFL)

        # Forzar flush de buffers de salida
        sys.stdout.flush()
        sys.stderr.flush()

        # Salir sin llamar a más handlers de atexit
        os._exit(exit_code)

    def register_cleanup_function(self, func: Callable):
        """
        Registra una función para ejecutar durante el cierre.

        Args:
            func: Función sin argumentos a ejecutar al cerrar
        """
        self._cleanup_functions.append(func)
        logger.debug(f"Función de limpieza registrada: {func.__name__}")

    def register_process(self, process):
        """
        Registra un proceso para terminarlo al cerrar.

        Args:
            process: Objeto proceso con método terminate() o kill()
        """
        self._active_processes.append(process)

    def unregister_process(self, process):
        """Desregistra un proceso."""
        if process in self._active_processes:
            self._active_processes.remove(process)

    def is_shutting_down(self) -> bool:
        """Retorna True si el cierre está en progreso."""
        return self._is_shutting_down


# Instancia global
shutdown_manager = ShutdownManager()


def setup_graceful_shutdown():
    """Configura el manejo graceful de señales."""
    shutdown_manager.setup_signal_handlers()


def register_cleanup(func: Callable):
    """Decorador para registrar una función de limpieza."""
    shutdown_manager.register_cleanup_function(func)
    return func


class ProcessContext:
    """
    Context manager para procesos que se registran automáticamente.

    Uso:
        with ProcessContext(mi_proceso) as proc:
            proc.do_work()
    """

    def __init__(self, process):
        self.process = process

    def __enter__(self):
        shutdown_manager.register_process(self.process)
        return self.process

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutdown_manager.unregister_process(self.process)
        return False
