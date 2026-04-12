import os
import re

class GenerativeAgentV2:
    """
    Orquestador de Inteligencia Generativa v.3.0.
    Implementa el marco ReAct y el Master System Prompt.
    """
    
    MASTER_PROMPT = """
    [ROL]: Arquitecto de Seguridad Autónomo Senior v.3.0.
    [OBJETIVO]: Remediación Generativa de CVEs.
    
    [LÓGICA ReAct]:
    1. PENSAMIENTO: Analizar riesgo y contexto local.
    2. ACCIÓN: Generar cambio exacto.
    3. EXPLICACIÓN: Justificar técnicamente.
    
    [ESTÁNDARES DE ARQUITECTURA]:
    1. TRINOMIO: Definición en 'ext' + Lógica en 'dependencyMgmt'.
    2. FAMILIAS: Agrupar por grupo (io.netty, etc).
    3. LINAJE (v.3.0): Analizar el origen de la dependencia para decidir si aplicar un 'force' centralizado o una variable puntual.

    FORMATO OBLIGATORIO:
    [PENSAMIENTO]: (Aquí el agente debe mencionar el linaje detectado).
    [ACCIÓN]: ...
    [EXPLICACIÓN]: ...
    """

    def __init__(self, model_path=None):
        self.model_path = model_path
        self.is_mock = model_path is None
        
    def generate_remediation(self, cve_data, local_context, previous_error=None):
        """
        Ejecuta la inferencia generativa.
        Si previous_error no es None, activa el Ciclo de Conciencia.
        """
        prompt = self._prepare_prompt(cve_data, local_context, previous_error)
        
        if self.is_mock:
            # Simulación de respuesta del modelo de 3-bits
            return self._mock_llm_response(cve_data, previous_error)
        else:
            # Aquí iría la integración real con llama-cpp-python
            return "[ERROR]: Motor llama-cpp no inicializado por falta de pesos."

    def parse_react_response(self, response):
        """ Extrae los bloques de Pensamiento, Acción y Explicación del modelo. """
        result = {
            "thought": self._extract_block(response, "PENSAMIENTO"),
            "action": self._extract_block(response, "ACCIÓN"),
            "explanation": self._extract_block(response, "EXPLICACIÓN")
        }
        return result

    def _prepare_prompt(self, cve, context, error):
        error_context = f"\n[ERROR PREVIO]: {error}\n[INSTRUCCIÓN]: El parche anterior falló. Debes analizar el error y generar un nuevo parche corregido." if error else ""
        return f"{self.MASTER_PROMPT}\n\n[CVE]: {cve}\n[CONTEXTO LOCAL]: {context}{error_context}"

    def _extract_block(self, text, block_name):
        pattern = rf"\[{block_name}\]:\s*(.*?)(?=\[|$)"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else f"No se encontró el bloque {block_name}"

    def _mock_llm_response(self, cve_data, previous_error):
        """ Simula la respuesta experta del modelo v.3.0. """
        if previous_error:
            return """
            [PENSAMIENTO]: El error indica un conflicto con la versión de Netty. Debo ajustar la versión de la familia nettyCodecVersion a una más estable compatible con el entorno actual.
            [ACCIÓN]: nettyCodecVersion = '4.1.118.Final'
            [EXPLICACIÓN]: Se ajusta la versión de Netty a una versión de parche anterior para resolver el conflicto de ejecución detectado en los tests.
            """
        else:
            library_name = cve_data.get('library', '')
            vuln_id = cve_data.get('cve') or cve_data.get('id', 'N/A')
            # v.3.0: Lógica de simulación dinámica por familia (Priorizando consolidación manual pero permitiendo autonomía)
            if "netty" in library_name:
                target_var = "nettyCodecVersion"
            elif "jackson" in library_name:
                target_var = "jacksonCoreVersion"
            elif "org.springframework" in library_name:
                target_var = "springBootVersion"
            elif "snakeyaml" in library_name:
                target_var = "snakeyamlVersion"
            elif "log4j" in library_name:
                target_var = "log4jCoreVersion"
            else:
                # Simulación de RAZONAMIENTO AUTÓNOMO para librerías desconocidas
                parts = library_name.split(':')[-1].split('-')
                target_var = parts[0] + "".join(p.capitalize() for p in parts[1:]) + "Version"
            
            # v.3.0: Generar un razonamiento dinámico basado en la decisión tomada
            reasoning = f"Analizando {vuln_id}. La librería detectada es {library_name}."
            if "netty" in library_name:
                reasoning += " Al pertenecer al ecosistema Netty, lo asocio a la familia 'nettyCodecVersion'."
            elif "jackson" in library_name:
                reasoning += " Como artefacto de Jackson, aplico la política de familia 'jacksonCoreVersion'."
            elif "spring" in library_name:
                reasoning += " Es un componente de Spring. Centralizo la versión en 'springBootVersion' siguiendo el estándar de arquitectura."
            elif "log4j" in library_name:
                reasoning += " Crítico de Log4j detectado. Aplico remediación en la familia 'log4jCoreVersion'."
            else:
                reasoning += f" No pertenece a un grupo común conocido. Genero variable específica '{target_var}'."

            # v.3.0: Asegurar VERSION ÚNICA (Respecting Master Rulebook)
            safe_ver_list = str(cve_data.get('safe_version', 'LATEST')).split(',')
            final_safe_v = safe_ver_list[0].strip()

            return f"""
            [PENSAMIENTO]: {reasoning}
            [ACCIÓN]: {target_var} = '{final_safe_v}'
            [EXPLICACIÓN]: Se aplica el parche de versión única para mitigar la vulnerabilidad, centralizando la definición en la variable de familia '{target_var}' para mantener la integridad del monorepo.
            """

if __name__ == "__main__":
    # Prueba rápida de parsing
    agent = GenerativeAgentV2()
    resp = agent._mock_llm_response({"cve": "CVE-2026", "library": "netty", "safe_version": "4.2.1"}, None)
    parsed = agent.parse_react_response(resp)
    print(f"Pensamiento IA: {parsed['thought']}")
    print(f"Acción IA: {parsed['action']}")
