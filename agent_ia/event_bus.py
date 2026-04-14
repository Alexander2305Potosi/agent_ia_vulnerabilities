"""
agent_ia/event_bus.py

Arquitectura Event-Driven (Pub/Sub) para el Agente de Remediación v.3.0
Permite procesamiento paralelo y desacoplado de microservicios.
"""

import asyncio
from typing import Dict, List, Callable, Any, Optional, Coroutine
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


class EventType(Enum):
    """Tipos de eventos del sistema."""
    VULNERABILITY_DISCOVERED = auto()
    MICROSERVICE_SCANNED = auto()
    REMEDIATION_ATTEMPTED = auto()
    REMEDIATION_SUCCEEDED = auto()
    REMEDIATION_FAILED = auto()
    ROLLBACK_TRIGGERED = auto()
    BUILD_VALIDATION_STARTED = auto()
    BUILD_VALIDATION_COMPLETED = auto()
    CYCLE_COMPLETED = auto()


@dataclass
class Event:
    """Evento del bus."""
    event_type: EventType
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(datetime.now().timestamp()))


@dataclass
class EventResult:
    """Resultado de procesamiento de evento."""
    event_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None


class EventBus:
    """Bus de eventos Pub/Sub para orquestación desacoplada."""

    def __init__(self, max_workers: int = 4):
        self.subscribers: Dict[EventType, List[Callable]] = {et: [] for et in EventType}
        self.async_subscribers: Dict[EventType, List[Callable]] = {et: [] for et in EventType}
        self.history: List[Event] = []
        self.max_history = 1000
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.Lock()

    def subscribe(self, event_type: EventType, handler: Callable):
        """Suscribe un handler síncrono a un tipo de evento."""
        with self._lock:
            self.subscribers[event_type].append(handler)

    def subscribe_async(self, event_type: EventType, handler: Callable):
        """Suscribe un handler asíncrono a un tipo de evento."""
        with self._lock:
            self.async_subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: EventType, handler: Callable):
        """Desuscribe un handler."""
        with self._lock:
            if handler in self.subscribers[event_type]:
                self.subscribers[event_type].remove(handler)
            if handler in self.async_subscribers[event_type]:
                self.async_subscribers[event_type].remove(handler)

    def publish(self, event: Event) -> List[EventResult]:
        """Publica un evento y notifica a todos los suscriptores."""
        self._add_to_history(event)

        results = []

        # Procesar handlers síncronos
        with self._lock:
            handlers = self.subscribers[event.event_type][:]

        for handler in handlers:
            try:
                result = handler(event.payload)
                results.append(EventResult(event.event_id, True, result))
            except Exception as e:
                results.append(EventResult(event.event_id, False, error=str(e)))

        return results

    async def publish_async(self, event: Event) -> List[EventResult]:
        """Publica un evento de forma asíncrona."""
        self._add_to_history(event)

        tasks = []

        # Handlers asíncronos
        with self._lock:
            async_handlers = self.async_subscribers[event.event_type][:]

        for handler in async_handlers:
            tasks.append(self._run_async_handler(handler, event))

        # Handlers síncronos en thread pool
        with self._lock:
            sync_handlers = self.subscribers[event.event_type][:]

        for handler in sync_handlers:
            tasks.append(self._run_sync_in_executor(handler, event))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Procesar resultados
        processed = []
        for r in results:
            if isinstance(r, Exception):
                processed.append(EventResult(event.event_id, False, error=str(r)))
            else:
                processed.append(r)

        return processed

    async def _run_async_handler(self, handler: Callable, event: Event) -> EventResult:
        """Ejecuta un handler asíncrono."""
        try:
            if asyncio.iscoroutinefunction(handler):
                result = await handler(event.payload)
            else:
                result = handler(event.payload)
            return EventResult(event.event_id, True, result)
        except Exception as e:
            return EventResult(event.event_id, False, error=str(e))

    async def _run_sync_in_executor(self, handler: Callable, event: Event) -> EventResult:
        """Ejecuta un handler síncrono en el thread pool."""
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(self.executor, handler, event.payload)
            return EventResult(event.event_id, True, result)
        except Exception as e:
            return EventResult(event.event_id, False, error=str(e))

    def _add_to_history(self, event: Event):
        """Agrega evento al historial."""
        with self._lock:
            self.history.append(event)
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history:]

    def get_history(self, event_type: Optional[EventType] = None) -> List[Event]:
        """Retorna historial de eventos."""
        with self._lock:
            if event_type:
                return [e for e in self.history if e.event_type == event_type]
            return self.history[:]

    def clear_history(self):
        """Limpia el historial."""
        with self._lock:
            self.history.clear()

    def shutdown(self):
        """Cierra el executor."""
        self.executor.shutdown(wait=True)


class ParallelRemediationOrchestrator:
    """Orquestador de remediaciones paralelas usando el bus de eventos."""

    def __init__(self, event_bus: EventBus, max_concurrent: int = 3):
        self.event_bus = event_bus
        self.max_concurrent = max_concurrent
        self.results: Dict[str, Any] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def process_vulnerabilities_batch(
        self,
        vulnerabilities: List[Dict],
        process_fn: Callable,
        context: Dict
    ) -> Dict[str, Any]:
        """Procesa un batch de vulnerabilidades en paralelo."""
        tasks = []

        for vuln in vulnerabilities:
            task = self._process_single_vulnerability(vuln, process_fn, context)
            tasks.append(task)

        await asyncio.gather(*tasks)
        return self.results

    async def _process_single_vulnerability(
        self,
        vulnerability: Dict,
        process_fn: Callable,
        context: Dict
    ):
        """Procesa una vulnerabilidad individual con límite de concurrencia."""
        async with self._semaphore:
            vuln_id = vulnerability.get('cve') or vulnerability.get('id', 'unknown')

            # Publicar evento de descubrimiento
            await self.event_bus.publish_async(Event(
                EventType.VULNERABILITY_DISCOVERED,
                {'vulnerability': vulnerability, 'context': context}
            ))

            try:
                result = await process_fn(vulnerability, context)
                self.results[vuln_id] = result

                # Publicar evento de éxito o fallo
                event_type = (EventType.REMEDIATION_SUCCEEDED if result.get('success')
                             else EventType.REMEDIATION_FAILED)
                await self.event_bus.publish_async(Event(
                    event_type,
                    {'vulnerability': vulnerability, 'result': result}
                ))

            except Exception as e:
                self.results[vuln_id] = {'success': False, 'error': str(e)}
                await self.event_bus.publish_async(Event(
                    EventType.REMEDIATION_FAILED,
                    {'vulnerability': vulnerability, 'error': str(e)}
                ))


class EventDrivenRemediationAgent:
    """Agente de remediación basado en eventos."""

    def __init__(self, max_workers: int = 4):
        self.event_bus = EventBus(max_workers=max_workers)
        self.orchestrator = ParallelRemediationOrchestrator(self.event_bus, max_concurrent=max_workers)
        self._setup_default_handlers()

    def _setup_default_handlers(self):
        """Configura handlers por defecto."""
        # Handler para logging
        self.event_bus.subscribe(EventType.REMEDIATION_SUCCEEDED, self._log_success)
        self.event_bus.subscribe(EventType.REMEDIATION_FAILED, self._log_failure)

    def _log_success(self, payload: Dict):
        """Log de éxito."""
        vuln = payload.get('vulnerability', {})
        print(f"    [EVENT] Remediación exitosa: {vuln.get('cve', 'N/A')}")

    def _log_failure(self, payload: Dict):
        """Log de fallo."""
        vuln = payload.get('vulnerability', {})
        error = payload.get('error', 'Unknown')
        print(f"    [EVENT] Remediación fallida: {vuln.get('cve', 'N/A')} - {error}")

    def on_vulnerability_discovered(self, handler: Callable):
        """Decorador para suscribirse a descubrimiento de vulnerabilidades."""
        self.event_bus.subscribe(EventType.VULNERABILITY_DISCOVERED, handler)
        return handler

    def on_remediation_completed(self, handler: Callable):
        """Decorador para suscribirse a remediaciones completadas."""
        self.event_bus.subscribe(EventType.REMEDIATION_SUCCEEDED, handler)
        self.event_bus.subscribe(EventType.REMEDIATION_FAILED, handler)
        return handler

    async def run_remediation_batch(self, vulnerabilities: List[Dict], process_fn, context: Dict):
        """Ejecuta un batch de remediaciones."""
        return await self.orchestrator.process_vulnerabilities_batch(
            vulnerabilities, process_fn, context
        )

    def shutdown(self):
        """Apaga el agente."""
        self.event_bus.shutdown()
