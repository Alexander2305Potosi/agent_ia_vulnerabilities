#!/usr/bin/env python3
"""
Sistema de Logging Mejorado para el Agente de Remediación v3.1

Proporciona logs estructurados y fáciles de entender con:
- Identificación clara del microservicio
- Estados visuales (éxito, fallo, advertencia)
- Tiempos de ejecución
- Contexto de CVE
"""

import time
from datetime import datetime
from enum import Enum
from typing import Optional


class LogLevel(Enum):
    """Niveles de log con emojis para mejor visualización."""
    DEBUG = "🔍 DEBUG"
    INFO = "ℹ️ INFO"
    SUCCESS = "✅ ÉXITO"
    WARNING = "⚠️ ADVERTENCIA"
    ERROR = "❌ ERROR"
    CRITICAL = "🚨 CRÍTICO"
    PROCESSING = "⚙️ PROCESANDO"
    START = "🚀 INICIO"
    COMPLETE = "🏁 COMPLETADO"


class ColorPalette:
    """Colores ANSI para terminal."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Colores
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Backgrounds
    BG_GREEN = "\033[42m"
    BG_RED = "\033[41m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"


class RemediationLogger:
    """
    Logger estructurado para el Agente de Remediación.

    Formato: [TIMESTAMP] [NIVEL] [MS: {ms}] [CVE: {cve}] Mensaje
    """

    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors
        self.current_ms: Optional[str] = None
        self.current_cve: Optional[str] = None
        self.start_times: dict = {}

    def set_context(self, ms: Optional[str] = None, cve: Optional[str] = None):
        """Establece el contexto actual de microservicio y CVE."""
        if ms:
            self.current_ms = ms
        if cve:
            self.current_cve = cve

    def clear_context(self):
        """Limpia el contexto actual."""
        self.current_ms = None
        self.current_cve = None

    def _format_timestamp(self) -> str:
        """Genera timestamp formateado."""
        return datetime.now().strftime("%H:%M:%S")

    def _colorize(self, text: str, color: str) -> str:
        """Aplica color al texto si está habilitado."""
        if not self.use_colors:
            return text
        return f"{color}{text}{ColorPalette.RESET}"

    def _build_context_string(self) -> str:
        """Construye la cadena de contexto [MS] [CVE]."""
        parts = []
        if self.current_ms:
            parts.append(f"MS:{self.current_ms}")
        if self.current_cve:
            parts.append(f"CVE:{self.current_cve}")
        return " ".join(parts)

    def _log(self, level: LogLevel, message: str, indent: int = 0):
        """Método base de logging."""
        timestamp = self._format_timestamp()
        context = self._build_context_string()

        indent_str = "  " * indent

        # Formato: [TIME] [LEVEL] [CONTEXT] Message
        parts = [f"[{timestamp}]"]

        # Nivel con color
        level_str = level.value
        if self.use_colors:
            if level in (LogLevel.SUCCESS, LogLevel.COMPLETE):
                level_str = self._colorize(level_str, ColorPalette.GREEN)
            elif level in (LogLevel.ERROR, LogLevel.CRITICAL):
                level_str = self._colorize(level_str, ColorPalette.RED)
            elif level in (LogLevel.WARNING,):
                level_str = self._colorize(level_str, ColorPalette.YELLOW)
            elif level == LogLevel.PROCESSING:
                level_str = self._colorize(level_str, ColorPalette.CYAN)
            elif level == LogLevel.START:
                level_str = self._colorize(level_str, ColorPalette.BLUE)
        parts.append(f"[{level_str}]")

        # Contexto
        if context:
            context_str = self._colorize(context, ColorPalette.DIM) if self.use_colors else context
            parts.append(f"[{context_str}]")

        # Mensaje
        parts.append(f"{indent_str}{message}")

        print(" ".join(parts))

    # Métodos específicos para cada nivel
    def debug(self, message: str, indent: int = 0):
        self._log(LogLevel.DEBUG, message, indent)

    def info(self, message: str, indent: int = 0):
        self._log(LogLevel.INFO, message, indent)

    def success(self, message: str, indent: int = 0):
        self._log(LogLevel.SUCCESS, message, indent)

    def warning(self, message: str, indent: int = 0):
        self._log(LogLevel.WARNING, message, indent)

    def error(self, message: str, indent: int = 0):
        self._log(LogLevel.ERROR, message, indent)

    def critical(self, message: str, indent: int = 0):
        self._log(LogLevel.CRITICAL, message, indent)

    def processing(self, message: str, indent: int = 0):
        self._log(LogLevel.PROCESSING, message, indent)

    def start(self, message: str, indent: int = 0):
        self._log(LogLevel.START, message, indent)

    def complete(self, message: str, indent: int = 0):
        self._log(LogLevel.COMPLETE, message, indent)

    # Métodos de utilidad específicos para el agente
    def start_ms(self, ms_name: str):
        """Log de inicio de procesamiento de microservicio."""
        self.set_context(ms=ms_name)
        self.start(f"Iniciando remediación de microservicio: {ms_name}")
        self.start_times[ms_name] = time.time()

    def complete_ms(self, ms_name: str, status: str = "SUCCESS"):
        """Log de finalización de microservicio."""
        elapsed = time.time() - self.start_times.get(ms_name, time.time())
        status_icon = "✅" if status == "SUCCESS" else "❌"
        self.complete(f"Microservicio {ms_name} completado en {elapsed:.1f}s [{status}]")
        self.clear_context()

    def start_cve(self, cve_id: str, library: str, severity: str):
        """Log de inicio de procesamiento de CVE."""
        self.set_context(cve=cve_id)
        severity_color = {"CRITICAL": "🚨", "HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(severity, "⚪")
        self.processing(f"Procesando {cve_id} [{library}] Severidad: {severity_color} {severity}", indent=1)

    def success_cve(self, cve_id: str, action: str = "remediado"):
        """Log de éxito de CVE."""
        self.success(f"{cve_id} {action} exitosamente", indent=2)

    def fail_cve(self, cve_id: str, error: str):
        """Log de fallo de CVE."""
        self.error(f"{cve_id} falló: {error}", indent=2)

    def step(self, step_name: str, status: str = "START", details: str = ""):
        """Log de paso del proceso con estado."""
        status_icons = {
            "START": "⏳",
            "DONE": "✓",
            "FAIL": "✗",
            "SKIP": "⊘"
        }
        icon = status_icons.get(status, "•")
        msg = f"{icon} {step_name}"
        if details:
            msg += f": {details}"

        if status == "START":
            self.info(msg, indent=2)
        elif status == "DONE":
            self.success(msg, indent=2)
        elif status == "FAIL":
            self.error(msg, indent=2)
        elif status == "SKIP":
            self.warning(msg, indent=2)

    def summary(self, total: int, success: int, failed: int, skipped: int = 0):
        """Log de resumen final."""
        print("\n" + "=" * 70)
        print(self._colorize("📊 RESUMEN DE EJECUCIÓN", ColorPalette.BOLD) if self.use_colors else "📊 RESUMEN DE EJECUCIÓN")
        print("=" * 70)
        print(f"  Total procesados: {total}")
        print(f"  {self._colorize(f'Exitosos: {success}', ColorPalette.GREEN) if self.use_colors else f'Exitosos: {success}'}")
        print(f"  {self._colorize(f'Fallidos: {failed}', ColorPalette.RED) if self.use_colors else f'Fallidos: {failed}'}")
        if skipped > 0:
            print(f"  Omitidos: {skipped}")
        print("=" * 70)


# Instancia global del logger
logger = RemediationLogger(use_colors=True)


def set_log_context(ms: Optional[str] = None, cve: Optional[str] = None):
    """Función de utilidad para establecer contexto global."""
    logger.set_context(ms, cve)


def clear_log_context():
    """Función de utilidad para limpiar contexto global."""
    logger.clear_context()
