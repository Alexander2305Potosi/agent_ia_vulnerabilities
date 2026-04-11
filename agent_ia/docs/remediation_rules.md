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

---

### 4. Patrón de Inyección estructural (Gradle)
El agente utiliza un **Parser de Llaves Balanceadas** para inyectar o actualizar el siguiente bloque en `dependencyMgmt.gradle`:

```gradle
configurations.all {
    resolutionStrategy.eachDependency { DependencyResolveDetails details ->
        // Inyección de Regla de Familia
        if (details.requested.group == 'io.netty') {
            details.useVersion "${nettyCodecVersion}"
            details.because "Fix: CVE-XXXX-XXXX"
        }
        // Inject rules here
    }
}
```

---

### 5. Políticas de Validación y Resiliencia
- **Atomicidad**: Antes de cada cambio, se respaldan los archivos `build.gradle`, `main.gradle` y `dependencyMgmt.gradle`.
- **Detección de Fallos**: Si `gradle clean test` retorna un código de salida distinto de 0, se ejecuta un **Rollback Total** inmediato.
- **Modo Estricto**: El agente no asume éxito si no puede verificar la construcción (Blindness Check).

---

### 6. Punto de Retorno (Recovery)
Si las reglas en el código se pierden o se corrompen:
1. Re-analizar este archivo para identificar las variables (`ext`) que deben existir.
2. Re-inyectar los bloques `apply from: 'dependencyMgmt.gradle'` en los archivos `main.gradle`.
3. Verificar la existencia de las variables de familia en el `ext` del `build.gradle` raíz o del microservicio.

> [!IMPORTANT]
> **Modificación Manual**: Si se ajustan estas reglas manualmente, el agente intentará respetarlas en el próximo ciclo mediante su lógica de **Acumulación de Razones** (v2.1+).
