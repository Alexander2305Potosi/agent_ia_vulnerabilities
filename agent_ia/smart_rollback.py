"""
agent_ia/smart_rollback.py

Rollback Inteligente v.3.0 — Generación de Reverse Patches
Permite rollback selectivo y mantiene historial de estados.
"""

import os
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
import json
import difflib


@dataclass
class FileChange:
    """Representa un cambio en un archivo."""
    file_path: str
    before_content: str
    after_content: str
    change_type: str  # 'create', 'modify', 'delete'
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def diff(self) -> str:
        """Genera diff del cambio."""
        before_lines = self.before_content.splitlines(keepends=True)
        after_lines = self.after_content.splitlines(keepends=True)
        if not before_lines:
            before_lines = ['\n']
        if not after_lines:
            after_lines = ['\n']
        return ''.join(difflib.unified_diff(
            before_lines, after_lines,
            fromfile=f"a/{self.file_path}",
            tofile=f"b/{self.file_path}",
            lineterm=''
        ))

    @property
    def reverse_diff(self) -> str:
        """Genera diff inverso para rollback."""
        before_lines = self.after_content.splitlines(keepends=True)
        after_lines = self.before_content.splitlines(keepends=True)
        if not before_lines:
            before_lines = ['\n']
        if not after_lines:
            after_lines = ['\n']
        return ''.join(difflib.unified_diff(
            before_lines, after_lines,
            fromfile=f"a/{self.file_path}",
            tofile=f"b/{self.file_path}",
            lineterm=''
        ))


@dataclass
class StateSnapshot:
    """Snapshot de estado completo."""
    snapshot_id: str
    timestamp: str
    cve_id: str
    microservice: str
    changes: List[FileChange] = field(default_factory=list)
    applied: bool = True

    @property
    def affected_files(self) -> List[str]:
        return [c.file_path for c in self.changes]


class SmartRollbackManager:
    """Gestor inteligente de rollback con reverse patches."""

    HISTORY_FILE = os.path.join(os.path.dirname(__file__), ".rollback_history.json")

    def __init__(self):
        self.snapshots: Dict[str, StateSnapshot] = {}
        self._load_history()

    def _load_history(self):
        """Carga el historial de snapshots."""
        if os.path.exists(self.HISTORY_FILE):
            try:
                with open(self.HISTORY_FILE, 'r') as f:
                    data = json.load(f)
                    for snap_id, snap_data in data.items():
                        changes = [FileChange(**c) for c in snap_data.pop('changes', [])]
                        self.snapshots[snap_id] = StateSnapshot(changes=changes, **snap_data)
            except:
                pass

    def _save_history(self):
        """Guarda el historial de snapshots."""
        data = {}
        for snap_id, snapshot in self.snapshots.items():
            snap_dict = asdict(snapshot)
            data[snap_id] = snap_dict

        os.makedirs(os.path.dirname(self.HISTORY_FILE), exist_ok=True)
        with open(self.HISTORY_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def create_snapshot(
        self,
        cve_id: str,
        microservice: str,
        files_before: Dict[str, str],
        files_after: Dict[str, str]
    ) -> StateSnapshot:
        """Crea un snapshot de estado."""
        changes = []

        all_files = set(files_before.keys()) | set(files_after.keys())

        for file_path in all_files:
            before = files_before.get(file_path, '')
            after = files_after.get(file_path, '')

            if before == after:
                continue

            if file_path not in files_before:
                change_type = 'create'
            elif file_path not in files_after:
                change_type = 'delete'
            else:
                change_type = 'modify'

            changes.append(FileChange(
                file_path=file_path,
                before_content=before,
                after_content=after,
                change_type=change_type
            ))

        snapshot_id = f"{microservice}_{cve_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        snapshot = StateSnapshot(
            snapshot_id=snapshot_id,
            timestamp=datetime.now().isoformat(),
            cve_id=cve_id,
            microservice=microservice,
            changes=changes
        )

        self.snapshots[snapshot_id] = snapshot
        self._save_history()

        return snapshot

    def generate_reverse_patch(self, snapshot_id: str) -> Optional[str]:
        """Genera un patch de reversión para un snapshot."""
        snapshot = self.snapshots.get(snapshot_id)
        if not snapshot:
            return None

        patches = []
        for change in snapshot.changes:
            patches.append(change.reverse_diff)
            patches.append('\n')

        return ''.join(patches)

    def apply_selective_rollback(
        self,
        snapshot_id: str,
        files_to_rollback: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """Aplica rollback selectivo de archivos específicos."""
        snapshot = self.snapshots.get(snapshot_id)
        if not snapshot:
            return False, f"Snapshot {snapshot_id} no encontrado"

        changes_to_rollback = snapshot.changes
        if files_to_rollback:
            changes_to_rollback = [
                c for c in changes_to_rollback
                if c.file_path in files_to_rollback
            ]

        success_count = 0
        errors = []

        for change in changes_to_rollback:
            try:
                # Verificar que el archivo actual coincide con el estado 'after'
                current_content = self._read_file(change.file_path)

                if current_content != change.after_content:
                    # El archivo ha cambiado desde el snapshot
                    errors.append(f"{change.file_path}: Archivo modificado desde el snapshot")
                    continue

                # Restaurar al estado 'before'
                if change.change_type == 'create':
                    # Eliminar archivo creado
                    if os.path.exists(change.file_path):
                        os.remove(change.file_path)
                else:
                    # Restaurar contenido
                    self._write_file(change.file_path, change.before_content)

                success_count += 1

            except Exception as e:
                errors.append(f"{change.file_path}: {str(e)}")

        # Actualizar estado del snapshot
        if success_count == len(changes_to_rollback):
            snapshot.applied = False
            self._save_history()

        if errors:
            return False, f"Rollback parcial: {success_count}/{len(changes_to_rollback)} archivos. Errores: {', '.join(errors)}"

        return True, f"Rollback exitoso de {success_count} archivos"

    def preview_rollback(self, snapshot_id: str) -> Optional[Dict]:
        """Muestra preview de lo que se revertiría."""
        snapshot = self.snapshots.get(snapshot_id)
        if not snapshot:
            return None

        preview = {
            'snapshot_id': snapshot_id,
            'timestamp': snapshot.timestamp,
            'cve_id': snapshot.cve_id,
            'microservice': snapshot.microservice,
            'files': []
        }

        for change in snapshot.changes:
            file_preview = {
                'path': change.file_path,
                'type': change.change_type,
                'lines_before': len(change.before_content.splitlines()),
                'lines_after': len(change.after_content.splitlines()),
                'preview': change.diff[:500] + '...' if len(change.diff) > 500 else change.diff
            }
            preview['files'].append(file_preview)

        return preview

    def get_snapshots_for_microservice(self, microservice: str) -> List[StateSnapshot]:
        """Retorna snapshots de un microservicio."""
        return [
            s for s in self.snapshots.values()
            if s.microservice == microservice
        ]

    def get_snapshots_for_cve(self, cve_id: str) -> List[StateSnapshot]:
        """Retorna snapshots de un CVE específico."""
        return [
            s for s in self.snapshots.values()
            if s.cve_id == cve_id
        ]

    def can_rollback(self, snapshot_id: str) -> Tuple[bool, str]:
        """Verifica si un snapshot puede ser revertido."""
        snapshot = self.snapshots.get(snapshot_id)
        if not snapshot:
            return False, "Snapshot no encontrado"

        if not snapshot.applied:
            return False, "Snapshot ya fue revertido"

        for change in snapshot.changes:
            current = self._read_file(change.file_path)
            if current != change.after_content:
                return False, f"{change.file_path} fue modificado desde el snapshot"

        return True, "Rollback posible"

    def _read_file(self, path: str) -> str:
        """Lee contenido de archivo."""
        if not os.path.exists(path):
            return ''
        with open(path, 'r') as f:
            return f.read()

    def _write_file(self, path: str, content: str):
        """Escribe contenido a archivo."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)

    def clear_history(self, older_than_days: Optional[int] = None):
        """Limpia historial de snapshots."""
        if older_than_days:
            from datetime import timedelta
            cutoff = datetime.now() - timedelta(days=older_than_days)
            to_remove = [
                sid for sid, s in self.snapshots.items()
                if datetime.fromisoformat(s.timestamp) < cutoff
            ]
            for sid in to_remove:
                del self.snapshots[sid]
        else:
            self.snapshots.clear()

        self._save_history()

    def get_rollback_statistics(self) -> Dict:
        """Retorna estadísticas de rollback."""
        total = len(self.snapshots)
        applied = sum(1 for s in self.snapshots.values() if s.applied)
        reverted = total - applied

        microservices = set(s.microservice for s in self.snapshots.values())
        cves = set(s.cve_id for s in self.snapshots.values())

        return {
            'total_snapshots': total,
            'applied_snapshots': applied,
            'reverted_snapshots': reverted,
            'unique_microservices': len(microservices),
            'unique_cves': len(cves),
            'microservices': list(microservices)
        }
