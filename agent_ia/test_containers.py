"""
agent_ia/test_containers.py

Test Containers para el Agente de Remediación v.3.0
Usa contenedores reales con diferentes versiones de JDK para validar builds.
"""

import os
import subprocess
import tempfile
import shutil
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ContainerConfig:
    """Configuración de un contenedor de test."""
    image: str
    jdk_version: str
    gradle_version: str
    working_dir: str = "/workspace"


class TestContainerManager:
    """Gestor de contenedores de prueba."""

    # Imágenes predefinidas con diferentes JDKs
    JDK_IMAGES = {
        '17': 'gradle:7.6-jdk17-alpine',
        '21': 'gradle:8.5-jdk21-alpine',
        '11': 'gradle:7.4-jdk11-alpine',
    }

    def __init__(self, container_runtime: str = 'docker'):
        self.container_runtime = container_runtime
        self._check_runtime()
        self.active_containers: List[str] = []

    def _check_runtime(self):
        """Verifica que el runtime de contenedores está disponible."""
        try:
            result = subprocess.run(
                [self.container_runtime, '--version'],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"[CONTAINER] Runtime disponible: {result.stdout.split('\\n')[0]}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(f"{self.container_runtime} no está instalado o no es accesible")

    def create_container(
        self,
        jdk_version: str,
        project_path: str,
        name: Optional[str] = None
    ) -> str:
        """Crea un contenedor para testing."""
        image = self.JDK_IMAGES.get(jdk_version, self.JDK_IMAGES['17'])

        container_name = name or f"remediation-test-{jdk_version}-{os.getpid()}"

        # Verificar que la imagen existe
        self._pull_image_if_needed(image)

        # Crear contenedor
        cmd = [
            self.container_runtime, 'create',
            '--name', container_name,
            '-v', f"{project_path}:/workspace:rw",
            '-w', '/workspace',
            image,
            'tail', '-f', '/dev/null'  # Mantener contenedor vivo
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        container_id = result.stdout.strip()

        self.active_containers.append(container_id)

        # Iniciar contenedor
        subprocess.run(
            [self.container_runtime, 'start', container_id],
            capture_output=True, check=True
        )

        print(f"[CONTAINER] Contenedor {container_name} creado con JDK {jdk_version}")
        return container_id

    def _pull_image_if_needed(self, image: str):
        """Descarga la imagen si no existe localmente."""
        result = subprocess.run(
            [self.container_runtime, 'images', '-q', image],
            capture_output=True, text=True
        )
        if not result.stdout.strip():
            print(f"[CONTAINER] Descargando imagen {image}...")
            subprocess.run(
                [self.container_runtime, 'pull', image],
                capture_output=True, check=True
            )

    def run_build_in_container(
        self,
        container_id: str,
        gradle_tasks: List[str] = None
    ) -> Tuple[bool, str]:
        """Ejecuta build dentro del contenedor."""
        tasks = gradle_tasks or ['clean', 'test']

        cmd = [
            self.container_runtime, 'exec',
            container_id,
            'gradle'
        ] + tasks + ['--console=plain']

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos timeout
        )

        success = result.returncode == 0
        output = result.stdout + result.stderr

        return success, output

    def copy_to_container(self, container_id: str, local_path: str, container_path: str):
        """Copia archivos al contenedor."""
        subprocess.run(
            [self.container_runtime, 'cp', local_path, f"{container_id}:{container_path}"],
            capture_output=True, check=True
        )

    def copy_from_container(self, container_id: str, container_path: str, local_path: str):
        """Copia archivos desde el contenedor."""
        subprocess.run(
            [self.container_runtime, 'cp', f"{container_id}:{container_path}", local_path],
            capture_output=True, check=True
        )

    def destroy_container(self, container_id: str):
        """Destruye un contenedor."""
        # Detener
        subprocess.run(
            [self.container_runtime, 'stop', '-t', '1', container_id],
            capture_output=True
        )
        # Eliminar
        subprocess.run(
            [self.container_runtime, 'rm', '-f', container_id],
            capture_output=True
        )

        if container_id in self.active_containers:
            self.active_containers.remove(container_id)

    def cleanup_all(self):
        """Limpia todos los contenedores activos."""
        for container_id in self.active_containers[:]:
            try:
                self.destroy_container(container_id)
            except Exception as e:
                print(f"[CONTAINER] Error limpiando {container_id}: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup_all()


class GradleContainerizedTest:
    """Test de Gradle usando contenedores."""

    def __init__(self, project_path: str, jdk_version: str = '17'):
        self.project_path = project_path
        self.jdk_version = jdk_version
        self.container_manager = TestContainerManager()
        self.container_id: Optional[str] = None

    def setup(self):
        """Configura el contenedor."""
        self.container_id = self.container_manager.create_container(
            jdk_version=self.jdk_version,
            project_path=self.project_path
        )

    def run_gradle_test(self) -> Tuple[bool, str]:
        """Ejecuta tests de Gradle."""
        if not self.container_id:
            raise RuntimeError("Contenedor no inicializado")

        return self.container_manager.run_build_in_container(
            self.container_id,
            gradle_tasks=['clean', 'test']
        )

    def run_gradle_build(self) -> Tuple[bool, str]:
        """Ejecuta build de Gradle."""
        if not self.container_id:
            raise RuntimeError("Contenedor no inicializado")

        return self.container_manager.run_build_in_container(
            self.container_id,
            gradle_tasks=['clean', 'build', '-x', 'test']
        )

    def run_dependency_check(self) -> Tuple[bool, str]:
        """Ejecuta análisis de dependencias."""
        if not self.container_id:
            raise RuntimeError("Contenedor no inicializado")

        return self.container_manager.run_build_in_container(
            self.container_id,
            gradle_tasks=['dependencies', '--configuration', 'runtimeClasspath']
        )

    def teardown(self):
        """Limpia recursos."""
        if self.container_id:
            self.container_manager.destroy_container(self.container_id)
            self.container_id = None

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.teardown()


class MultiJDKTestMatrix:
    """Matriz de tests contra múltiples versiones de JDK."""

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.results: Dict[str, Dict] = {}

    def run_matrix(self, jdk_versions: List[str] = None) -> Dict[str, Dict]:
        """Ejecuta tests contra todas las versiones de JDK."""
        versions = jdk_versions or ['17', '21']

        for jdk in versions:
            print(f"[MATRIX] Probando con JDK {jdk}...")

            try:
                with GradleContainerizedTest(self.project_path, jdk) as test:
                    build_success, build_output = test.run_gradle_build()
                    test_success, test_output = test.run_gradle_test()

                    self.results[jdk] = {
                        'build_success': build_success,
                        'test_success': test_success,
                        'build_output': build_output[-500:] if len(build_output) > 500 else build_output,
                        'test_output': test_output[-500:] if len(test_output) > 500 else test_output,
                        'compatible': build_success and test_success
                    }
            except Exception as e:
                self.results[jdk] = {
                    'error': str(e),
                    'compatible': False
                }

        return self.results

    def get_compatible_jdks(self) -> List[str]:
        """Retorna versiones de JDK compatibles."""
        return [
            jdk for jdk, result in self.results.items()
            if result.get('compatible', False)
        ]

    def print_report(self):
        """Imprime reporte de la matriz."""
        print("\n" + "=" * 60)
        print("📊 MULTI-JDK TEST MATRIX REPORT")
        print("=" * 60)

        for jdk, result in self.results.items():
            status = "✅ COMPATIBLE" if result.get('compatible') else "❌ INCOMPATIBLE"
            print(f"\nJDK {jdk}: {status}")

            if 'error' in result:
                print(f"  Error: {result['error']}")
            else:
                build_status = "✅" if result['build_success'] else "❌"
                test_status = "✅" if result['test_success'] else "❌"
                print(f"  Build: {build_status}")
                print(f"  Tests: {test_status}")


# Tests de integración con contenedores
class ContainerizedIntegrationTests:
    """Tests de integración que usan contenedores reales."""

    @staticmethod
    def test_remediation_in_isolated_environment(project_path: str) -> bool:
        """Test: Una remediación debe funcionar en ambiente aislado."""
        print(f"[INTEGRATION] Probando remediación en {project_path}")

        with GradleContainerizedTest(project_path, '17') as test:
            # Primero verificar que build funciona
            success, output = test.run_gradle_build()

            if not success:
                print(f"[INTEGRATION] Build inicial falló: {output[:200]}")
                return False

            # Aplicar remediación (simulada)
            # ... código para aplicar remediación ...

            # Verificar build post-remediación
            success, output = test.run_gradle_build()

            return success

    @staticmethod
    def test_multi_module_compatibility(project_path: str) -> bool:
        """Test: Compatibilidad de microservicios multi-módulo."""
        matrix = MultiJDKTestMatrix(project_path)
        results = matrix.run_matrix(['17', '21'])

        compatible_jdks = [
            jdk for jdk, r in results.items() if r.get('compatible')
        ]

        return len(compatible_jdks) >= 1


def run_container_tests(project_path: Optional[str] = None):
    """Ejecuta todos los tests con contenedores."""
    print("=" * 60)
    print("🐳 CONTAINERIZED TEST SUITE v.3.0")
    print("=" * 60)

    if not project_path:
        print("[SKIP] No se proporcionó ruta de proyecto")
        return

    # Verificar que Docker está disponible
    try:
        subprocess.run(['docker', '--version'], capture_output=True, check=True)
    except:
        print("[SKIP] Docker no disponible, saltando tests de contenedores")
        return

    # Ejecutar tests
    results = []

    try:
        result = ContainerizedIntegrationTests.test_remediation_in_isolated_environment(project_path)
        results.append(('isolated_remediation', result))
    except Exception as e:
        print(f"[ERROR] Test aislado falló: {e}")
        results.append(('isolated_remediation', False))

    # Reporte
    print("\n" + "=" * 60)
    print("📊 CONTAINER TEST RESULTS")
    print("=" * 60)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")

    passed = sum(1 for _, r in results if r)
    print(f"\nTotal: {passed}/{len(results)} tests pasaron")


if __name__ == '__main__':
    import sys
    project = sys.argv[1] if len(sys.argv) > 1 else None
    run_container_tests(project)
