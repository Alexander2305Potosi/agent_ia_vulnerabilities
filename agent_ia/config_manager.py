"""
agent_ia/config_manager.py

Configuración Declarativa para el Agente de Remediación v.3.0
Soporta archivos .remediation.yaml por proyecto.
"""

import os
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class MicroserviceOverride:
    """Configuración específica para un microservicio."""
    name: str
    enabled: bool = True
    exclude_vulnerabilities: List[str] = field(default_factory=list)
    custom_variables: Dict[str, str] = field(default_factory=dict)
    additional_repositories: List[str] = field(default_factory=list)


@dataclass
class RemediationRule:
    """Regla personalizada de remediación."""
    library_pattern: str
    variable_name: Optional[str] = None
    version_override: Optional[str] = None
    skip: bool = False
    priority: str = "normal"  # low, normal, high, critical


@dataclass
class AgentConfig:
    """Configuración completa del agente."""
    version: str = "3.0"
    project_name: str = "default"

    # Configuración global
    enabled: bool = True
    dry_run: bool = False
    auto_commit: bool = False
    max_retries: int = 3
    parallel_processing: bool = True
    max_workers: int = 4

    # Configuración de JDK
    preferred_jdk_versions: List[str] = field(default_factory=lambda: ["21", "17"])
    jdk_auto_detect: bool = True

    # Configuración de Gradle
    gradle_wrapper_required: bool = False
    gradle_offline_mode: bool = False

    # Configuración de remediación
    default_strategy: str = "TRANSITIVE"
    allow_downgrades: bool = False
    version_conflict_resolution: str = "latest"  # latest, conservative, strict

    # Reglas personalizadas
    rules: List[RemediationRule] = field(default_factory=list)

    # Overrides por microservicio
    microservice_overrides: Dict[str, MicroserviceOverride] = field(default_factory=dict)

    # Exclusiones globales
    global_exclusions: List[str] = field(default_factory=list)

    # Notificaciones
    notify_on_completion: bool = False
    notify_channels: List[str] = field(default_factory=list)


class ConfigManager:
    """Gestor de configuración declarativa."""

    CONFIG_FILE = ".remediation.yaml"
    LEGACY_CONFIG_FILES = [".remediation.yml", "remediation.yaml", "remediation.yml"]

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.config: Optional[AgentConfig] = None
        self._load_config()

    def _load_config(self):
        """Carga la configuración desde archivo."""
        config_path = self._find_config_file()

        if config_path:
            self.config = self._parse_yaml_config(config_path)
        else:
            self.config = AgentConfig()

    def _find_config_file(self) -> Optional[str]:
        """Busca archivo de configuración."""
        # Buscar en orden de prioridad
        for filename in [self.CONFIG_FILE] + self.LEGACY_CONFIG_FILES:
            path = os.path.join(self.project_root, filename)
            if os.path.exists(path):
                return path

        # Buscar en subdirectorios (máximo 2 niveles)
        for root, dirs, files in os.walk(self.project_root):
            depth = root.count(os.sep) - self.project_root.count(os.sep)
            if depth > 2:
                continue

            for filename in [self.CONFIG_FILE] + self.LEGACY_CONFIG_FILES:
                if filename in files:
                    return os.path.join(root, filename)

        return None

    def _parse_yaml_config(self, config_path: str) -> AgentConfig:
        """Parsea archivo YAML de configuración."""
        # Usar PyYAML si está disponible, sino parseo manual simple
        try:
            import yaml
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
        except ImportError:
            data = self._manual_yaml_parse(config_path)
        except Exception as e:
            print(f"[CONFIG] Error parseando {config_path}: {e}")
            data = {}

        if not data:
            return AgentConfig()

        return self._dict_to_config(data)

    def _manual_yaml_parse(self, config_path: str) -> Dict:
        """Parseo manual simple de YAML (fallback)."""
        data = {}
        current_section = None
        current_list = None

        with open(config_path, 'r') as f:
            for line in f:
                line = line.rstrip()
                if not line or line.startswith('#'):
                    continue

                # Sección de nivel superior
                if not line.startswith(' ') and ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()

                    if value:
                        data[key] = self._parse_value(value)
                    else:
                        current_section = key
                        data[current_section] = {}
                        current_list = None

                # Elemento de lista
                elif line.strip().startswith('- '):
                    item = line.strip()[2:]
                    if current_list is None:
                        current_list = []
                        if current_section:
                            data[current_section] = current_list
                    current_list.append(self._parse_value(item))

                # Valor anidado
                elif current_section and ':' in line:
                    indent = len(line) - len(line.lstrip())
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()

                    if isinstance(data[current_section], dict):
                        data[current_section][key] = self._parse_value(value)

        return data

    def _parse_value(self, value: str) -> Any:
        """Parsea un valor YAML simple."""
        value = value.strip()
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False
        if value.isdigit():
            return int(value)
        if value.startswith('[') and value.endswith(']'):
            # Lista simple
            items = value[1:-1].split(',')
            return [i.strip().strip('"\'') for i in items if i.strip()]
        return value.strip('"\'')

    def _dict_to_config(self, data: Dict) -> AgentConfig:
        """Convierte diccionario a objeto AgentConfig."""
        config = AgentConfig()

        # Propiedades simples
        if 'project_name' in data:
            config.project_name = data['project_name']
        if 'enabled' in data:
            config.enabled = data['enabled']
        if 'dry_run' in data:
            config.dry_run = data['dry_run']
        if 'auto_commit' in data:
            config.auto_commit = data['auto_commit']
        if 'max_retries' in data:
            config.max_retries = data['max_retries']
        if 'parallel_processing' in data:
            config.parallel_processing = data['parallel_processing']
        if 'max_workers' in data:
            config.max_workers = data['max_workers']

        # JDK
        jdk_config = data.get('jdk', {})
        if 'preferred_versions' in jdk_config:
            config.preferred_jdk_versions = jdk_config['preferred_versions']
        if 'auto_detect' in jdk_config:
            config.jdk_auto_detect = jdk_config['auto_detect']

        # Gradle
        gradle_config = data.get('gradle', {})
        if 'wrapper_required' in gradle_config:
            config.gradle_wrapper_required = gradle_config['wrapper_required']
        if 'offline_mode' in gradle_config:
            config.gradle_offline_mode = gradle_config['offline_mode']

        # Remediation
        remediation_config = data.get('remediation', {})
        if 'default_strategy' in remediation_config:
            config.default_strategy = remediation_config['default_strategy']
        if 'allow_downgrades' in remediation_config:
            config.allow_downgrades = remediation_config['allow_downgrades']
        if 'version_conflict_resolution' in remediation_config:
            config.version_conflict_resolution = remediation_config['version_conflict_resolution']

        # Rules
        rules_config = data.get('rules', [])
        for rule_data in rules_config:
            if isinstance(rule_data, dict):
                rule = RemediationRule(
                    library_pattern=rule_data.get('library_pattern', ''),
                    variable_name=rule_data.get('variable_name'),
                    version_override=rule_data.get('version_override'),
                    skip=rule_data.get('skip', False),
                    priority=rule_data.get('priority', 'normal')
                )
                config.rules.append(rule)

        # Microservice overrides
        ms_config = data.get('microservices', {})
        for ms_name, ms_data in ms_config.items():
            if isinstance(ms_data, dict):
                override = MicroserviceOverride(
                    name=ms_name,
                    enabled=ms_data.get('enabled', True),
                    exclude_vulnerabilities=ms_data.get('exclude_vulnerabilities', []),
                    custom_variables=ms_data.get('custom_variables', {}),
                    additional_repositories=ms_data.get('additional_repositories', [])
                )
                config.microservice_overrides[ms_name] = override

        # Global exclusions
        if 'exclusions' in data:
            config.global_exclusions = data['exclusions']

        return config

    def get_config(self) -> AgentConfig:
        """Retorna la configuración cargada."""
        return self.config

    def is_microservice_enabled(self, ms_name: str) -> bool:
        """Verifica si un microservicio está habilitado."""
        if not self.config.enabled:
            return False

        override = self.config.microservice_overrides.get(ms_name)
        if override:
            return override.enabled

        return True

    def get_custom_variable(self, ms_name: str, library: str) -> Optional[str]:
        """Obtiene variable personalizada para una librería."""
        # Primero buscar en rules
        for rule in self.config.rules:
            if re.search(rule.library_pattern, library, re.I):
                if rule.variable_name:
                    return rule.variable_name

        # Luego en overrides del microservicio
        override = self.config.microservice_overrides.get(ms_name)
        if override:
            return override.custom_variables.get(library)

        return None

    def should_skip_vulnerability(self, ms_name: str, cve_id: str) -> bool:
        """Verifica si una vulnerabilidad debe ser ignorada."""
        if cve_id in self.config.global_exclusions:
            return True

        override = self.config.microservice_overrides.get(ms_name)
        if override and cve_id in override.exclude_vulnerabilities:
            return True

        return False

    def get_version_override(self, library: str) -> Optional[str]:
        """Obtiene versión override para una librería."""
        for rule in self.config.rules:
            if re.search(rule.library_pattern, library, re.I):
                if rule.version_override:
                    return rule.version_override
        return None

    def should_skip_library(self, library: str) -> bool:
        """Verifica si una librería debe ser ignorada."""
        for rule in self.config.rules:
            if re.search(rule.library_pattern, library, re.I):
                return rule.skip
        return False

    def save_default_config(self, output_path: str = None):
        """Genera un archivo de configuración por defecto."""
        config_path = output_path or os.path.join(self.project_root, self.CONFIG_FILE)

        default_config = '''# Configuración del Agente de Remediación v.3.0
# Documentación: agent_ia/docs/remediation_rules.md

project_name: "Mi Proyecto"

# Modo de operación
enabled: true
dry_run: false
auto_commit: false

# Configuración de procesamiento
max_retries: 3
parallel_processing: true
max_workers: 4

# JDK Configuration
jdk:
  preferred_versions:
    - "21"
    - "17"
  auto_detect: true

# Gradle Configuration
gradle:
  wrapper_required: false
  offline_mode: false

# Remediation Settings
remediation:
  default_strategy: "TRANSITIVE"
  allow_downgrades: false
  version_conflict_resolution: "latest"

# Custom Rules
rules:
  - library_pattern: "io\.netty.*"
    variable_name: "nettyVersion"
    priority: "high"

  - library_pattern: "org\.springframework.*"
    skip: false
    priority: "critical"

# Microservice-specific Overrides
microservices:
  ms-auth:
    enabled: true
    exclude_vulnerabilities:
      - "CVE-2025-0001"  # Ejemplo: ignorar CVE específico
    custom_variables:
      "io.netty:netty-handler": "nettyVersion"

  ms-sales:
    enabled: true
    additional_repositories:
      - "https://custom.repo.example.com"

# Global Exclusions
global_exclusions:
  - "CVE-2024-IGNORED"
'''

        with open(config_path, 'w') as f:
            f.write(default_config)

        print(f"[CONFIG] Configuración por defecto creada en: {config_path}")


class ConfigValidator:
    """Validador de configuraciones."""

    VALID_STRATEGIES = ["TRANSITIVE", "DIRECT", "BOTH"]
    VALID_PRIORITIES = ["low", "normal", "high", "critical"]
    VALID_VERSION_CONFLICTS = ["latest", "conservative", "strict"]

    def __init__(self, config: AgentConfig):
        self.config = config
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> bool:
        """Valida la configuración completa."""
        self.errors = []
        self.warnings = []

        self._validate_basic()
        self._validate_rules()
        self._validate_microservices()
        self._validate_jdk()

        return len(self.errors) == 0

    def _validate_basic(self):
        """Valida configuración básica."""
        if self.config.max_retries < 0:
            self.errors.append("max_retries no puede ser negativo")

        if self.config.max_workers < 1:
            self.errors.append("max_workers debe ser al menos 1")

        if self.config.default_strategy not in self.VALID_STRATEGIES:
            self.errors.append(f"default_strategy debe ser uno de: {self.VALID_STRATEGIES}")

        if self.config.version_conflict_resolution not in self.VALID_VERSION_CONFLICTS:
            self.errors.append(f"version_conflict_resolution debe ser uno de: {self.VALID_VERSION_CONFLICTS}")

    def _validate_rules(self):
        """Valida reglas personalizadas."""
        for i, rule in enumerate(self.config.rules):
            if not rule.library_pattern:
                self.errors.append(f"Rule {i}: library_pattern es requerido")

            if rule.priority not in self.VALID_PRIORITIES:
                self.warnings.append(f"Rule {i}: prioridad desconocida '{rule.priority}'")

            # Validar regex
            try:
                re.compile(rule.library_pattern)
            except re.error:
                self.errors.append(f"Rule {i}: library_pattern no es un regex válido")

    def _validate_microservices(self):
        """Valida overrides de microservicios."""
        for ms_name, override in self.config.microservice_overrides.items():
            if not ms_name:
                self.warnings.append("Microservice override con nombre vacío")

    def _validate_jdk(self):
        """Valida configuración de JDK."""
        valid_versions = ["8", "11", "17", "21"]
        for v in self.config.preferred_jdk_versions:
            if v not in valid_versions:
                self.warnings.append(f"JDK versión {v} puede no ser soportada")

    def get_report(self) -> Dict:
        """Retorna reporte de validación."""
        return {
            'valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings
        }
