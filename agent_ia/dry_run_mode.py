"""
agent_ia/dry_run_mode.py

Modo Dry-Run Mejorado para el Agente de Remediación v.3.0
Preview de cambios en formato diff coloreado y estimación de impacto.
"""

import difflib
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FileChangePreview:
    """Preview de cambios en un archivo."""
    file_path: str
    before_content: str
    after_content: str
    lines_added: int = 0
    lines_removed: int = 0
    lines_modified: int = 0
    impact_score: float = 0.0  # 0-100


@dataclass
class ImpactEstimate:
    """Estimación de impacto de una remediación."""
    affected_files: int
    total_lines_changed: int
    potential_breaking_changes: int
    estimated_build_time: str
    tests_at_risk: List[str] = field(default_factory=list)
    risk_level: str = "low"  # low, medium, high, critical
    recommendation: str = ""


class ColorPalette:
    """Paleta de colores para terminal."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"


class DryRunMode:
    """Modo de simulación para preview de remediaciones."""

    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors and self._supports_colors()
        self.previews: List[FileChangePreview] = []
        self.c = ColorPalette if self.use_colors else self._NoColor()

    def _supports_colors(self) -> bool:
        """Verifica si el terminal soporta colores."""
        return hasattr(os, 'isatty') and os.isatty(1)

    class _NoColor:
        """Clase placeholder cuando no hay soporte de colores."""
        def __getattr__(self, _):
            return ""

    def simulate_remediation(
        self,
        cve_id: str,
        library: str,
        safe_version: str,
        project_files: Dict[str, str],
        proposed_changes: Dict[str, str]
    ) -> List[FileChangePreview]:
        """Simula una remediación y genera previews."""
        self.previews = []

        for file_path, new_content in proposed_changes.items():
            old_content = project_files.get(file_path, "")

            if old_content == new_content:
                continue

            # Calcular estadísticas
            old_lines = old_content.splitlines() if old_content else []
            new_lines = new_content.splitlines() if new_content else []

            lines_added = max(0, len(new_lines) - len(old_lines))
            lines_removed = max(0, len(old_lines) - len(new_lines))

            # Calcular líneas modificadas (usando diff)
            diff = list(difflib.unified_diff(old_lines, new_lines))
            lines_modified = self._count_modified_lines(diff)

            # Calcular impacto
            impact = self._calculate_impact(
                old_content, new_content, file_path, library
            )

            preview = FileChangePreview(
                file_path=file_path,
                before_content=old_content,
                after_content=new_content,
                lines_added=lines_added,
                lines_removed=lines_removed,
                lines_modified=lines_modified,
                impact_score=impact
            )
            self.previews.append(preview)

        return self.previews

    def _count_modified_lines(self, diff: List[str]) -> int:
        """Cuenta líneas modificadas en un diff."""
        modified = 0
        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                modified += 1
            elif line.startswith('-') and not line.startswith('---'):
                modified += 1
        return modified // 2  # Aproximación

    def _calculate_impact(
        self,
        old_content: str,
        new_content: str,
        file_path: str,
        library: str
    ) -> float:
        """Calcula score de impacto (0-100)."""
        score = 0.0

        # Impacto base por tamaño del cambio
        old_size = len(old_content) if old_content else 1
        new_size = len(new_content) if new_content else 1
        size_diff = abs(new_size - old_size)
        score += min(30, size_diff / old_size * 100)

        # Impacto por tipo de archivo
        if 'build.gradle' in file_path or 'main.gradle' in file_path:
            score += 20  # Archivos de build son críticos
        if 'dependencyMgmt' in file_path:
            score += 15  # Gestión de dependencias es importante

        # Impacto por librería
        if 'netty' in library.lower() or 'spring' in library.lower():
            score += 15  # Frameworks core

        # Reducir si es solo versión
        if old_content and new_content:
            old_vars = set(re.findall(r'\w+Version\s*=\s*[\'"][^\'"]+[\'"]', old_content))
            new_vars = set(re.findall(r'\w+Version\s*=\s*[\'"][^\'"]+[\'"]', new_content))
            if old_vars != new_vars:
                score -= 5  # Solo cambio de versión

        return min(100, score)

    def generate_colored_diff(self, preview: FileChangePreview) -> str:
        """Genera un diff coloreado para un preview."""
        c = self.c

        lines = []

        # Header del archivo
        header = f"{c.BOLD}{c.CYAN}📄 {preview.file_path}{c.RESET}"
        lines.append(header)

        # Stats
        stats = f"  {c.GREEN}+{preview.lines_added}{c.RESET} "
        stats += f"{c.RED}-{preview.lines_removed}{c.RESET} "
        stats += f"{c.YELLOW}~{preview.lines_modified}{c.RESET}"
        stats += f"  Impacto: {self._get_impact_color(preview.impact_score)}"
        lines.append(stats)
        lines.append("")

        # Diff
        old_lines = preview.before_content.splitlines(keepends=True) if preview.before_content else []
        new_lines = preview.after_content.splitlines(keepends=True) if preview.after_content else []

        diff = list(difflib.unified_diff(
            old_lines, new_lines,
            fromfile=f"a/{preview.file_path}",
            tofile=f"b/{preview.file_path}",
            lineterm=''
        ))

        for line in diff:
            colored_line = self._colorize_diff_line(line)
            lines.append(colored_line)

        return '\n'.join(lines)

    def _colorize_diff_line(self, line: str) -> str:
        """Aplica colores a una línea de diff."""
        c = self.c

        if line.startswith('+++'):
            return f"{c.GREEN}{c.BOLD}{line}{c.RESET}"
        elif line.startswith('---'):
            return f"{c.RED}{c.BOLD}{line}{c.RESET}"
        elif line.startswith('+') and not line.startswith('+++'):
            return f"{c.GREEN}{line}{c.RESET}"
        elif line.startswith('-') and not line.startswith('---'):
            return f"{c.RED}{line}{c.RESET}"
        elif line.startswith('@@'):
            return f"{c.CYAN}{c.BOLD}{line}{c.RESET}"
        elif line.startswith('diff --git'):
            return f"{c.MAGENTA}{c.BOLD}{line}{c.RESET}"
        else:
            return line

    def _get_impact_color(self, score: float) -> str:
        """Retorna el score de impacto con color."""
        c = self.c

        if score < 25:
            return f"{c.GREEN}● Bajo ({score:.0f}){c.RESET}"
        elif score < 50:
            return f"{c.YELLOW}● Medio ({score:.0f}){c.RESET}"
        elif score < 75:
            return f"{c.YELLOW}{c.BOLD}● Alto ({score:.0f}){c.RESET}"
        else:
            return f"{c.RED}{c.BOLD}● Crítico ({score:.0f}){c.RESET}"

    def estimate_impact(self, cve_id: str, library: str, previews: List[FileChangePreview]) -> ImpactEstimate:
        """Estima el impacto completo de una remediación."""
        if not previews:
            return ImpactEstimate(
                affected_files=0,
                total_lines_changed=0,
                potential_breaking_changes=0,
                estimated_build_time="N/A",
                risk_level="low",
                recommendation="No hay cambios propuestos"
            )

        total_files = len(previews)
        total_changes = sum(
            p.lines_added + p.lines_removed + p.lines_modified
            for p in previews
        )

        # Detectar cambios potencialmente breaking
        breaking = 0
        tests_at_risk = []

        for p in previews:
            # Cambios en versiones mayores
            if 'Version' in p.before_content and 'Version' in p.after_content:
                old_ver = self._extract_version(p.before_content)
                new_ver = self._extract_version(p.after_content)
                if old_ver and new_ver:
                    old_major = old_ver.split('.')[0] if old_ver else '0'
                    new_major = new_ver.split('.')[0] if new_ver else '0'
                    if old_major != new_major:
                        breaking += 1
                        tests_at_risk.append(f"Cambio de versión mayor en {os.path.basename(p.file_path)}")

            # Cambios en archivos de infraestructura
            if 'dependencyMgmt' in p.file_path:
                breaking += 1

        # Calcular nivel de riesgo
        avg_impact = sum(p.impact_score for p in previews) / len(previews)
        if avg_impact >= 70 or breaking >= 2:
            risk_level = "critical"
        elif avg_impact >= 50 or breaking >= 1:
            risk_level = "high"
        elif avg_impact >= 25:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Estimar tiempo de build
        if total_changes < 10:
            build_time = "1-2 min"
        elif total_changes < 50:
            build_time = "2-5 min"
        else:
            build_time = "5-10 min"

        # Generar recomendación
        recommendation = self._generate_recommendation(risk_level, breaking)

        return ImpactEstimate(
            affected_files=total_files,
            total_lines_changed=total_changes,
            potential_breaking_changes=breaking,
            estimated_build_time=build_time,
            tests_at_risk=tests_at_risk,
            risk_level=risk_level,
            recommendation=recommendation
        )

    def _extract_version(self, content: str) -> Optional[str]:
        """Extrae versión de contenido."""
        import re
        match = re.search(r"=\s*['\"]([^'\"]+)['\"]", content)
        return match.group(1) if match else None

    def _generate_recommendation(self, risk_level: str, breaking: int) -> str:
        """Genera recomendación basada en el riesgo."""
        if risk_level == "critical":
            return "⚠️ REVISIÓN MANUAL REQUERIDA: Cambios de alto impacto detectados. Se recomienda revisión de arquitecto."
        elif risk_level == "high":
            return "⚡ ATENCIÓN: Posibles breaking changes. Ejecutar tests exhaustivos."
        elif risk_level == "medium":
            return "✓ APROBADO CON PRECAUCIÓN: Revisar cambios en staging antes de producción."
        else:
            return "✓ SEGURO: Cambios de bajo riesgo. Puede aplicarse automáticamente."

    def print_full_report(
        self,
        cve_id: str,
        library: str,
        safe_version: str,
        previews: List[FileChangePreview]
    ):
        """Imprime reporte completo del modo dry-run."""
        c = self.c

        print("\n" + "=" * 70)
        print(f"{c.BOLD}{c.CYAN}🔄 DRY-RUN MODE PREVIEW{c.RESET}")
        print("=" * 70)

        print(f"\n{c.BOLD}Vulnerabilidad:{c.RESET} {cve_id}")
        print(f"{c.BOLD}Librería:{c.RESET} {library}")
        print(f"{c.BOLD}Versión propuesta:{c.RESET} {c.GREEN}{safe_version}{c.RESET}")

        # Diffs por archivo
        print(f"\n{c.BOLD}📋 Cambios Propuestos:{c.RESET}")
        print("-" * 70)

        for preview in previews:
            diff_output = self.generate_colored_diff(preview)
            print(diff_output)
            print("-" * 70)

        # Estimación de impacto
        estimate = self.estimate_impact(cve_id, library, previews)

        print(f"\n{c.BOLD}📊 Estimación de Impacto:{c.RESET}")
        print(f"  Archivos afectados: {c.CYAN}{estimate.affected_files}{c.RESET}")
        print(f"  Líneas totales modificadas: {c.CYAN}{estimate.total_lines_changed}{c.RESET}")
        print(f"  Cambios potencialmente breaking: {c.YELLOW if estimate.potential_breaking_changes > 0 else c.GREEN}{estimate.potential_breaking_changes}{c.RESET}")
        print(f"  Tiempo estimado de build: {c.CYAN}{estimate.estimated_build_time}{c.RESET}")

        print(f"\n{c.BOLD}🎯 Nivel de Riesgo:{c.RESET}")
        risk_colors = {
            "low": c.GREEN,
            "medium": c.YELLOW,
            "high": c.RED,
            "critical": c.RED + c.BOLD
        }
        risk_symbol = {"low": "●", "medium": "●", "high": "▲", "critical": "⚠"}
        rc = risk_colors.get(estimate.risk_level, c.WHITE)
        rs = risk_symbol.get(estimate.risk_level, "●")
        print(f"  {rc}{rs} {estimate.risk_level.upper()}{c.RESET}")

        if estimate.tests_at_risk:
            print(f"\n{c.BOLD}⚠️ Tests Potencialmente Afectados:{c.RESET}")
            for test in estimate.tests_at_risk:
                print(f"  • {c.YELLOW}{test}{c.RESET}")

        print(f"\n{c.BOLD}💡 Recomendación:{c.RESET}")
        print(f"  {estimate.recommendation}")

        print("\n" + "=" * 70)
        print(f"{c.DIM}Modo dry-run activado: No se aplicaron cambios{c.RESET}")
        print("=" * 70 + "\n")


class DryRunReportGenerator:
    """Generador de reportes de dry-run en diferentes formatos."""

    def __init__(self, previews: List[FileChangePreview]):
        self.previews = previews

    def generate_markdown_report(self, cve_id: str, library: str) -> str:
        """Genera reporte en formato Markdown."""
        lines = [
            f"# Dry-Run Report: {cve_id}",
            "",
            f"**Librería:** `{library}`",
            f"**Fecha:** {__import__('datetime').datetime.now().isoformat()}",
            "",
            "## Cambios Propuestos",
            ""
        ]

        for preview in self.previews:
            lines.append(f"### {preview.file_path}")
            lines.append(f"- Líneas agregadas: {preview.lines_added}")
            lines.append(f"- Líneas eliminadas: {preview.lines_removed}")
            lines.append(f"- Impacto: {preview.impact_score:.0f}/100")
            lines.append("")
            lines.append("```diff")

            old_lines = preview.before_content.splitlines(keepends=True) if preview.before_content else []
            new_lines = preview.after_content.splitlines(keepends=True) if preview.after_content else []

            diff = difflib.unified_diff(
                old_lines, new_lines,
                fromfile=f"a/{preview.file_path}",
                tofile=f"b/{preview.file_path}",
                lineterm=''
            )
            lines.extend([f"{line}" for line in diff])
            lines.append("```")
            lines.append("")

        return '\n'.join(lines)

    def save_report(self, output_path: str, cve_id: str, library: str):
        """Guarda el reporte a un archivo."""
        report = self.generate_markdown_report(cve_id, library)
        with open(output_path, 'w') as f:
            f.write(report)
        print(f"[DRY-RUN] Reporte guardado en: {output_path}")


import re
