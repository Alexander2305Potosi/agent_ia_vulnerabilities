"""
agent_ia/long_term_memory.py

Sistema de Memoria a Largo Plazo para el Agente de Remediación v.3.0
Almacena decisiones previas y patrones de éxito/fracaso por proyecto.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field


@dataclass
class RemediationDecision:
    """Registro de una decisión de remediación."""
    cve_id: str
    library: str
    microservice: str
    attempted_action: str
    success: bool
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    gradle_version: Optional[str] = None
    java_version: Optional[str] = None


@dataclass
class SuccessPattern:
    """Patrón de éxito aprendido."""
    library_family: str
    variable_naming_pattern: str
    version_strategy: str
    context: Dict[str, Any]
    occurrences: int = 1
    last_success: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class FailurePattern:
    """Patrón de fallo aprendido."""
    library_family: str
    attempted_version: str
    error_type: str
    error_signature: str
    resolution: Optional[str] = None
    occurrences: int = 1
    last_failure: str = field(default_factory=lambda: datetime.now().isoformat())


class LongTermMemory:
    """Memoria persistente del agente para aprendizaje a largo plazo."""

    MEMORY_FILE = os.path.join(os.path.dirname(__file__), ".agent_memory.json")
    MAX_HISTORY_PER_CVE = 5
    MAX_PATTERNS = 100

    def __init__(self, project_id: str = "default"):
        self.project_id = project_id
        self.memory = self._load_memory()
        self._ensure_structure()

    def _load_memory(self) -> Dict:
        """Carga la memoria desde disco."""
        if os.path.exists(self.MEMORY_FILE):
            try:
                with open(self.MEMORY_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_memory(self):
        """Guarda la memoria a disco."""
        os.makedirs(os.path.dirname(self.MEMORY_FILE), exist_ok=True)
        with open(self.MEMORY_FILE, 'w') as f:
            json.dump(self.memory, f, indent=2)

    def _ensure_structure(self):
        """Asegura la estructura base de la memoria."""
        if self.project_id not in self.memory:
            self.memory[self.project_id] = {
                'decisions': [],
                'success_patterns': [],
                'failure_patterns': [],
                'project_metadata': {}
            }

    def record_decision(self, decision: RemediationDecision):
        """Registra una nueva decisión de remediación."""
        proj = self.memory[self.project_id]
        proj['decisions'].append(asdict(decision))

        # Mantener solo las últimas N decisiones por CVE
        cve_decisions = [d for d in proj['decisions'] if d['cve_id'] == decision.cve_id]
        if len(cve_decisions) > self.MAX_HISTORY_PER_CVE:
            # Eliminar las más antiguas
            to_remove = cve_decisions[:-self.MAX_HISTORY_PER_CVE]
            proj['decisions'] = [d for d in proj['decisions'] if d not in to_remove]

        if decision.success:
            self._update_success_pattern(decision)
        else:
            self._update_failure_pattern(decision)

        self._save_memory()

    def _update_success_pattern(self, decision: RemediationDecision):
        """Actualiza patrones de éxito."""
        proj = self.memory[self.project_id]
        library_family = decision.library.split(':')[0] if ':' in decision.library else decision.library

        # Buscar patrón existente
        for pattern in proj['success_patterns']:
            if (pattern['library_family'] == library_family and
                pattern['variable_naming_pattern'] in decision.attempted_action):
                pattern['occurrences'] += 1
                pattern['last_success'] = datetime.now().isoformat()
                return

        # Crear nuevo patrón
        var_pattern = self._extract_variable_pattern(decision.attempted_action)
        new_pattern = SuccessPattern(
            library_family=library_family,
            variable_naming_pattern=var_pattern,
            version_strategy="explicit",
            context={'microservice': decision.microservice}
        )
        proj['success_patterns'].append(asdict(new_pattern))

        # Limitar tamaño
        if len(proj['success_patterns']) > self.MAX_PATTERNS:
            proj['success_patterns'].sort(key=lambda x: x['occurrences'], reverse=True)
            proj['success_patterns'] = proj['success_patterns'][:self.MAX_PATTERNS]

    def _update_failure_pattern(self, decision: RemediationDecision):
        """Actualiza patrones de fallo."""
        proj = self.memory[self.project_id]
        library_family = decision.library.split(':')[0] if ':' in decision.library else decision.library

        # Extraer versión intentada
        version = self._extract_version_from_action(decision.attempted_action)
        error_type = self._classify_error(decision.error_message)

        # Buscar patrón existente
        for pattern in proj['failure_patterns']:
            if (pattern['library_family'] == library_family and
                pattern['attempted_version'] == version and
                pattern['error_type'] == error_type):
                pattern['occurrences'] += 1
                pattern['last_failure'] = datetime.now().isoformat()
                return

        # Crear nuevo patrón
        new_pattern = FailurePattern(
            library_family=library_family,
            attempted_version=version,
            error_type=error_type,
            error_signature=self._extract_error_signature(decision.error_message)
        )
        proj['failure_patterns'].append(asdict(new_pattern))

        if len(proj['failure_patterns']) > self.MAX_PATTERNS:
            proj['failure_patterns'].sort(key=lambda x: x['occurrences'], reverse=True)
            proj['failure_patterns'] = proj['failure_patterns'][:self.MAX_PATTERNS]

    def get_suggested_variable_name(self, library: str) -> Optional[str]:
        """Sugiere nombre de variable basado en patrones de éxito."""
        proj = self.memory.get(self.project_id, {})
        library_family = library.split(':')[0] if ':' in library else library

        patterns = proj.get('success_patterns', [])
        matching = [p for p in patterns if p['library_family'] == library_family]

        if matching:
            # Devolver el más frecuente
            best = max(matching, key=lambda x: x['occurrences'])
            return best['variable_naming_pattern']
        return None

    def get_version_to_avoid(self, library: str) -> List[str]:
        """Retorna versiones que han causado fallos."""
        proj = self.memory.get(self.project_id, {})
        library_family = library.split(':')[0] if ':' in library else library

        failures = proj.get('failure_patterns', [])
        matching = [f['attempted_version'] for f in failures
                   if f['library_family'] == library_family]
        return matching

    def has_previous_failure(self, cve_id: str, action: str) -> Optional[Dict]:
        """Verifica si una acción similar falló anteriormente."""
        proj = self.memory.get(self.project_id, {})
        decisions = proj.get('decisions', [])

        for decision in decisions:
            if (decision['cve_id'] == cve_id and
                decision['attempted_action'] == action and
                not decision['success']):
                return decision
        return None

    def get_learning_summary(self) -> Dict:
        """Retorna resumen de aprendizaje del proyecto."""
        proj = self.memory.get(self.project_id, {})
        decisions = proj.get('decisions', [])

        total = len(decisions)
        successes = sum(1 for d in decisions if d['success'])
        failures = total - successes

        return {
            'total_decisions': total,
            'success_rate': (successes / total * 100) if total > 0 else 0,
            'success_patterns': len(proj.get('success_patterns', [])),
            'failure_patterns': len(proj.get('failure_patterns', [])),
            'common_failure_types': self._get_common_failures()
        }

    def _get_common_failures(self) -> List[Dict]:
        """Retorna los tipos de fallo más comunes."""
        proj = self.memory.get(self.project_id, {})
        failures = proj.get('failure_patterns', [])

        from collections import Counter
        error_types = [f['error_type'] for f in failures]
        return [{'type': t, 'count': c} for t, c in Counter(error_types).most_common(5)]

    def _extract_variable_pattern(self, action: str) -> str:
        """Extrae el patrón de nombre de variable de la acción."""
        if '=' in action:
            return action.split('=')[0].strip()
        return "unknown"

    def _extract_version_from_action(self, action: str) -> str:
        """Extrae la versión de la acción."""
        if '=' in action:
            return action.split('=')[1].strip().strip("'\"")
        return "unknown"

    def _classify_error(self, error_message: Optional[str]) -> str:
        """Clasifica el tipo de error."""
        if not error_message:
            return "UNKNOWN"

        error_lower = error_message.lower()

        if 'gradle' in error_lower or 'build' in error_lower:
            return "BUILD_FAILURE"
        elif 'version' in error_lower or 'conflict' in error_lower:
            return "VERSION_CONFLICT"
        elif 'infra' in error_lower:
            return "INFRA_ERROR"
        elif 'permission' in error_lower or 'access' in error_lower:
            return "PERMISSION_ERROR"
        return "UNKNOWN_ERROR"

    def _extract_error_signature(self, error_message: Optional[str]) -> str:
        """Extrae una firma única del error."""
        if not error_message:
            return ""
        # Tomar las primeras 50 caracteres como firma
        return error_message[:50].replace(' ', '_')

    def clear_project_memory(self):
        """Limpia la memoria del proyecto actual."""
        if self.project_id in self.memory:
            del self.memory[self.project_id]
            self._save_memory()
