# Documentación del Modelo de IA (Explicación Sencilla)

Este documento explica cómo el agente "piensa" y toma decisiones inteligentes para arreglar vulnerabilidades.

## 1. ¿Cómo funciona la Inteligencia del Agente?
En lugar de usar reglas fijas, el agente utiliza un **Bosque de Decisión Estratégico** (Random Forest):

Este motor procesa la vulnerabilidad a través de **100 Árboles de Decisión de Seguridad**. Cada "árbol" evalúa una combinación diferente de factores:
1.  Uno puede priorizar la **jerarquía del proyecto** (si es un microservicio núcleo o periférico).
2.  Otro puede enfocarse en la **naturaleza de la deuda técnica** (si es una dependencia directa o heredada).
3.  El veredicto final es un **consenso matemático** de estos 100 árboles. Esto permite que el agente maneje excepciones que una regla manual no podría prever.

## 2. ¿Qué factores analiza el Agente? (Ejemplos Reales)
Para tomar una decisión, el modelo mira 5 puntos clave (Features):
*   **Origen de la librería**: ¿Viene directamente o es una transitiva (como `netty-codec` que viene dentro de Spring)? (`is_transitive`).
*   **Posición en el Proyecto**: ¿El microservicio está en la raíz o es un módulo profundo como `backend/services/ms-auth`? (`project_depth`).
*   **Herramientas disponibles**: ¿El microservicio ya usa un archivo central de versiones (`dependencyMgmt.gradle`)? (`has_dep_mgmt`).
*   **Gravedad del CVE**: ¿Es un riesgo CRITICAL (como un RCE) o LOW? (`severity`).
*   **Complejidad del Código**: ¿Cuántas dependencias tiene el microservicio (Ej: 15 vs 80)? (`ms_complexity`).

## 3. Escenarios de Decisión (Casos del Mundo Real)
Aquí tienes ejemplos de cómo votaría el **Consejo de Expertos**:

*   **Caso A (Estrategia TRANSITIVA)**: Una vulnerabilidad en `netty-handler` (transitiva) detectada en el microservicio `ms-sales` que ya tiene gestión centralizada. 
    *   *Decisión*: **TRANSITIVE** (Confianza 100%). Se centraliza la versión para que afecte a todos los servicios que usen Netty.
    *   *Acción*: El agente edita `dependencyMgmt.gradle`.

*   **Caso B (Estrategia DIRECTA)**: Una vulnerabilidad en `jackson-core` detectada en un microservicio de prueba en la raíz que no tiene gestión centralizada.
    *   *Decisión*: **DIRECT** (Confianza 98%). Es más seguro y rápido aplicar el parche localmente sin afectar el resto del monorepo.
    *   *Acción*: El agente edita el `build.gradle` del servicio.

## 4. Entrenamiento (Cómo "estudia" el Agente)
El proceso de entrenamiento es una **simulación de casos reales** que convierte al agente en experto. El script `agent_ia/librerias/model_trainer.py` genera 2,000 escenarios de prueba para "enseñar" al modelo.

**Ejemplo de cómo el modelo aprende un patrón:**
1.  **El Profesor (Script)**: Crea 1,000 casos donde una vulnerabilidad en `netty-codec` es **Transitiva**, está en un servicio **muy profundo** en el repo y ya existe un archivo de gestión de dependencias. Para todos esos casos, el profesor le dice: *"La decisión correcta es TRANSITIVE"*.
2.  **El Estudiante (IA)**: El algoritmo Random Forest encuentra la relación matemática entre esos factores. No guarda el ejemplo exacto, sino que aprende la **ley general**: *"Si es profundo + transitivo = centralizar"*.
3.  **El Examen (Producción)**: Cuando el agente se encuentra con una vulnerabilidad real que nunca ha visto, aplica esa "ley general" para decidir con total confianza.

**Para actualizar el cerebro de la IA:**
```bash
python3 agent_ia/librerias/model_trainer.py
```

## 5. Privacidad y Funcionamiento 100% Local
Una de las mayores ventajas de este agente es que es **totalmente privado**:

*   **Sin Nube (No Cloud)**: El agente no envía tu código, tus reportes de Snyk, ni tus rutas de archivos a ninguna API externa o servidor en internet.
*   **Inferencia en CPU**: Cuando el agente toma una decisión ("Strategy Prediction"), el cálculo matemático se realiza íntegramente en tu procesador local usando la librería `scikit-learn`.
*   **Modelo Portátil**: El archivo `remediation_model.joblib` contiene todo el conocimiento en unos pocos kilobytes. Puedes llevarte la carpeta `agent_ia/` a un equipo sin conexión a internet y el agente seguirá siendo igual de inteligente.
*   **Entrenamiento Privado**: El script `model_trainer.py` también funciona sin internet, permitiéndote "educar" al agente en entornos de máxima seguridad (Air-gapped).

## 6. ¿Por qué usar IA en lugar de reglas simples?
Las reglas simples se rompen fácilmente cuando el proyecto cambia. La IA es más **flexible**: puede ver patrones complejos y se adapta a monorepos dinámicos, garantizando que el parche se aplique siempre en el lugar con menor riesgo de romper el build.

---
*Capa de Inteligencia Autónoma para Seguridad de Grado Laboratorio v1.5.*
