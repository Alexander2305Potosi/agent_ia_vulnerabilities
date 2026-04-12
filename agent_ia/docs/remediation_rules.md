# Master Remediation Rulebook v.3.0 "Zero-Risk"
## Manual Maestro de Operaciones e Inteligencia del Agente IA

Este documento define la misión, los estándares técnicos y los protocolos de ejecución del Agente de Remediación. Sirve como la **Fuente de Verdad** para la toma de decisiones autónomas en el monorepo.

---

### 1. Misión y Propósito
El objetivo fundamental del Agente es la **Estabilización y Aseguramiento Autónomo** del software mediante la remediación de vulnerabilidades (CVEs) con "Cero Corrupción" de archivos. El Agente no solo aplica parches, sino que garantiza que cada cambio mantenga la integridad operativa del sistema mediante validaciones rigurosas.

---

### 2. Estándares de Infraestructura (LTS)
Para garantizar la estabilidad en entornos monorepo de alto rendimiento (Gradle 8/9, Spring Boot 3), se establecen los siguientes requisitos innegociables:

- **Entorno JVM (Java 21 LTS)**: Todos los procesos de construcción deben ejecutarse bajo JDK 21. Se prohíbe el uso de versiones superiores para evitar incompatibilidades críticas.
- **Acceso Modular**: Es obligatorio configurar `jvmargs` con `--add-opens` y `--add-exports` en `gradle.properties` para procesadores de anotaciones (Lombok).
- **Validación de Tests (JUnit Platform)**: Cada microservicio debe incluir `testRuntimeOnly 'org.junit.platform:junit-platform-launcher'`.
- **Configuración Persistente**: La propiedad `org.gradle.java.home` debe estar sincronizada en todo el monorepo.

---

### 3. Inteligencia de Remediación (Precision First)
El Agente utiliza una estrategia de **Mutación de Alta Precisión** para evitar inyectar código malformado:

- **Regla de Versión Única**: Se prohíbe el uso de rangos. El Agente elige una versión segura compatible con la rama del proyecto.
- **Inteligencia Adaptativa (Regla 4)**: Si la versión del reporte falla, el Agente tiene facultad de **Override** para aplicar la versión sugerida por su Cerebro Generativo tras el fallo.
- **Estándar de Indentación**: Todas las inyecciones en bloques `ext` deben seguir el estándar industrial de **4 espacios** para alineación perfecta.
- **Standard de Metadatos (Auditoría)**: Uso estricto de `because "Fix: CVE-XXXX-XXXXX"` sin acumulación de historial.
- **Exclusiones de Seguridad**: El Agente nunca debe intervenir carpetas de infraestructura (`agent_ia`), de estrés (`stress`) o de certificación (`certification`).

---

### 4. Ciclo de Conciencia (Self-Healing)
El Agente opera bajo un ciclo cerrado de retroalimentación recursiva:
1. **PENSAMIENTO**: Análisis de la vulnerabilidad y el contexto del microservicio.
2. **ACCIÓN**: Generación y aplicación física del parche estructural.
3. **VALIDACIÓN FÍSICA**: Ejecución de `gradle clean compileJava test` para certificar la veracidad del cambio.
4. **AUTO-HEAL**: Si falta la infraestructura de seguridad o el vínculo en `main.gradle`, el Agente la reconstruye antes de la validación.
5. **APRENDIZAJE**: Si el build falla, el error se re-inyecta para un override inteligente de versión (Hasta 3 intentos).

---

### 5. Trazabilidad y Gestión de Git (Success or Nothing)
La persistencia de los cambios en el repositorio es **Dinámica y Bajo Demanda**:

- **Activación por Comando**: La integración con Git NO es estática. Se activa exclusivamente mediante el parámetro `--commit` (o `-c`) en la línea de comandos.
- **Branching Condicional**: Al finalizar la sesión, se creará una nueva rama (ej: `security/remediation_TIMESTAMP`) **SÓLO SI** se logró al menos una remediación exitosa y validada.
- **Commit Consolidado**: Se realiza un único commit global al final del proceso con un mensaje profesional que detalla microservicios y CVEs.

---

### 6. Guía de Ejecución Rápida (CLI)
Para operar el Agente de forma eficiente y portable, utiliza los siguientes flags:

| Operación | Comando Sugerido |
| :--- | :--- |
| **Remediación Total** | `python3 remediation_agent.py --commit` |
| **Filtrado por Microservicios** | `python3 remediation_agent.py --folders ms-auth ms-sales --commit` |
| **Ruta Gradle Personalizada** | `python3 remediation_agent.py --gradle-path /usr/local/bin/gradle --commit` |
| **Modo Debug** | `python3 remediation_agent.py --debug --folders ms-clients` |

---
*Este manual es una extensión de la visión v.3.0, optimizado para la automatización total del flujo DevSecOps.*
