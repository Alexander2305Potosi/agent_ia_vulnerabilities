#Bienvenido al repositorio de documentación técnica del Agente v2.0. Estos manuales detallan la arquitectura, operación y estándares del sistema de remediación autónoma.

## 📚 Índice de Documentación
1.  **[Remediation Rules (Maestro)](../remediation_rules.md)**: El Rulebook definitivo (v2.0) con estándares de Java 21 y Git.
2.  **[Manual del Operador](MANUAL.md)**: Guía de ejecución, flujos ReAct y resolución de problemas de validación.
3.  **[IA Model Theory](IA_MODEL_DOC.md)**: Documentación sobre el Cerebro Generativo de 3 bits, ICL y la política de versión única.

## 🚀 Versión 2.0: Estabilización & Autodescubrimiento
Esta versión introduce:
- **Validación Robusta**: Integración nativa con Gradle 9 y Java 21 LTS.
- **Git Success Intelligence**: Automatización total de ramas y commits profesionales.
- **Detección Portable**: Lógica avanzada para encontrar herramientas de construcción en cualquier entorno.

## 📁 Estructura del Módulo `agent_ia`

- **`core/`**: Lógica fundamental del sistema.
    - `mutator.py`: Motor de modificación quirúrgica de archivos Gradle.
    - `consciousness.py`: Controlador del ciclo de autocuración (Re-aprendizaje).
    - `utils.py`: Herramientas de limpieza y mantenimiento.
- **`engine/`**: Inteligencia Artificial.
    - `generative.py`: Motor de inferencia local GGUF con marco ReAct.
- **`data/`**: Información de entrada.
    - `cve/`: Reportes de vulnerabilidades en formato JSON.
- **`docs/`**: Documentación y activos.
    - `manuals/`: Guías de usuario y guías técnicas.
    - `assets/`: Diagramas de arquitectura e infografías.
- **`models/`**: Pesos de los modelos de IA (GGUF).

## 🚀 Inicio Rápido

1.  Asegúrate de tener el modelo en `agent_ia/models/`.
2.  Ejecuta desde la raíz:
    ```bash
    python3 remediation_agent.py
    ```

---
*Arquitectura Limpia v2.0 - Seguridad y Privacidad Local.*
