import sys
import os

class CycleOfConsciousness:
    """
    Controlador del bucle de autocuración (v.30).
    Permite que el agente aprenda de sus errores de ejecución de forma recursiva.
    """
    
    def __init__(self, generative_engine, validator_fn):
        self.engine = generative_engine
        self.validate = validator_fn
        self.max_attempts = 3

    def run_remediation_cycle(self, cve_data, local_context):
        """
        Inicia el ciclo: Generar -> Aplicar -> Validar -> Aprender.
        """
        attempts = 0
        previous_error = None
        
        while attempts < self.max_attempts:
            attempts += 1
            print(f"    [Ciclo v.30] Intento {attempts}/{self.max_attempts}...")
            
            # 1. GENERACIÓN (Cerebro Generativo)
            response = self.engine.generate_remediation(cve_data, local_context, previous_error)
            parsed = self.engine.parse_react_response(response)
            
            print(f"    [PENSAMIENTO]: {parsed['thought']}")
            print(f"    [ACCIÓN]: {parsed['action']}")
            
            # 2. APLICACIÓN (Aquí iría el Mutator real, simulamos éxito para la prueba lógica)
            # self.apply(parsed['action'])
            
            # 3. VALIDACIÓN (Gradle / Pip / etc)
            success, result_data = self.validate(parsed['action'], attempts, cve_data)
            
            if success:
                print(f"    [OK] Ciclo completado exitosamente en el intento {attempts}.")
                return True, parsed['explanation'], result_data
            else:
                # 4. ERROR FATAL (Abortar Ciclo)
                if isinstance(result_data, dict) and result_data.get("fatal"):
                    print(f"    [FATAL] {result_data.get('message', 'Error de infraestructura')}")
                    return False, f"Abortado por error fatal: {result_data.get('message')}", result_data

                # 5. APRENDIZAJE (Ciclo de Conciencia)
                print(f"    [!] Error detectado. Re-inyectando contexto de fallo al modelo...")
                previous_error = result_data # Aquí result_data es el error_log
                
        print("    [ERROR] No se pudo solventar la vulnerabilidad tras los intentos permitidos.")
        return False, "Se agotaron los intentos de autocuración o error persistente.", None

if __name__ == "__main__":
    # Prueba rápida del ciclo
    from agent_ia.engine.generative import GenerativeAgentV2
    
    def mock_validator(action, attempt):
        # Simula un error en el primer intento y éxito en el segundo
        if attempt == 1:
            return False, "ERROR: Versión incompatible detectada en Gradle Sync."
        return True, None

    engine = GenerativeAgentV2()
    cycle = CycleOfConsciousness(engine, mock_validator)
    cycle.run_remediation_cycle({"cve": "CVE-2026", "library": "netty"}, "Project: ms-auth")
