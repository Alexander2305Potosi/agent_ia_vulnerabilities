# Manual del Operador: Agente IA v2.0 (Generativo)

Este manual detalla las operaciones para el Agente de Remediación Generativo Versión 2.0.

## 1. Flujo de Operación v2.0
El agente ha pasado de un enfoque de "Tablas de Decisión" a un **Cerebro Autónomo**. El flujo operativo es el siguiente:

1.  **Escaneo de Snyk**: El agente lee el reporte `snyk_monorepo.json`.
2.  **Inferencia ReAct**: El modelo GGUF razona:
    - *Pensamiento*: "¿Qué tan crítico es? ¿Hay conflictos?"
    - *Acción*: "Actualizar versión X a Y".
3.  **Remediación Física**: El agente invoca al `GradleMutator` y **escribe físicamente** el cambio.
    - **Restricción v2.0**: Solo tiene permitido modificar `build.gradle`, `main.gradle` y `dependencyMgmt.gradle` del microservicio. Cualquier otro archivo será ignorado por seguridad.
4.  **Validación & Aprendizaje**:
    - Se ejecuta `gradle clean test`.
    - Si falla, el error se re-inyecta al modelo para una nueva propuesta (Ciclo de Conciencia).

## 2. Configuración de Modelos
El agente busca el cerebro generativo en:
`agent_ia/models/remediation_v2_3bits.gguf`

- **Soporte**: Modelos GGUF (cuantizados IQ3_M para mayor velocidad en hardware local).
- **RAM**: Se recomiendan 4.5 GB libres.

## 3. Comandos Útiles
Para iniciar una sesión de remediación generativa completa:
```bash
python3 remediation_agent.py
```

Para realizar una limpieza de archivos temporales:
```bash
python3 agent_ia/cleanup_repo.py
```

---
*Manual V2.0 - Seguridad Autónoma por Diseño.*

## 4. Garantía de Seguridad: 100% Local y Privado
Para operar con total tranquilidad en entornos corporativos:

- **Nada sale de casa**: El agente lee tus archivos solo para repararlos. NUNCA envía información, código o reportes a internet.
- **Funciona sin conexión**: No necesitas internet para que la IA tome decisiones. El "cerebro" reside en tu propio disco duro.
- **Privacidad Total**: No usamos servicios externos (nube). Todo el procesamiento ocurre dentro de los límites de tu propia computadora.
