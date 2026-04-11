# Teoría de la IA v2.0: Remediación Generativa (ReAct)

Este documento detalla la lógica de pensamiento que convierte al agente en un sistema autónomo de "Grado Laboratorio".

## 1. De Predicción a Razonamiento
En la v2.0, el agente ha abandonado los modelos estadísticos rígidos. El "entrenamiento" ahora se basa en el marco **ReAct** (Reason + Act).

### In-Context Learning (ICL)
El agente no necesita ser re-entrenado matemáticamente para cada librería. Al proporcionarle:
1.  **Leyes Arquitectónicas** (Prompt Maestro).
2.  **Contexto del Proyecto** (Estructura de archivos Gradle).
3.  **Datos del CVE** (Reporte de Snyk).

El modelo **deduce** la solución óptima mediante lógica deductiva en tiempo real.

## 2. Ciclo de Conciencia: El Autodidacta
El agente implementa un bucle de retroalimentación:
- **Error como Contexto**: Si una remediación falla, el log de error de Gradle se convierte en la nueva "lección" para el modelo.
- **Evolución Recursiva**: El modelo ajusta su propuesta basándose en el fallo anterior hasta alcanzar el éxito o agotar los intentos.

### Soberanía de Nomenclatura & Precisión (v2.0)
- **Nomenclatura**: Si la IA detecta que debe usarse un estándar específico (ej. `awsSdkVersion`), el sistema sobrescribirá los nombres de variables tradicionales.
- **Single Version Policy**: El Cerebro Generativo tiene prohibido emitir listas o rangos. Debe elegir **una única versión final** compatible con la rama del proyecto para garantizar la integridad estructural de Gradle.

## 4. Trazabilidad & Auditoría (v2.0)
Cada decisión tomada por la IA se traduce en un rastro de auditoría profesional:
- **Metadatos en Configuración**: Inyección de `details.because "Fix: CVE-XXXX"`.
- **Git Intelligence**: Generación automática de resúmenes de impacto (`fix: global remediation...`) agrupando éxitos por servicio.
Este es el conjunto de instrucciones que rigen el comportamiento del modelo de 3 bits:

> **Rol:** Eres el Arquitecto de Seguridad Autónomo Senior (v2.0). 
> **Objetivo:** Recibir un reporte de CVE y los archivos locales. Interpretar el riesgo y generar la corrección exacta en disco.

## 5. Inferencia Local Garantizada
El motor v2.0 está optimizado para pesos GGUF, permitiendo ejecutar inteligencia de nivel senior en máquinas locales sin GPU dedicada, delegando las tareas de edición física al motor `GradleMutator` bajo la supervisión del razonamiento IA.

---
*Capa de Inteligencia Autónoma de Seguridad v2.0. Inferencia Local.*
