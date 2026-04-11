# Manual del Operador: Agente de Remediación v2.0

Este manual describe el funcionamiento del Agente de Remediación SCA en su versión Generativa v2.0.

## 1. Flujo de Ejecución Profundo
El agente opera en un ciclo de 4 fases basado en el marco ReAct:

1.  **Descubrimiento**: Escanea el monorepo y detecta el microservicio afectado.
2.  **Inferencia ReAct**: El modelo GGUF razona:
    - *Pensamiento*: "¿Qué tan crítico es? ¿Hay conflictos?"
    - *Acción*: "Actualizar versión X a Y".
3.  **Remediación Física**: El agente invoca al `GradleMutator` y **escribe físicamente** el cambio.
    - **Recursividad Selectiva v2.0**: El agente explora todas las subcarpetas del microservicio buscando el "Trinomio Autorizado" (`build.gradle`, `main.gradle`, `dependencyMgmt.gradle`). Ignora cualquier otro tipo de archivo por seguridad.
4.  **Validación & Aprendizaje**:
    - Se ejecuta `gradle clean test`.
    - Si falla, el error se re-inyecta al modelo para una nueva propuesta (Ciclo de Conciencia).
5.  **Persistencia & Trazabilidad (v2.0)**:
    *   Si hay éxitos: Crea rama de seguridad y realiza commit consolidado.
    *   Si no hay cambios validados: Finaliza sin alterar el historial de Git.

## 2. Configuración de Seguridad (Privacidad)
El agente ha sido diseñado para entornos de alta seguridad:
- **No requiere Internet**: El motor de IA (v2.0_3bits.gguf) se ejecuta localmente.
- **Sin Exfiltración**: No se envían logs, reportes ni código fuente a servidores externos.

## 3. Resolución de Problemas
- **Gradle no encontrado**: El agente buscará en rutas comunes (`/usr/local/bin`, `/opt/homebrew`, etc.). Si falla, usa `--gradle-path`.
- **Fallo en Test**: Verifica logs. Asegúrate de que el puerto no esté ocupado y de que la base de datos de pruebas (si aplica) sea accesible.
- **Conflicto de Familias**: Si dos librerías de la misma familia requieren versiones distintas, la IA elegirá la versión única más reciente que sea compatible con la rama del proyecto (v2.0 Rulebook).

## 4. Estándar de Infraestructura Obligatorio
Para que la validación sea exitosa, el entorno debe cumplir con:
- **JDK 21 LTS**: Indispensable para estabilidad en Gradle 9 / Spring Boot 3.
- **JUnit Platform Launcher**: Requerido en todos los microservicios.
*Manual de Operación Local v2.0.*
