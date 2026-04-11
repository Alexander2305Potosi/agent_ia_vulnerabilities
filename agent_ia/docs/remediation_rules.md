# Master Remediation Rulebook v2.0
## Centralized Standard for AI Vulnerability Mitigation

Este documento consolida la lógica, los estándares y los patrones de remediación utilizados por el Agente de IA. Sirve como un **Punto de Retorno** y referencia técnica para garantizar la consistencia en el manejo de vulnerabilidades en el monorepo Gradle.

---

### 1. Filosofía de Remediación
El agente utiliza una estrategia de **Mutación Estructural y Desacoplada**:
- **Definición de Versiones**: Se centralizan en el bloque `ext` de los archivos `build.gradle`.
- **Inyección de Reglas**: Se desacoplan en archivos `dependencyMgmt.gradle` para evitar contaminar la lógica de construcción principal.
- **Aislamiento**: Cada microservicio tiene su propio control de versiones, pero se fomenta el uso de variables consistentes.

---

### 2. Registro de Familias de Dependencias
Para optimizar las reglas, el agente agrupa artefactos en "Familias". Cuando se detecta un artefacto de estas familias, se aplica una regla de grupo (Group Rule) en lugar de una individual.

| Familia (Group ID) | Variable de Versión | Descripción |
| :--- | :--- | :--- |
| `io.netty` | `nettyCodecVersion` | Maneja todos los codecs y handlers de Netty de forma sincronizada. |
| `org.springframework` | `springBootVersion` | Alinea el framework base de Spring Boot y Webflux. |
| `com.fasterxml.jackson` | `jacksonCoreVersion` | Garantiza consistencia en la serialización JSON. |
| `org.apache.logging.log4j` | `log4jVersion` | (Reserva) Manejo crítico de vulnerabilidades de logging. |

---

### 3. Estándar de Metadatos (Auditoría)
El campo `because` en Gradle debe seguir estrictamente un formato legible por humanos y máquinas para facilitar auditorías de seguridad.

- **Prefijo**: `Fix: `
- **Formato de IDs**: Lista de identificadores únicos (CVE o GHSA) separados por comas.
- **Whitelist Regex**: `CVE-\d{4}-\d+` \| `GHSA-[a-z0-9-]+`
- **Ejemplo**: `details.because "Fix: CVE-2026-33870, CVE-2026-33871"`
- **Política de Limpieza**: El agente mantiene un registro de auditoría enfocado únicamente en la **última solución aplicada**. No se debe concatenar información de vulnerabilidades anteriores para evitar archivos de configuración sobrecargados e ilegibles.

---

### 4. Estándar de Implementación Técnica
Para evitar la corrupción de archivos que plagó versiones anteriores (v1.x), cualquier mutador que actúe sobre Gradle **DEBE** seguir estos requisitos funcionales:

- **Balanced Brace Tracking**: No se permiten expresiones regulares simples para modificar bloques de configuración (como `ext { ... }` o `resolutionStrategy { ... }`). Se debe usar un rastreador de llaves balanceadas `{}` para identificar el inicio y fin exacto de cada bloque, garantizando cierres limpios.
- **Sustitución Activa de Literales**: Cuando se inyecta una variable de familia, el agente debe escanear todos los archivos `build.gradle` y reemplazar dependencias directas en formato literal (`"group:artifact:version"`) por el formato dinámico (`"group:artifact:${variableVersion}"`).
- **Purga de Redundancia**: Si se inyecta una variable "paraguas" (ej: `nettyCodecVersion`), se deben eliminar variables específicas y redundantes del bloque `ext` (ej: `nettyHandlerVersion`) para mantener el código limpio.
- **Inteligencia de Rama (Multi-Branch Support)**: El agente de mutación **NO DEBE** asumir que la primera versión de una lista de seguridad es la correcta. Debe realizar una coincidencia de rama basada en `Major.Minor` (ej: si el proyecto usa 4.2.9, debe buscar el parche en la línea 4.2.x y no saltar a la 4.1.x o 5.x automáticamente).
- **Weighted Token-Based Matching**: Para evitar colisiones en la detección de variables (ej: diferenciar entre `spring-boot` y `spring-web`), el mutador debe utilizar un motor de coincidencia ponderada basado en tokens. Se asignan pesos a las coincidencias exactas para garantizar que se elija la variable con mayor relevancia semántica.
- **Compatibilidad de Runtime (JUnit 5)**: En proyectos Spring Boot 3 / Gradle 8+, el mutador debe asegurar la presencia de `testRuntimeOnly 'org.junit.platform:junit-platform-launcher'` en el bloque de dependencias. Sin este componente, el proceso de validación real podría fallar prematuramente.

---

### 5. Patrón de Inyección estructural (Gradle)
El agente utiliza el **Balanced Brace Parser** para inyectar o actualizar el bloque de infraestructura global en el orquestador (`main.gradle` o `build.gradle`).

```gradle
allprojects {
    apply from: "${rootDir}/dependencyMgmt.gradle"
}
```

- **Gestión de Repositorios**: La configuración de `repositories { ... }` es responsabilidad del usuario. El agente NO forzará la inyección de `mavenCentral()` para permitir configuraciones privadas o personalizadas.
- **Idempotencia Garantizada**: Antes de inyectar, el agente debe verificar si el vínculo ya existe para evitar duplicaciones innecesarias del código.

---

### 6. Procedimiento de Auto-Healing (Recuperación)
Si la infraestructura se corrompe o se pierden funcionalidades:
1. **Validación de Infraestructura Global**: Asegurarse de que el orquestador contenga el bloque `allprojects` con el vínculo `apply from: "${rootDir}/dependencyMgmt.gradle"`. La resolución de dependencias dependerá de los repositorios configurados manualmente por el usuario.
2. **Re-Sincronización de Variables**: Si una regla en `dependencyMgmt.gradle` referencia una variable inexistente en `ext`, el agente debe identificar la carpeta del microservicio y re-crear la variable en el `build.gradle` más cercano.
3. **Consistencia de Rama**: En caso de re-sincronización manual, verificar que la versión elegida coincida con la rama del proyecto (4.1.x vs 4.2.x).
4. **Rollback de Emergencia**: Ante cualquier `BUILD FAILED`, se debe restaurar el estado de los archivos binarios (respaldo de texto plano) previo a la mutación.

---

### 7. Resumen de Familias (Referencia Rápida)
- `io.netty` -> `nettyCodecVersion`
- `org.springframework` -> `springBootVersion`
- `com.fasterxml.jackson` -> `jacksonCoreVersion`
- `org.apache.logging.log4j` -> `log4jVersion`

---

### 8. Guía para Ajustes Futuros (Prompting)
Si en el futuro deseas que una IA (como Antigravity u otra) modifique estas reglas o añada nuevas funcionalidades, puedes usar este archivo como contexto base con el siguiente comando de prompt:

> **PROMPT SUGERIDO**:
> *"Analiza el archivo `remediation_rules.md` v2.0 adjunto. Basándote en sus estándares técnicos y familias actuales, por favor [AÑADE/MODIFICA] lo siguiente: [TU REQUERIMIENTO, ej: 'Añade una nueva familia para com.google.guava']. 
> Asegúrate de mantener el estándar de metadatos 'Fix: CVE' y respeta el requisito del Balanced Brace Parser."*

Esta sección garantiza que cualquier extensión futura del agente sea consistente con la arquitectura de "Cero Corrupción" establecida en esta versión.
