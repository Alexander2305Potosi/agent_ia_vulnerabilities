# Master Remediation Rulebook v2.0
## Manual Maestro de Operaciones e Inteligencia del Agente IA

Este documento define la misión, los estándares técnicos y los protocolos de ejecución del Agente de Remediación. Sirve como la **Fuente de Verdad** para la toma de decisiones autónomas en el monorepo.

---

### 1. Misión y Propósito
El objetivo fundamental del Agente es la **Estabilización y Aseguramiento Autónomo** del software mediante la remediación de vulnerabilidades (CVEs) con "Cero Corrupción" de archivos. El Agente no solo aplica parches, sino que garantiza que cada cambio mantenga la integridad operativa del sistema mediante validaciones rigurosas.

---

### 2. Estándares de Infraestructura (LTS)
Para garantizar la estabilidad en entornos monorepo de alto rendimiento (Gradle 8/9, Spring Boot 3), se establecen los siguientes requisitos innegociables:

- **Entorno JVM (Java 21 LTS)**: Todos los procesos de construcción deben ejecutarse bajo JDK 21. Se prohíbe el uso de JDK 25 o superiores para evitar incompatibilidades críticas con procesadores de anotaciones (Lombok).
- **Validación de Tests (JUnit Platform)**: Cada microservicio debe incluir `testRuntimeOnly 'org.junit.platform:junit-platform-launcher'` para asegurar que el motor de pruebas de JUnit 5 sea detectable por Gradle.
- **Configuración Persistente**: La propiedad `org.gradle.java.home` en `gradle.properties` debe apuntar siempre al SDK de Java 21 definido por el administrador.

---

### 3. Inteligencia de Remediación (Precision First)
El Agente utiliza una estrategia de **Mutación de Alta Precisión** para evitar inyectar código malformado:

- **Regla de Versión Única**: Queda terminantemente prohibido el uso de listas, comas o rangos de versiones en las variables de Gradle. El Agente **DEBE elegir estrictamente UNA (1) versión segura** que coincida con la rama del proyecto (Ej: `'4.1.132.Final'`).
- **Standard de Metadatos (Auditoría)**: Cada cambio debe documentarse en el campo `because` de Gradle siguiendo el patrón: `Fix: CVE-XXXX-XXXXX`. Este campo solo debe contener los IDs de seguridad activos, sin historial acumulado.
- **Weighted Token-Based Matching**: El sistema de detección de variables utiliza pesos semánticos para diferenciar entre componentes de una misma familia (ej: `netty-codec` vs `netty-handler`) y evitar colisiones de nombres.

---

### 4. Ciclo de Conciencia (Self-Healing)
El Agente opera bajo un ciclo cerrado de retroalimentación recursiva:
1. **PENSAMIENTO**: Análisis de la vulnerabilidad y el contexto del microservicio.
2. **ACCIÓN**: Generación y aplicación física del parche estructural.
3. **VALIDACIÓN**: Ejecución de `gradle clean test`.
4. **APRENDIZAJE**: Si la validación falla, el error se re-inyecta a la memoria del Agente para generar un nuevo parche corregido (Hasta 3 intentos).

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
*Este manual es una extensión de la visión v2.0, optimizado para la automatización total del flujo DevSecOps.*
