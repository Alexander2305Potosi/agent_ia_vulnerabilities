# 🛡️ Agente de Seguridad SCA: v2.0 (Edición Generativa)

Bienvenido a la Versión 2.0 del Agente de Remediación para el proyecto `agent_ia_vulnerabilities`. Este sistema ha evolucionado de un modelo predictivo tradicional a un ecosistema de **Inteligencia Artificial Generativa Autónoma**.

## 🚀 ¿Qué hay de nuevo en la v2.0?

A diferencia de las versiones anteriores, la v2.0 utiliza un **Cerebro Generativo (LLM)** de 3 bits que permite al agente razonar antes de actuar.

### 🧠 El Marco ReAct (Reason + Act)
El agente sigue un ciclo lógico de pensamiento crítico:
1.  **PENSAMIENTO**: Analiza la vulnerabilidad (CVE) y el contexto del microservicio.
2.  **ACCIÓN**: Define el cambio exacto de código necesario.
3.  **EXPLICACIÓN**: Justifica técnicamente por qué la remediación es segura.

## 🛡️ Garantía de Privacidad: Tu código NO sale de tu equipo
> [!IMPORTANT]
> **Es un sistema 100% privado y desconectado.** 
> Para tu tranquilidad absoluta:
> - **Sin Internet**: El agente no necesita conexión para funcionar. Puedes usarlo en modo avión.
> - **Tu código se queda en casa**: Ni una sola línea de tu código fuente o configuración se envía a la nube o a servidores externos.
> - **Cerebro Local**: La Inteligencia Artificial vive en un archivo dentro de tu computadora, no en internet.

### 🔄 Ciclo de Conciencia (Self-Healing)
El agente posee una capacidad de **autocuración**. Si una remediación física falla en la validación de Gradle, el agente captura el error, lo analiza y genera una nueva propuesta corregida automáticamente.

## 🛠️ Arquitectura Técnica
- **Motor de Inferencia**: `llama-cpp-python` (Optimizado para modelos GGUF de 3 bits).
- **Inferencia 100% Local**: Privacidad absoluta, sin envío de datos a la nube.
- **Mutación Quirúrgica**: Integración directa con `GradleMutator` para modificar archivos `.gradle` de forma segura.

## 📋 Requisitos Rápidos
- Python 3.10+
- `pip install -r agent_ia/requirements.txt`
- Modelo GGUF en `agent_ia/models/` (Recomendado: 3.5GB RAM).

## 🖱️ Ejecución
Ejecuta el agente principal con un solo comando:
```bash
python3 remediation_agent.py
```

---
*Protección Generativa para Microservicios. Inteligencia v2.0 Local y Privada.*
