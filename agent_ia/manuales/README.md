# Agente de Remediación SCA (Impulsado por IA)

Sistema de remediación de seguridad autónomo para monorepos basados en Gradle. Implementa parches de seguridad de forma segura mediante la gestión de dependencias tanto directas como transitivas, utilizando un **modelo de IA personalizado** para la selección inteligente de estrategias.

## 🚀 Características Clave

- **Selección de Estrategia Impulsada por IA**: Reemplaza las heurísticas fijas con un **Clasificador Random Forest** que predice la ruta de remediación óptima con alta confianza.
- **Descubrimiento Inteligente de Microservicios**: Identifica recursivamente los proyectos afectados y mapea su contexto estructural (profundidad, complejidad, etc.) al modelo de IA.
- **Sustitución Activa de Código**: Reemplaza automáticamente las versiones fijas en `build.gradle` con referencias a variables seguras una vez creadas.
- **Motor de Mutación Quirúrgico**: La lógica de regex reforzada garantiza una sintaxis de Gradle válida y evita colisiones de versiones.
- **Automatización del Ciclo de Vida de Git**: Creación automática de ramas con marca de tiempo y commits para soluciones validadas exitosamente.
- **Validación a Prueba de Fallos**: Registro en tiempo real de los ciclos de construcción `clean test` con reversión (rollback) automática en caso de fallo.
- **Listo para la Empresa**: Soporte completo multiplataforma (Mac, Linux, Windows) para flujos de trabajo de DevSecOps empresariales.

# Agente de Remediación SCA (AI-Driven)

Este agente autónomo utiliza Inteligencia Artificial para remediar vulnerabilidades de seguridad en monorepos de Gradle de forma local y segura.

## 1. Estructura de Carpetas

Para mantener la raíz limpia, el proyecto se organiza de la siguiente manera:

*   **`remediation_agent.py`**: El ejecutor principal.
*   **`agent_ia/`**: Cerebro y recursos del agente.
    *   `manuales/`: Guías de uso y detalles del modelo.
    *   `librerias/`: Motor de mutación, modelo `.joblib` y scripts internos.
    *   `cve/`: Reportes de vulnerabilidades (JSON).

## 2. Inicio Rápido

1.  **Instalar dependencias**:
    ```bash
    pip install -r agent_ia/librerias/requirements.txt
    ```
2.  **Ejecutar el Agente**:
    ```bash
    python3 remediation_agent.py
    ```

El agente buscará automáticamente el reporte en `agent_ia/cve/` y cargará el modelo de IA desde `agent_ia/librerias/`.

## 3. Características Principales
*   **IA RandomForest**: Decide la mejor estrategia de parcheo (Centralizada vs Local).
*   **Motor de Mutación Robusto**: Modifica archivos Gradle sin romper la sintaxis.
*   **Validación Local**: Ejecuta `gradle clean test` antes de confirmar cualquier cambio.
*   **100% Local**: No envía información a internet.
oma para DevSecOps Modernos.*
