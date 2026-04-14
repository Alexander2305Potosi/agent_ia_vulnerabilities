# Master Remediation Rulebook v.3.0 "Adaptive Zero-Risk"

Este documento define la visión técnica y las leyes de inyección del Agente v.3.0. Es la Fuente de Verdad para garantizar la integridad estructural del monorepo.

---

### 1. Misión de Estabilidad Adaptativa
El objetivo es la remediación autónoma que se ajusta a las limitaciones del entorno. El agente tiene la soberanía de adaptar el JDK y la infraestructura de soporte para lograr el `BUILD SUCCESSFUL`.

---

### 2. Estándares de Entorno (JDKManager)
- **Selección de Java**: Se prohíbe el uso de versiones de Java que causen incompatibilidad con el ecosistema de Gradle. El agente descubrirá y priorizará JDK 21 o 17 sobre JDK 25 si el sistema lo requiere.
- **Acceso Modular**: Inyección obligatoria de `jvmargs` modularizados en `gradle.properties` para soportar Lombok y otras herramientas industriales.

---

### 3. Inteligencia de Remediación y Soberanía de Nomenclatura (v.3.0)
Para que el Cerebro Generativo mantenga el orden del monorepo, debe seguir estas leyes de ecosistemas:
- **Agrupación de Familias**: Los artefactos pertenecientes a ecosistemas conocidos DEBEN centralizarse bajo una única versión maestra para evitar conflictos.
    - `io.netty:*` -> `nettyCodecVersion`
    - `org.springframework:*` -> `springBootVersion`
    - `com.fasterxml.jackson.*:*` -> `jacksonCoreVersion`
- **Soberanía de Nomenclatura**: Si el artefacto no pertenece a una familia, la IA debe reconstruir el nombre de variable basado en su dominio (ej. `awsSdkVersion`).
- **Resolución de Conflictos**: Si dos CVEs de la misma familia requieren diferentes versiones seguras, la IA debe priorizar la actualización hacia la versión mayor/más reciente.

---

### 4. Leyes de Mutación Estructural (Precision First)
El Agente opera bajo reglas físicas estrictas:
- **Estándar de Trinomio Autorizado**: La IA y el motor físico solo tienen permitido editar y leer lógicas de los archivos `build.gradle`, `main.gradle` y `dependencyMgmt.gradle`. Se prohíbe tocar infraestructuras abstractas o scripts ajenos.
- **Regla de Versión Única**: Se prohíbe terminantemente el uso de rangos (ej. `[1.0, 2.0)`). El agente debe elegir y forzar una versión estática única.
- **Blindaje por Interpolación**: Todas las versiones inyectadas en bloques `ext` DEBEN usar comillas dobles (`"..."`).
- **Regla de Prioridad 6.1**: Para la inyección de variables globales `ext`:
    1.  Prioridad 1: `build.gradle`
    2.  Prioridad 2: `main.gradle`
- **Standard de Metadatos (Auditoría y Zero-Watermark)**: El Motor Físico inyectará obligatoriamente la regla `details.because "Fix: CVE-XXXX"` al crear resoluciones transitivas. La infraestructura generada (ej. `dependencyMgmt.gradle`) se escribirá limpia y sin marcas de agua o comentarios del agente para salvaguardar la estética del repositorio.
- **Exclusiones de Seguridad**: El sistema tiene instrucciones inquebrantables de ignorar carpetas de infraestructura (`agent_ia`), de estrés (`stress`) o de certificación (`certification`), protegiendo el entorno operativo.
- **Ley de Profundidad Hexagonal (Depth Sort)**: Para proyectos multi-módulo (ej: Arquitectura Hexagonal), el Agente inferirá el archivo `build.gradle` Maestro contando la profundidad de su ruta (menor cantidad de separadores = Raíz). Las variables `ext` se inyectarán exclusivamente en esta Raíz, mientras que la sustitución por variables `"${version}"` se aplicará en cascada a todos los submódulos.
- **Inyección Seamless (Indent Sniffing)**: Si la arquitectura concentra sus variables dentro de un scope de compilación (ej. `buildscript { ext { } }`), el Agente es capaz de escanear la profundidad de su indentación y replicarla matemáticamente para las nuevas vulnerabilidades inyectadas, garantizando una alineación visual perfecta y erradicando el desfase de tabulaturas.
- **Exclusividad Estructural (Target Locking)**: El motor iterativo tiene prohibido inspeccionar archivos ajenos o complementarios (como `main.gradle`, `settings.gradle`) para crear o buscar variables globales. Estas responsabilidades están estrictamente delegadas a la Raíz designada (`build.gradle` principal).
- **Inyección Pura de Infraestructura**: Toda vinculación del Auto-Healer hacia los archivos locales se hará respetando implacablemente los bloques pre-armados del usuario (ej. insertando la vinculación como primera línea de `allprojects { }`) con Cero-Adulteración, erradicando repositorios paralelos u overrides indeseados.
---

### 5. Ciclo Adaptive ReAct (Self-Healing)
1. **DESCUBRIMIENTO**: Identifica solo microservicios compilables y aplica exclusiones hexagonales (ignora `api`, `usecase`, `domain`).
2. **ADAPTACIÓN**: Inyecta el entorno Java idóneo y vincula la infraestructura de `dependencyMgmt`.
3. **PENSAMIENTO**: Decide la versión basada en familia y linaje.
4. **MUTACIÓN**: Aplica el parche siguiendo la Regla 6.1 y Comillas Dobles.
5. **VALIDACIÓN Y APRENDIZAJE**: Certifica con `gradle clean build`. Si falla, entra en bucle recursivo reinyectando errores de compilación para corrección automática (hasta 3 intentos).

---

### 6. Trazabilidad y Seguridad
- **Indentación**: Uso estricto de **4 espacios**.
- **Rollback**: Ante cualquier fallo de infraestructura o compilación tras los 3 intentos recursivos, el agente restaura el estado original del microservicio (`Zero-Risk`).
- **Logs Jerárquicos**: Visibilidad con 0, 4 y 8 espacios para facilitar la auditoría humana del Pensamiento de la IA.

---



### 7. Interfaz y Ejecución (CLI)
Para operar el Agente con la flexibilidad que exige la v.3.0, el Panel de Control soporta banderas dinámicas:

| Operación | Comando Sugerido |
| :--- | :--- |
| **Remediación Total Segura** | `python3 remediation_agent.py` |
| **Filtrado por Sistemas** | `python3 remediation_agent.py --folders ms-auth ms-sales` |
| **Modo Debug (Trace/Auditoría)**| `python3 remediation_agent.py --debug` |
| **Simulación de Falla** | Sin dependencia externa, rollback asegurado. |

---
*Este manual es una extensión de la visión v.3.0 Adaptive, optimizado para la automatización total del flujo DevSecOps.*

---

### 8. Arquitectura Consolidada (Refactorización v.3.0.12)

A partir de la refactorización ejecutada en la sesión de estabilización final, el agente opera con **4 módulos Python** en lugar de los 14 archivos dispersos originales.

| Módulo | Contenido | Rol |
| :--- | :--- | :--- |
| `remediation_agent.py` | `RemediationAgent`, `RollbackManager` | CLI Orchestrator |
| `agent_ia/core/__init__.py` | `Vulnerability`, `JDKManager`, `FSProvider`, `GradleProvider`, `GitProvider`, `DependencyGraph`, `InfrastructureHealer`, `VariableManager`, `RuleInjector`, `GradleMutator`, `CycleOfConsciousness` | Motor Físico Completo |
| `agent_ia/brain.py` | `GenerativeAgentV2` | Cerebro ReAct LLM |
| `agent_ia/scripts/run_master_certification.py` | 7 escenarios de certificación | Suite QA |

**Archivos eliminados en esta refactorización:**
- `agent_ia/core/mutator.py`, `consciousness.py`, `providers.py`, `graph.py`, `utils.py`, `diag_graph.py`, `test_parser.py`
- `agent_ia/engine/generative.py`
- `agent_ia/models/vulnerability.py`
- `debug_mutator.py`, `test_debug.py` (scripts temporales)
