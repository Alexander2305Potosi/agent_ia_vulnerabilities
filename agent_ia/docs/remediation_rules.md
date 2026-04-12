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

### 3. Leyes de Mutación Estructural (Precision First)
El Agente opera bajo reglas físicas estrictas:
- **Blindaje por Interpolación**: Todas las versiones inyectadas en bloques `ext` DEBEN usar comillas dobles (`"..."`). Se prohíben comillas simples para asegurar la correcta resolución de variables en Groovy.
- **Regla de Prioridad 6.1 (Archivo Raíz)**: Para la inyección de variables globales `ext`:
    1.  Prioridad 1: `build.gradle`
    2.  Prioridad 2: `main.gradle`
- **Consolidación de Reglas**: Las resoluciones transitivas se centralizan en `dependencyMgmt.gradle`, evitando la dispersión de reglas fuera de este archivo de infraestructura.

---

### 4. Ciclo Adaptive ReAct
1. **DESCUBRIMIENTO**: Identifica solo microservicios compilables (excluye `api`, `usecase`, `domain`).
2. **ADAPTACIÓN**: Inyecta el entorno Java idóneo.
3. **PENSAMIENTO**: Decide la versión basada en familia y linaje.
4. **MUTACIÓN**: Aplica el parche siguiendo la Regla 6.1 y Comillas Dobles.
5. **VALIDACIÓN**: Certifica con `gradle clean build`.

---

### 5. Trazabilidad y Seguridad
- **Indentación**: Uso estricto de **4 espacios**.
- **Rollback**: Ante cualquier fallo de infraestructura o compilación tras 3 intentos, el agente restaura el estado original (`Zero-Risk`).
- **Logs**: Jerarquía visible con 0, 4 y 8 espacios para facilitar la auditoría humana del Pensamiento de la IA.

---
*Este manual es una extensión de la visión v.3.0 Adaptive, optimizado para la automatización total del flujo DevSecOps.*
