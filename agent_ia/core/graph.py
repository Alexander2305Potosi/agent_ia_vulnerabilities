import subprocess
import re
import os
from agent_ia.core.providers import JDKManager

class DependencyGraph:
    """
    Analizador de Grafo de Dependencias v.30.13.
    Permite descubrir el linaje y origen de las vulnerabilidades transitivas.
    Soporta Adaptación de Entorno (JDK-Aware).
    """
    
    def __init__(self, gradle_cmd):
        self.gradle_cmd = gradle_cmd
        self.graph = {} # {child: [parents]}
        self.java_home = JDKManager.get_best_java_home()
        
    def build_for_project(self, project_path):
        """ Ejecuta gradle dependencies y construye el grafo en memoria. """
        try:
            # v.30: Usar configuración runtimeClasspath por ser la más certera para seguridad
            cmd = [self.gradle_cmd, "dependencies", "--configuration", "runtimeClasspath"]
            
            # v.30.13: Inyectar JAVA_HOME si fue detectado para evitar fallos de inicialización
            env = os.environ.copy()
            if self.java_home:
                env["JAVA_HOME"] = self.java_home
                env["PATH"] = os.path.join(self.java_home, "bin") + os.pathsep + env.get("PATH", "")

            result = subprocess.run(cmd, cwd=project_path, capture_output=True, text=True, check=True, env=env)
            self._parse_output(result.stdout)
            return True
        except Exception as e:
            # Fallback silencioso pero informativo
            print(f"    ⚠️ [GRAPH] Error construyendo grafo: {str(e)}")
            return False
    
    def _parse_output(self, output):
        lines = output.splitlines()
        stack = [] # [(indent, artifact_id)]
        
        for line in lines:
            if '---' not in line: continue
            
            # 1. Extraer indentación y nombre del artefacto
            # Regex busca: [prefijo] +--- [group:artifact:version]
            match = re.search(r'([|+\s]*)[\+\\]--- ([\w\.\-\:]+)', line)
            if not match: continue
            
            prefix, artifact_raw = match.groups()
            indent = len(prefix)
            
            # Limpiar nombre del artefacto (group:id)
            parts = artifact_raw.split(':')
            if len(parts) < 2: continue
            artifact_group_id = f"{parts[0]}:{parts[1]}"
            
            # 2. Reconstruir jerarquía usando el stack
            while stack and stack[-1][0] >= indent:
                stack.pop()
            
            parent = stack[-1][1] if stack else "ROOT"
            
            if artifact_group_id not in self.graph:
                self.graph[artifact_group_id] = set()
            self.graph[artifact_group_id].add(parent)
            
            stack.append((indent, artifact_group_id))

    def get_lineage(self, target_artifact):
        """ Retorna la ruta desde ROOT hasta el artefacto (BFS simplificado). """
        # Normalizar target si viene con versión
        target = ":".join(target_artifact.split(':')[:2])
        
        if target not in self.graph:
            return ["UNKNOWN_ORIGIN"]
            
        # Retornamos la ruta más corta hasta el ROOT (simplificado para v.30)
        path = [target]
        curr = target
        while curr in self.graph:
            parents = list(self.graph[curr])
            if not parents or parents[0] == "ROOT": break
            curr = parents[0]
            path.insert(0, curr)
            
        return path

if __name__ == "__main__":
    # Prueba rápida si se ejecuta solo
    g = DependencyGraph("gradle")
    # Simulación de parseo
    sample = """
+--- org.springframework.boot:spring-boot-starter-webflux:3.3.4
|    +--- org.springframework.boot:spring-boot-starter:3.3.4
|    \\--- org.springframework.boot:spring-boot-starter-reactor-netty:3.3.4
|         \\--- io.projectreactor.netty:reactor-netty-http:1.1.22
|              \\--- io.netty:netty-codec-http:4.1.112.Final
"""
    g._parse_output(sample)
    print(f"Linaje de Netty: {' -> '.join(g.get_lineage('io.netty:netty-codec-http'))}")
