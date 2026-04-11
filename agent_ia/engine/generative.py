import os
import re

class GenerativeAgentV2:
    """
    Orquestador de Inteligencia Generativa v2.0.
    Implementa el marco ReAct y el Master System Prompt.
    """
    
    MASTER_PROMPT = """
    [ROL]: Arquitecto de Seguridad Autónomo Senior v2.0.
    [OBJETIVO]: Remediación Generativa de CVEs.
    
    [LÓGICA ReAct]:
    1. PENSAMIENTO: Analizar riesgo y contexto local.
    2. ACCIÓN: Generar cambio exacto.
    3. EXPLICACIÓN: Justificar técnicamente.
    
    [ESTÁNDARES DE ARQUITECTURA]:
    1. TRINOMIO: Definición en 'ext' + Lógica en 'dependencyMgmt'.
    2. FAMILIAS: Agrupar por grupo (io.netty, etc).

    FORMATO OBLIGATORIO:
    [PENSAMIENTO]: ...
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
        """ Simula la respuesta experta del modelo v2.0. """
        if previous_error:
            return """
            [PENSAMIENTO]: El error indica que la versión 4.1.132 no es compatible con el plugin de Spring Boot actual en este MS. Debo bajar a la 4.1.120 o actualizar el plugin.
            [ACCIÓN]: springBootVersion = '3.5.7'
            [EXPLICACIÓN]: Al actualizar el Framework Parent, se resuelven las dependencias transitivas de Netty de forma nativa sin conflictos.
            """
        else:
            library_name = cve_data.get('library', '')
            vuln_id = cve_data.get('cve') or cve_data.get('id', 'N/A')
            # v2.0: Lógica de simulación dinámica por familia (Priorizando consolidación manual pero permitiendo autonomía)
            if "netty" in library_name:
                target_var = "nettyCodecVersion"
            elif "jackson" in library_name:
                target_var = "jacksonCoreVersion"
            elif "spring" in library_name:
                target_var = "springWebfluxVersion"
            elif "snakeyaml" in library_name:
                target_var = "snakeyamlVersion"
            else:
                # Simulación de RAZONAMIENTO AUTÓNOMO para librerías desconocidas
                # Extrae el nombre del artefacto y lo convierte a camelCase
                parts = library_name.split(':')[-1].split('-')
                target_var = parts[0] + "".join(p.capitalize() for p in parts[1:]) + "Version"
            
            # v2.0: Generar un razonamiento dinámico basado en la decisión tomada
            reasoning = f"Analizando {vuln_id}. La librería detectada es {library_name}."
            if "netty" in library_name:
                reasoning += " Al pertenecer al ecosistema Netty, razono que lo más seguro y limpio es agruparla en la familia 'nettyCodecVersion' para mantener la coherencia de versiones en el monorepo."
            elif "jackson" in library_name:
                reasoning += " Detecto que es un artefacto de Jackson. Aplico la política de familia 'jacksonCoreVersion' para evitar conflictos entre módulos de serialización."
            elif "spring" in library_name:
                reasoning += " Es un componente de Spring. Centralizo la versión en 'springWebfluxVersion' siguiendo el estándar de arquitectura del proyecto."
            else:
                reasoning += f" No pertenece a un grupo común conocido. Aplico el Estándar de Trinomio generando una variable ultra-específica '{target_var}' para mitigar el riesgo sin afectar otras dependencias."

            return f"""
            [PENSAMIENTO]: {reasoning}
            [ACCIÓN]: {target_var} = '{cve_data.get('safe_version')}'
            [EXPLICACIÓN]: Se aplica el parche directo en el bloque ext del microservicio para mitigar el riesgo de seguridad centralizando la versión mediante el Estándar de Trinomio.
            """

if __name__ == "__main__":
    # Prueba rápida de parsing
    agent = GenerativeAgentV2()
    resp = agent._mock_llm_response({"cve": "CVE-2026", "library": "netty", "safe_version": "4.2.1"}, None)
    parsed = agent.parse_react_response(resp)
    print(f"Pensamiento IA: {parsed['thought']}")
    print(f"Acción IA: {parsed['action']}")
