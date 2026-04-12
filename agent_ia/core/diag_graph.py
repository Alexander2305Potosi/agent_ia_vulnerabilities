from agent_ia.core.graph import DependencyGraph
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
ms_path = os.path.join(project_root, "backend_sales_products", "ms-auth")
gradle_bin = "gradle" # Rely on path for portability

print(f"[*] Probando DependencyGraph en {ms_path}")
g = DependencyGraph(gradle_bin)
if g.build_for_project(ms_path):
    print("[*] Grafo construido con éxito.")
    lineage = g.get_lineage("com.fasterxml.jackson.core:jackson-databind")
    print(f"[*] Linaje de Jackson: {' -> '.join(lineage)}")
    
    lineage2 = g.get_lineage("org.reactivestreams:reactive-streams")
    print(f"[*] Linaje de Reactive Streams: {' -> '.join(lineage2)}")
    
    lineage3 = g.get_lineage("io.netty:netty-handler")
    print(f"[*] Linaje de Netty Handler: {' -> '.join(lineage3)}")
else:
    print("[!] Fallo al construir el grafo.")
