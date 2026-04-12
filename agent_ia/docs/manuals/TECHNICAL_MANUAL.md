# Manual Técnico y de Operación: Agente IA v.30

Este documento constituye la fuente única de verdad para entender la teoría, las facultades autónomas y la operación práctica del Agente de Remediación Generativa.

---

## 1. Fundamentos de la IA Autónoma

A diferencia de la automatización tradicional, este sistema opera como un **Agente Inteligente** con capacidades cognitivas aplicadas a la ciberseguridad.

### 🧠 Facultades del Agente
*   **Razonamiento ReAct (Cerebro)**: El Agente no ejecuta comandos ciegos. Sigue un ciclo cognitivo de **Pensamiento -> Acción -> Explicación**, permitiéndole entender el contexto semántico de un microservicio antes de proponer un cambio.
*   **Ciclo de Autocorrección (Self-Healing)**: Si una validación falla (ej. error de compilación), el Agente captura el log de error, lo interpreta como una nueva lección y genera una propuesta corregida de forma recursiva.
*   **In-Context Learning (ICL)**: El sistema no requiere reglas estáticas para cada librería. Deduce la solución óptima vinculando dinámicamente el Master Rulebook, los datos del CVE y la estructura real de los archivos Gradle.
*   **Orquestación Atómica ("Success or Nothing")**: El Agente coordina backups preventivos, mutaciones multivariantes y validación de salud en una sola operación atómica. Si el éxito no está garantizado, el sistema realiza un rollback completo.

---

## 2. Arquitectura de Pensamiento (v.30)

### De Predicción a Razonamiento
El agente ha abandonado los modelos estadísticos rígidos por un marco deductivo en tiempo real:
- **Soberanía de Nomenclatura**: La IA tiene prioridad para definir estándares de variables (ej. `familyVersion`) si detecta una necesidad arquitectónica.
- **Single Version Policy**: El Cerebro Generativo garantiza la integridad estructural eligiendo estrictamente una única versión segura compatible con la rama del proyecto.

---

## 3. Guía de Operación (Operator Manual)

### Flujo de Ejecución Profundo
1.  **Descubrimiento**: Escaneo del monorepo y detección de microservicios afectados.
2.  **Inferencia ReAct**: Razonamiento sobre criticidad y conflictos potenciales.
3.  **Remediación Física**: Invocación al `GradleMutator` para la escritura quirúrgica del cambio.
4.  **Validación & Aprendizaje**: Ejecución de `gradle clean test` y retroalimentación de errores.
5.  **Persistencia & Trazabilidad**: Creación de rama de seguridad y commit consolidado (solo en caso de éxito).

---

## 4. Resolución de Problemas e Infraestructura

### Requisitos Obligatorios
Para garantizar la estabilidad del sistema, el entorno debe cumplir con:
- **JDK 21 LTS**: Indispensable para estabilidad en Gradle 9 / Spring Boot 3.
- **JUnit Platform Launcher**: Requerido en todos los microservicios para detección de tests.

### Solución de Fallos Comunes
- **Gradle no encontrado**: El agente busca en rutas estándar (`/usr/local/bin`, etc.). Si falla, se debe usar el flag `--gradle-path`.
- **Fallo en Test**: Verifica logs de puerto ocupado o acceso a red. El Agente solo persiste cambios que pasan exitosamente el build.
- **Conflicto de Familias**: La IA prioriza siempre la versión más reciente que mantenga la compatibilidad con el Rulebook Maestro.

---
*Manual Maestro Unificado v.30.*
