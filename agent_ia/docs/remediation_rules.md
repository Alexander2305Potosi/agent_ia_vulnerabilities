# Master Remediation Rulebook v.3.1 "Enhanced Intelligence"

Este documento define la visión técnica y las leyes de inyección del Agente v.3.1. Es la Fuente de Verdad para garantizar la integridad estructural del monorepo.

---

## Versión 3.1.3 - Cambios Clave

### Nuevo: Profundidad de Detección Configurable
- El `FSProvider` ahora soporta el parámetro `max_depth` en `get_microservices(max_depth=2)` y `get_ms_path(ms_name, max_depth=2)`
- Permite adaptar la detección de microservicios a diferentes estructuras de monorepo
- Valor por defecto: 2 (compatible con versiones anteriores)

## Versión 3.1 - Cambios Clave

### Remoción del campo `microservice`
A partir de la v.3.1, las vulnerabilidades en `snyk_monorepo.json` son **globales**. El campo `microservice` ha sido eliminado del JSON. El control de qué microservicios procesar se realiza mediante:
- **Sin `--folders`**: Aplica a todos los microservicios detectados
- **Con `--folders`**: Aplica solo a los microservicios especificados

### Nuevas Capacidades
- **Prompt Caching**: Reducción de latencia en el ciclo ReAct
- **Clasificación de Vulnerabilidades**: Scoring CVSS-like automático
- **Memoria a Largo Plazo**: Aprendizaje persistente
- **Procesamiento Paralelo de Microservicios**: Hasta 4 workers simultáneos por CVE
- **Graceful Shutdown**: Cierre limpio ante interrupciones manuales (Ctrl+C)
- **Rollback Inteligente**: Reverse patches selectivos
- **Configuración Declarativa**: Soporte para `.remediation.yaml`
- **Thread-Local Context**: Seguridad en hilos para procesamiento paralelo

---

### 1. Procesamiento Paralelo de Microservicios (v.3.1.2+)

A partir de la v.3.1.2, el agente procesa **CVEs secuencialmente**, pero los **microservicios en paralelo** para maximizar la eficiencia:

**Patrón de Ejecución**:
```
CVE-1: MS-1, MS-2, MS-3, MS-4 (en paralelo, hasta 4 workers)
   ↓
CVE-2: MS-1, MS-2, MS-3, MS-4 (en paralelo)
   ↓
CVE-3: MS-1, MS-2, MS-3, MS-4 (en paralelo)
```

**Configuración**:
- `max_workers`: 4 microservicios simultáneos por CVE
- `timeout_per_ms`: 300 segundos (5 minutos) por microservicio
- `fail_fast`: false (continuar aunque haya errores)

**Thread-Safety**:
El contexto `current_ms` usa `threading.local()` para garantizar que cada hilo mantenga su propio estado, evitando condiciones de carrera en el procesamiento paralelo.

---

### 2. Graceful Shutdown y Manejo de Señales

El agente implementa cierre graceful ante interrupciones:

- **SIGINT (Ctrl+C)**: Captura la señal, termina procesos activos, ejecuta funciones de limpieza
- **SIGTERM**: Mismo comportamiento para terminación externa
- **Limpieza Automática**: Libera recursos, cierra conexiones y archivos al salir

**Recursos Liberados**:
- Procesos hijos activos (Gradle)
- Conexiones de archivos
- Referencias a objetos grandes (engine, cycle_controller)

---

### 3. Misión de Estabilidad Adaptativa

El objetivo es la remediación autónoma que se ajusta a las limitaciones del entorno. El agente tiene la soberanía de adaptar el JDK y la infraestructura de soporte para lograr el `BUILD SUCCESSFUL`.

---

### 4. Estándares de Entorno (JDKManager)

- **Selección de Java**: Se prohíbe el uso de versiones de Java que causen incompatibilidad con el ecosistema de Gradle. El agente descubrirá y priorizará JDK 21 o 17 sobre JDK 25 si el sistema lo requiere.
- **Acceso Modular**: Inyección obligatoria de `jvmargs` modularizados en `gradle.properties` para soportar Lombok y otras herramientas industriales.

---

### 5. Inteligencia de Remediación y Soberanía de Nomenclatura (v.3.1)

Para que el Cerebro Generativo mantenga el orden del monorepo, debe seguir estas leyes de ecosistemas:

- **Agrupación de Familias**: Los artefactos pertenecientes a ecosistemas conocidos DEBEN centralizarse bajo una única versión maestra para evitar conflictos.
    - `io.netty:*` -> `nettyCodecVersion`
    - `org.springframework:*` -> `springBootVersion`
    - `com.fasterxml.jackson.*:*` -> `jacksonCoreVersion`
- **Soberanía de Nomenclatura**: Si el artefacto no pertenece a una familia, la IA debe reconstruir el nombre de variable basado en su dominio (ej. `awsSdkVersion`).
- **Resolución de Conflictos**: Si dos CVEs de la misma familia requieren diferentes versiones seguras, la IA debe priorizar la actualización hacia la versión mayor/más reciente.

#### Clasificación Automática de Vulnerabilidades

El agente clasifica cada CVE usando el `VulnerabilityClassifier`:

| Campo | Descripción |
|-------|-------------|
| `base_score` | Score CVSS-like (0-10) basado en prioridad y keywords |
| `severity` | CRITICAL, HIGH, MEDIUM, LOW |
| `exploitability` | Facilidad de explotación (0-10) |
| `impact` | Impacto potencial (0-10) |
| `remediation_priority` | Prioridad calculada para remediación |

**Keywords de alto riesgo**: `remote code execution`, `rce`, `sql injection`, `authentication bypass`, `log4j`, etc.

---

### 6. Leyes de Mutación Estructural (Precision First)

El Agente opera bajo reglas físicas estrictas:

- **Estándar de Trinomio Autorizado**: La IA y el motor físico solo tienen permitido editar y leer lógicas de los archivos `build.gradle`, `main.gradle` y `dependencyMgmt.gradle`. Se prohíbe tocar infraestructuras abstractas o scripts ajenos.
- **Regla de Versión Única**: Se prohíbe terminantemente el uso de rangos (ej. `[1.0, 2.0)`). El agente debe elegir y forzar una versión estática única.
- **Blindaje por Interpolación**: Todas las versiones inyectadas en bloques `ext` DEBEN usar comillas dobles (`"..."`).
- **Regla de Prioridad 6.1**: Para la inyección de variables globales `ext`:
    1. Prioridad 1: `build.gradle`
    2. Prioridad 2: `main.gradle`
- **Standard de Metadatos (Auditoría y Zero-Watermark)**: El Motor Físico inyectará obligatoriamente la regla `details.because "Fix: CVE-XXXX"` al crear resoluciones transitivas. La infraestructura generada (ej. `dependencyMgmt.gradle`) se escribirá limpia y sin marcas de agua o comentarios del agente para salvaguardar la estética del repositorio.
- **Exclusiones de Seguridad**: El sistema tiene instrucciones inquebrantables de ignorar carpetas de infraestructura (`agent_ia`), de estrés (`stress`) o de certificación (`certification`), protegiendo el entorno operativo.
- **Ley de Profundidad de Detección (v.3.1.3+)**: El agente detecta microservicios buscando archivos `build.gradle` hasta un **nivel máximo configurable** (`max_depth`, por defecto: 2). No realiza búsquedas recursivas profundas para evitar falsos positivos en subcarpetas internas de microservicios (ej: `src/`, `bin/`, `acceptance_*`).
  - **Configuración**: El parámetro `max_depth` controla la profundidad de búsqueda
  - **Nivel 0**: `root_path` (directorio raíz del proyecto)
  - **Nivel 1**: Directorios hijos directos de `root_path`
  - **Nivel 2** (default): Subdirectorios de los directorios de Nivel 1 (ej: `backend_sales_products/ms_sales`)
  - **Nivel 3+**: Ignorado intencionalmente (subcarpetas internas de microservicios)
  - **Portabilidad**: El sistema es portable y se adapta a diferentes estructuras de monorepo sin depender de nombres específicos de microservicios
- **Ley de Exclusión Exacta (v.3.1.1+)**: El sistema utiliza **coincidencia exacta** (no por subcadena) para filtrar directorios excluidos durante el descubrimiento de microservicios. Esto permite que directorios con nombres como `ms_endpoint_adapter` sean detectados correctamente sin ser confundidos con palabras clave de exclusión (`api`). Las exclusiones aplican solo a nombres de carpeta exactos: `agent_ia`, `.git`, `.gradle`, `venv`, `__pycache__`, `out`, `build`, `stress`, `tests`, `certification`, `api`, `usecase`, `domain`, `infrastructure`, `src`, `bin`.
- **Ley de Profundidad Hexagonal (Depth Sort)**: Para proyectos multi-módulo (ej: Arquitectura Hexagonal), el Agente inferirá el archivo `build.gradle` Maestro contando la profundidad de su ruta (menor cantidad de separadores = Raíz). Las variables `ext` se inyectarán exclusivamente en esta Raíz, mientras que la sustitución por variables `"${version}"` se aplicará en cascada a todos los submódulos.
- **Inyección Seamless (Indent Sniffing)**: Si la arquitectura concentra sus variables dentro de un scope de compilación (ej. `buildscript { ext { } }`), el Agente es capaz de escanear la profundidad de su indentación y replicarla matemáticamente para las nuevas vulnerabilidades inyectadas, garantizando una alineación visual perfecta y erradicando el desfase de tabulaturas.
- **Exclusividad Estructural (Target Locking)**: El motor iterativo tiene prohibido inspeccionar archivos ajenos o complementarios (como `main.gradle`, `settings.gradle`) para crear o buscar variables globales. Estas responsabilidades están estrictamente delegadas a la Raíz designada (`build.gradle` principal).
- **Inyección Pura de Infraestructura**: Toda vinculación del Auto-Healer hacia los archivos locales se hará respetando implacablemente los bloques pre-armados del usuario (ej. insertando la vinculación como primera línea de `allprojects { }`) con Cero-Adulteración, erradicando repositorios paralelos u overrides indeseados.

---

### 7. Ciclo Adaptive ReAct (Self-Healing) con Mejoras v.3.1

1. **DESCUBRIMIENTO**: Identifica microservicios según `--folders` o todos los detectados.
2. **CLASIFICACIÓN**: Calcula score de severidad para cada CVE.
3. **ADAPTACIÓN**: Inyecta el entorno Java idóneo y vincula la infraestructura de `dependencyMgmt`.
4. **PENSAMIENTO**: Decide la versión basada en familia y linaje (con Prompt Caching).
5. **MUTACIÓN**: Aplica el parche siguiendo la Regla 6.1 y Comillas Dobles.
6. **VALIDACIÓN Y APRENDIZAJE**: Certifica con `gradle clean build`. Si falla, entra en bucle recursivo reinyectando errores de compilación para corrección automática (hasta 3 intentos).
7. **MEMORIZACIÓN**: Guarda el patrón de éxito en memoria a largo plazo.

---

### 8. Memoria a Largo Plazo

El agente mantiene aprendizaje persistente en `.agent_memory.json`:

**Estructura de Datos**:
```json
{
  "project_name": {
    "decisions": [...],
    "success_patterns": [...],
    "failure_patterns": [...]
  }
}
```

**Decisiones Guardadas**:
- `cve_id`: Identificador del CVE
- `library`: Librería afectada
- `microservice`: Microservicio procesado
- `attempted_action`: Acción intentada
- `success`: Éxito o fallo
- `timestamp`: Fecha de la decisión

**Patrones Aprendidos**:
- **Success Patterns**: Familias de librerías con estrategias exitosas
- **Failure Patterns**: Versiones problemáticas y tipos de error

---

### 9. Rollback Inteligente

El sistema mantiene historial de snapshots en `.rollback_history.json`:

**Capacidades**:
- Generación de **reverse patches** por archivo
- **Rollback selectivo**: Revertir solo archivos específicos
- **Historial persistente**: Metadatos de cada cambio
- **Detección de conflictos**: Si archivos cambiaron desde el snapshot

**Comandos de Gestión** (futuro):
```bash
# Listar snapshots disponibles
python3 remediation_agent.py --list-snapshots

# Preview de rollback
python3 remediation_agent.py --preview-rollback <snapshot_id>

# Aplicar rollback
python3 remediation_agent.py --rollback <snapshot_id>
```

---

### 10. Configuración Declarativa

El agente soporta configuración vía `.remediation.yaml`:

**Secciones Soportadas**:

| Sección | Descripción |
|---------|-------------|
| `project_name` | Nombre identificador del proyecto |
| `enabled` | Activa/desactiva el agente |
| `dry_run` | Modo simulación sin cambios reales |
| `jdk.preferred_versions` | Versiones de JDK preferidas |
| `rules` | Reglas personalizadas por patrón de librería |
| `microservices` | Overrides por microservicio |
| `global_exclusions` | CVEs a ignorar globalmente |

**Ejemplo de Reglas**:
```yaml
rules:
  - library_pattern: "io\.netty.*"
    variable_name: "nettyVersion"
    version_override: "4.1.132.Final"
    priority: "high"
    skip: false
```

---

### 11. Trazabilidad y Seguridad

- **Indentación**: Uso estricto de **4 espacios**.
- **Rollback**: Ante cualquier fallo de infraestructura o compilación tras los 3 intentos recursivos, el agente restaura el estado original del microservicio (`Zero-Risk`).
- **Logs Jerárquicos**: Visibilidad con 0, 4 y 8 espacios para facilitar la auditoría humana del Pensamiento de la IA.
- **Prompt Caching**: TTL de 24 horas para respuestas cacheadas.

---

### 12. Interfaz y Ejecución (CLI)

Para operar el Agente con la flexibilidad que exige la v.3.1:

| Operación | Comando |
| :--- | :--- |
| **Remediación Total** | `python3 remediation_agent.py` |
| **Filtrado por Microservicios** | `python3 remediation_agent.py --folders ms-auth ms-sales` |
| **Modo Debug** | `python3 remediation_agent.py --debug` |
| **Dry-Run (Preview)** | `python3 remediation_agent.py --dry-run` |
| **Ver Aprendizaje** | `python3 remediation_agent.py --learning-summary` |
| **Generar Config** | `python3 remediation_agent.py --generate-config` |
| **Certificación QA** | `python3 agent_ia/scripts/run_master_certification.py` |

**Salida de Ejecución**:
```
📊 RESUMEN DE EJECUCIÓN
======================================================================
  Total procesados: 3
  Exitosos: 3
  Fallidos: 0

⏱️  Tiempo total de ejecución: 3.8s
======================================================================
```

---

### 13. Arquitectura Consolidada (v.3.1.2)

A partir de la v.3.1.2, el agente opera con **12 módulos Python**:

| Módulo | Contenido | Rol |
| :--- | :--- | :--- |
| `remediation_agent.py` | `RemediationAgent`, `RollbackManager` | CLI Orchestrator |
| `agent_ia/core/__init__.py` | 11 clases principales | Motor Físico |
| `agent_ia/core/logging_utils.py` | `RemediationLogger`, `LogLevel` | Logging estructurado con contexto |
| `agent_ia/core/parallel_processor.py` | `ParallelMicroserviceProcessor`, `SequentialCVEProcessor` | Procesamiento paralelo |
| `agent_ia/core/shutdown_manager.py` | `ShutdownManager` | Graceful shutdown |
| `agent_ia/brain.py` | `GenerativeAgentV2`, `PromptCacheManager` | Cerebro ReAct |
| `agent_ia/vulnerability_classifier.py` | `VulnerabilityClassifier` | Clasificación de CVEs |
| `agent_ia/long_term_memory.py` | `LongTermMemory` | Memoria persistente |
| `agent_ia/smart_rollback.py` | `SmartRollbackManager` | Rollback inteligente |
| `agent_ia/event_bus.py` | `EventBus`, `EventDrivenRemediationAgent` | Event-Driven |
| `agent_ia/dry_run_mode.py` | `DryRunMode` | Preview de cambios |
| `agent_ia/config_manager.py` | `ConfigManager`, `ConfigValidator` | Configuración YAML |

**Archivos de Datos**:
- `agent_ia/data/cve/snyk_monorepo.json`: Vulnerabilidades globales
- `.agent_memory.json`: Memoria de aprendizaje (generado)
- `.prompt_cache.json`: Cache de prompts (generado)
- `.rollback_history.json`: Historial de snapshots (generado)

---

### 14. Resumen de Estados

El agente reporta los siguientes estados por CVE:

| Estado | Icono | Descripción |
|--------|-------|-------------|
| `FIXED` | ✅ | Cambios aplicados exitosamente |
| `ALREADY_FIXED` | ✓ | Ya estaba corregido, sin cambios |
| `ERROR` | ❌ | Fallo en la remediación |
| `NO_CHANGE` | ⚠️ | Éxito pero sin cambios detectados |

---

*Este manual es una extensión de la visión v.3.1 Enhanced, optimizado para la automatización total del flujo DevSecOps.*

*Última actualización: 2026-04-15 (v.3.1.3 - Profundidad de Detección Configurable + Procesamiento Paralelo + Graceful Shutdown)*
