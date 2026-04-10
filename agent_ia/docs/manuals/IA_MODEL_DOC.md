# Teoría de la IA v2.0: Remediación Generativa (ReAct)

Este documento detalla la lógica de pensamiento que convierte al agente en un sistema autónomo de "Grado Laboratorio".

## 1. El Marco ReAct (Pensamiento ➔ Acción ➔ Explicación)
Para compensar las limitaciones de los modelos cuantizados de 3 bits, el agente v2.0 utiliza el marco lógico **ReAct**:

1.  **[PENSAMIENTO]**: El modelo analiza el CVE, identifica la librería y deduce el riesgo. Razona sobre posibles conflictos antes de proponer nada.
2.  **[ACCIÓN]**: Genera la corregida línea de código, comando o configuración exacta de Gradle/Maven.
3.  **[EXPLICACIÓN]**: Justifica técnicamente por qué ese cambio resuelve la vulnerabilidad sin romper el sistema.

## 2. El Prompt Maestro de Sistema (Nucleo de v2.0)
Este es el conjunto de instrucciones que rigen el comportamiento del modelo de 3 bits:

> **Rol:** Eres el Arquitecto de Seguridad Autónomo Senior (v2.0). 
> **Objetivo:** Recibir un reporte de CVE y los archivos locales. Interpretar el riesgo y generar la corrección exacta en disco.

## 3. El Ciclo de Conciencia (Self-Healing)
A diferencia de la v1.5 que era puramente predictiva, la v2.0 genera una **hipótesis de solución**, la aplica físicamente y, si falla, **aprende del error**. El agente re-inyecta el stacktrace de error al modelo generativo para una segunda pasada analítica, cerrando el gap entre la inteligencia y la validación real.

## 4. Inferencia Local Garantizada
El motor v2.0 está optimizado para pesos GGUF, permitiendo ejecutar inteligencia de nivel senior en máquinas locales sin GPU dedicada, delegando las tareas de edición física al motor `GradleMutator` bajo la supervisión del razonamiento IA.

---
*Capa de Inteligencia Autónoma de Seguridad v2.0. Inferencia Local.*
