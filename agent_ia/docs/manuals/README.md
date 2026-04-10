# Documentación Técnica: Agente IA v2.0 (Generativo)

Este directorio contiene los recursos técnicos y manuales del Agente de Remediación v2.0.

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
