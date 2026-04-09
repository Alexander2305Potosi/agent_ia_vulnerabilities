# Manual de Usuario: Agente de Remediación Inteligente (AI-Ready)

Este agente es un sistema de DevSecOps autónomo que utiliza **Inteligencia Artificial** para corregir vulnerabilidades en monorepos de microservicios.

## 1. Arquitectur---
*Capa de Inteligencia Autónoma para Seguridad de Grado Laboratorio v1.5.*
pts tradicionales, este agente utiliza un **Modelo de Machine Learning** para tomar decisiones:

1.  **Modelo**: Clasificador Random Forest (Entrenado con `scikit-learn`).
2.  **Inferencia**: El agente analiza variables de entorno (profundidad del proyecto, complejidad, severidad) y predice la mejor estrategia (`DIRECT` vs `TRANSITIVE`).
3.  **Entrenamiento**: Puedes mejorar la inteligencia del agente ejecutando:
    ```bash
# Manual del Operador: Agente de Remediación IA

Este manual guía al usuario en la operación y mantenimiento del agente de seguridad autónomo.

## 1. Instalación y Reemplazos
El agente está diseñado para ser portable. Para desplegar en un nuevo equipo:

1.  **Copiar el proyecto**: Asegúrate de que la carpeta `agent_ia/` y el archivo `remediation_agent.py` estén en el mismo directorio.
2.  **Instalar librerías**:
    ```bash
    pip install -r agent_ia/librerias/requirements.txt
    ```

## 2. Ejecución
El agente es inteligente y busca sus propios insumos:

```bash
# Ejecución Estándar (Recomendado)
python3 remediation_agent.py
```

*   **Entrada**: Busca el reporte en `agent_ia/cve/snyk_monorepo.json`.
*   **Modelo**: Carga el cerebro desde `agent_ia/librerias/remediation_model.joblib`.

## 3. Configuración y Mantenimiento
*   **Ajustes**: Dentro de `remediation_agent.py` puedes activar `GIT_COMMIT_ENABLED = True` para commits automáticos.
*   **Re-entrenamiento (Actualizar IA)**:
    Si la estructura de tu monorepo cambia drásticamente, es recomendable actualizar el "cerebro" del agente:
    ```bash
    python3 agent_ia/librerias/model_trainer.py
    ```

## 4. Portabilidad Multiplataforma
Si mueves el agente a un equipo **Windows**:
1.  Usa `python` en lugar de `python3`.
2.  Asegúrate de que `gradle` esté en el PATH del sistema para que el agente pueda validar los arreglos.

## 5. Resolución de Problemas (Troubleshooting)
- **Fallo de Validación**: Si el agente dice "Validation Failed", revisará el log de Gradle. Si el test falla, el agente hará un **Rollback automático** para no dejar el código roto.
- **Modelo no encontrado**: Si borras la carpeta `agent_ia/librerias/`, el agente pasará a modo "Seguro" (Sin IA) y usará reglas básicas para intentar salvar el día.

---
*Manual de Operación Segura v1.5*

*   **Low Confidence (Baja Confianza)**: Si la IA muestra una confianza baja, puede deberse a un patrón de proyecto no visto durante el entrenamiento. Se recomienda re-entrenar el modelo con nuevos datos en `model_trainer.py`.
*   **Missing Model**: Si el archivo `.joblib` se pierde, el agente funcionará en modo "Seguro" (determinista).

---
