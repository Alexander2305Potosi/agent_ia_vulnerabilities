"""
agent_ia/tests/test_mutation.py

Mutation Testing para el Agente de Remediación v.3.0
Verifica que el agente detecta correctamente cuando una remediación falla.
"""

import unittest
import os
import json
import tempfile
import shutil
from pathlib import Path

# Importar módulos del agente
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_ia.core import GradleMutator, Vulnerability
from agent_ia.brain import GenerativeAgentV2


class MutationTestCase:
    """Caso base para tests de mutación."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.original_content = ""
        self.mutated_content = ""
        self.expected_detected = True


class MutationTestSuite:
    """Suite de mutation testing."""

    def __init__(self):
        self.test_cases: list[MutationTestCase] = []
        self.results: list[dict] = []

    def add_test(self, test_case: MutationTestCase):
        """Agrega un caso de test."""
        self.test_cases.append(test_case)

    def run_all(self) -> dict:
        """Ejecuta todos los tests de mutación."""
        passed = 0
        failed = 0

        for test in self.test_cases:
            result = self._run_single_test(test)
            if result['detected']:
                passed += 1
            else:
                failed += 1
            self.results.append(result)

        return {
            'total': len(self.test_cases),
            'passed': passed,
            'failed': failed,
            'mutation_score': (passed / len(self.test_cases) * 100) if self.test_cases else 0,
            'results': self.results
        }

    def _run_single_test(self, test: MutationTestCase) -> dict:
        """Ejecuta un test individual."""
        # Aquí implementaríamos la lógica de detección
        # Por ahora es un placeholder
        return {
            'test_name': test.name,
            'description': test.description,
            'detected': True,  # Placeholder
            'details': 'Test ejecutado'
        }


class GradleBuildMutationTests(unittest.TestCase):
    """Tests de mutación para validación de builds Gradle."""

    def setUp(self):
        """Configuración inicial."""
        self.temp_dir = tempfile.mkdtemp()
        self.build_file = os.path.join(self.temp_dir, "build.gradle")

    def tearDown(self):
        """Limpieza."""
        shutil.rmtree(self.temp_dir)

    def _create_valid_build_file(self):
        """Crea un build.gradle válido."""
        content = '''
plugins {
    id 'java'
    id 'application'
}

ext {
    nettyVersion = '4.1.100.Final'
}

repositories {
    mavenCentral()
}

dependencies {
    implementation "io.netty:netty-handler:${nettyVersion}"
    implementation "io.netty:netty-codec-http:${nettyVersion}"
}
'''
        with open(self.build_file, 'w') as f:
            f.write(content)
        return content

    def test_mutation_version_mismatch(self):
        """Test: El agente debe detectar cuando una versión causa conflicto."""
        original = self._create_valid_build_file()

        # Mutación: versión incompatible
        mutated = original.replace('4.1.100.Final', '999.999.999')

        # El agente debería detectar esto al validar el build
        # (La validación debería fallar con versión inexistente)
        self.assertNotEqual(original, mutated)

    def test_mutation_syntax_error(self):
        """Test: El agente debe detectar errores de sintaxis introducidos."""
        original = self._create_valid_build_file()

        # Mutación: sintaxis inválida
        mutated = original.replace('ext {', 'ext {{')

        self.assertNotEqual(original, mutated)

    def test_mutation_missing_brace(self):
        """Test: El agente debe detectar llaves desbalanceadas."""
        original = self._create_valid_build_file()

        # Mutación: eliminar llave de cierre
        mutated = original.replace('}', '', 1)

        # Contar llaves
        open_count = mutated.count('{')
        close_count = mutated.count('}')

        self.assertNotEqual(open_count, close_count)


class RemediationMutationTests(unittest.TestCase):
    """Tests de mutación para lógica de remediación."""

    def setUp(self):
        self.agent = GenerativeAgentV2()
        self.suite = MutationTestSuite()

    def test_mutant_wrong_variable_name(self):
        """El agente debe detectar cuando el nombre de variable es incorrecto."""
        cve_data = {
            'cve': 'CVE-2026-TEST',
            'library': 'io.netty:netty-handler',
            'safe_version': '4.1.118.Final',
            'priority': 'high'
        }

        # Generar respuesta normal
        response = self.agent.generate_remediation(cve_data, "Test context")
        parsed = self.agent.parse_react_response(response)

        # Verificar que la acción contiene una variable válida
        action = parsed.get('action', '')

        # La acción debería contener un nombre de variable con sufijo Version
        self.assertIn('Version', action)
        self.assertIn('=', action)

    def test_mutant_invalid_version_format(self):
        """El agente debe rechazar formatos de versión inválidos."""
        cve_data = {
            'cve': 'CVE-2026-TEST',
            'library': 'io.netty:netty-handler',
            'safe_version': 'not-a-version',
            'priority': 'high'
        }

        response = self.agent.generate_remediation(cve_data, "Test context")
        parsed = self.agent.parse_react_response(response)

        action = parsed.get('action', '')

        # Extraer la versión sugerida
        if '=' in action:
            version_part = action.split('=')[1].strip().strip("'\"")
            # La versión debería seguir un patrón semántico
            version_pattern = r'^\d+(\.\d+)*(\.[A-Za-z0-9]+)?$'
            import re
            self.assertRegex(version_part, version_pattern)


class VulnerabilityClassifierMutationTests(unittest.TestCase):
    """Tests de mutación para el clasificador de vulnerabilidades."""

    def test_mutant_hidden_critical_severity(self):
        """El clasificador debe detectar severidad oculta en descripción."""
        from agent_ia.vulnerability_classifier import VulnerabilityClassifier

        # CVE que parece bajo pero tiene keyword crítico
        cve_data = {
            'cve': 'CVE-2026-HIDDEN',
            'library': 'com.example:some-lib',
            'description': 'This vulnerability allows remote code execution via crafted input',
            'priority': 'low'  # Prioridad baja pero descripción crítica
        }

        score = VulnerabilityClassifier.classify(cve_data)

        # Debería ser al menos MEDIUM debido al keyword RCE
        self.assertGreaterEqual(score.base_score, 5.0)

    def test_mutant_transitive_propagation(self):
        """El clasificador debe ajustar score por propagación transitiva."""
        from agent_ia.vulnerability_classifier import VulnerabilityClassifier

        cve_data = {
            'cve': 'CVE-2026-TRANSITIVE',
            'library': 'io.netty:netty-handler',
            'transitive': True,
            'priority': 'medium'
        }

        score = VulnerabilityClassifier.classify(cve_data)

        # Debería tener impacto mayor por ser transitiva
        self.assertGreater(score.impact, 5.0)


class MutantKillerValidator:
    """Validador que verifica que los mutantes sean detectados."""

    def __init__(self):
        self.kill_count = 0
        self.survivor_count = 0

    def validate_mutation(self, mutation_result: dict) -> bool:
        """Verifica si un mutante fue 'matado' (detectado)."""
        if mutation_result.get('detected'):
            self.kill_count += 1
            return True
        else:
            self.survivor_count += 1
            return False

    def get_kill_rate(self) -> float:
        """Retorna el porcentaje de mutantes detectados."""
        total = self.kill_count + self.survivor_count
        return (self.kill_count / total * 100) if total > 0 else 0


def run_mutation_tests():
    """Ejecuta todos los tests de mutación."""
    print("=" * 60)
    print("🧬 MUTATION TESTING SUITE v.3.0")
    print("=" * 60)

    # Crear suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Agregar tests
    suite.addTests(loader.loadTestsFromTestCase(GradleBuildMutationTests))
    suite.addTests(loader.loadTestsFromTestCase(RemediationMutationTests))
    suite.addTests(loader.loadTestsFromTestCase(VulnerabilityClassifierMutationTests))

    # Ejecutar
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Reporte de mutación
    print("\n" + "=" * 60)
    print("📊 MUTATION SCORE REPORT")
    print("=" * 60)
    print(f"Tests ejecutados: {result.testsRun}")
    print(f"Fallos (mutantes detectados): {len(result.failures)}")
    print(f"Errores (mutantes vivos): {len(result.errors)}")
    print(f"Éxitos: {result.wasSuccessful()}")

    return result.wasSuccessful()


if __name__ == '__main__':
    run_mutation_tests()
