import re
import hashlib
import json
import os
from datetime import datetime, timedelta


class PromptCacheManager:
    """Gestor de caché para prompts del cerebro ReAct."""

    CACHE_FILE = os.path.join(os.path.dirname(__file__), ".prompt_cache.json")
    CACHE_TTL_HOURS = 24

    def __init__(self):
        self.cache = self._load_cache()
        self._clean_expired()

    def _load_cache(self) -> dict:
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self):
        with open(self.CACHE_FILE, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def _clean_expired(self):
        now = datetime.now()
        expired = []
        for key, entry in self.cache.items():
            cached_at = datetime.fromisoformat(entry.get('timestamp', '2000-01-01'))
            if now - cached_at > timedelta(hours=self.CACHE_TTL_HOURS):
                expired.append(key)
        for key in expired:
            del self.cache[key]
        if expired:
            self._save_cache()

    def _hash(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get(self, prompt: str) -> dict:
        key = self._hash(prompt)
        entry = self.cache.get(key)
        if entry:
            return entry.get('response')
        return None

    def set(self, prompt: str, response: dict):
        key = self._hash(prompt)
        self.cache[key] = {
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'prompt_snippet': prompt[:100] + '...' if len(prompt) > 100 else prompt
        }
        self._save_cache()


class GenerativeAgentV2:
    """
    Cerebro Generativo v.3.0 — Implementa el marco ReAct y el Master System Prompt.
    Opera en modo Mock (reglas hard-coded) o puede integrarse con llama-cpp-python.
    """

    MASTER_PROMPT = """
    [ROL]: Arquitecto de Seguridad Autónomo Senior v.3.0.
    [OBJETIVO]: Remediación Generativa de CVEs.

    [LÓGICA ReAct]:
    1. PENSAMIENTO: Analizar riesgo, ecosistema de la librería y contexto local.
    2. ACCIÓN: Generar cambio exacto.
    3. EXPLICACIÓN: Justificar técnicamente la nomenclatura elegida.

    [ESTÁNDARES DE ARQUITECTURA MAESTRA (INQUEBRANTABLES)]:
    1. TRINOMIO AUTORIZADO: Tienes prohibido editar fuera de build.gradle, main.gradle y dependencyMgmt.gradle.
    2. SOBERANÍA DE NOMENCLATURA: Las variables en 'ext' deben tener sufijo 'Version' y usar CamelCase exacto del dominio.
    3. ECOSISTEMAS Y FAMILIAS:
       - io.netty          → nettyCodecVersion
       - org.springframework → springBootVersion
       - com.fasterxml.jackson → jacksonCoreVersion
    4. VERSIÓN ÚNICA: Se prohíbe el uso de rangos. Siempre versión estática.

    FORMATO OBLIGATORIO:
    [PENSAMIENTO]: (Familia, Linaje y Nomenclatura elegida)
    [ACCIÓN]: [variableName] = '[version]'
    [EXPLICACIÓN]: ...
    """

    # Mapa de familias conocidas para el mock ReAct
    _FAMILY_MAP = {
        "netty":          "nettyCodecVersion",
        "jackson":        "jacksonCoreVersion",
        "org.springframework": "springBootVersion",
        "snakeyaml":      "snakeyamlVersion",
        "log4j":          "log4jCoreVersion",
    }

    _FAMILY_REASONING = {
        "netty":          "Al pertenecer al ecosistema Netty, lo asocio a la familia 'nettyCodecVersion'.",
        "jackson":        "Como artefacto de Jackson, aplico la política de familia 'jacksonCoreVersion'.",
        "org.springframework": "Es un componente de Spring. Centralizo la versión en 'springBootVersion' siguiendo el estándar de arquitectura.",
        "log4j":          "Crítico de Log4j detectado. Aplico remediación en la familia 'log4jCoreVersion'.",
    }

    def __init__(self, model_path=None):
        self.model_path = model_path
        self.is_mock = model_path is None
        self.cache = PromptCacheManager()

    def generate_remediation(self, cve_data: dict, local_context: str, previous_error=None) -> str:
        """Ejecuta la inferencia generativa (mock o real) con caching."""
        # Cache key basado en CVE + contexto + error previo (sin intento actual)
        cache_prompt = f"{json.dumps(cve_data, sort_keys=True)}|{local_context}|{previous_error}"

        # Solo cachear si no hay error previo (errores pueden requerir ajustes)
        if not previous_error:
            cached = self.cache.get(cache_prompt)
            if cached:
                print(f"        [CACHE HIT] Usando respuesta cacheada")
                return cached.get('response_text', '')

        if self.is_mock:
            response = self._mock_llm_response(cve_data, previous_error)
            if not previous_error:
                self.cache.set(cache_prompt, {'response_text': response})
            return response

        # Integración futura con llama-cpp-python
        return "[ERROR]: Motor llama-cpp no inicializado por falta de pesos."

    def parse_react_response(self, response: str) -> dict:
        """Extrae los bloques Pensamiento, Acción y Explicación del output del modelo."""
        return {
            "thought":      self._extract_block(response, "PENSAMIENTO"),
            "action":       self._extract_block(response, "ACCIÓN"),
            "explanation":  self._extract_block(response, "EXPLICACIÓN"),
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _prepare_prompt(self, cve: dict, context: str, error) -> str:
        error_ctx = (
            f"\n[ERROR PREVIO]: {error}\n[INSTRUCCIÓN]: El parche anterior falló. "
            "Analiza el error y genera un nuevo parche corregido."
            if error else ""
        )
        return f"{self.MASTER_PROMPT}\n\n[CVE]: {cve}\n[CONTEXTO LOCAL]: {context}{error_ctx}"

    def _extract_block(self, text: str, block_name: str) -> str:
        pattern = rf"\[{block_name}\]:\s*(.*?)(?=\[|$)"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else f"No se encontró el bloque {block_name}"

    def _mock_llm_response(self, cve_data: dict, previous_error) -> str:
        """Simula la respuesta experta del modelo v.3.0."""
        if previous_error:
            return (
                "\n            [PENSAMIENTO]: El error indica un conflicto con la versión de Netty. "
                "Debo ajustar la versión de la familia nettyCodecVersion a una más estable compatible con el entorno actual.\n"
                "            [ACCIÓN]: nettyCodecVersion = '4.1.118.Final'\n"
                "            [EXPLICACIÓN]: Se ajusta la versión de Netty a una versión de parche anterior "
                "para resolver el conflicto de ejecución detectado en los tests.\n"
            )

        library_name = cve_data.get('library', '')
        vuln_id = cve_data.get('cve') or cve_data.get('id', 'N/A')
        target_var, reasoning_suffix = self._resolve_family(library_name)
        safe_ver = str(cve_data.get('safe_version', 'LATEST')).split(',')[0].strip()

        reasoning = f"Analizando {vuln_id}. La librería detectada es {library_name}. {reasoning_suffix}"

        return (
            f"\n            [PENSAMIENTO]: {reasoning}\n"
            f"            [ACCIÓN]: {target_var} = '{safe_ver}'\n"
            f"            [EXPLICACIÓN]: Se aplica el parche de versión única para mitigar la vulnerabilidad, "
            f"centralizando la definición en la variable de familia '{target_var}'.\n"
        )

    def _resolve_family(self, library_name: str):
        for key, var in self._FAMILY_MAP.items():
            if key in library_name:
                return var, self._FAMILY_REASONING.get(key, "")
        # Inferencia autónoma para librerías desconocidas
        parts = library_name.split(':')[-1].split('-')
        target_var = parts[0] + "".join(p.capitalize() for p in parts[1:]) + "Version"
        return target_var, f"No pertenece a un grupo común. Genero variable específica '{target_var}'."
