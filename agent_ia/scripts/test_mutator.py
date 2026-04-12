import sys
import os

# Asegurar que podemos importar agent_ia
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent_ia.core.mutator import VariableManager

def test_substitute_literals():
    print("🧪 [TEST] Iniciando validación de VariableManager.substitute_literals...")
    
    cases = [
        {
            "name": "BOM Dependency (No version) - SHOULD NOT MODIFY",
            "content": "    implementation 'io.netty:netty-handler'",
            "package": "io.netty:netty-handler",
            "var": "nettyCodecVersion",
            "expected": "    implementation 'io.netty:netty-handler'"
        },
        {
            "name": "Literal Version - SHOULD MODIFY VERSION AND USE DOUBLE QUOTES",
            "content": "    implementation 'io.netty:netty-handler:4.1.100.Final'",
            "package": "io.netty:netty-handler",
            "var": "nettyCodecVersion",
            "expected": '    implementation "io.netty:netty-handler:${nettyCodecVersion}"'
        },
        {
            "name": "Family Match with Version - SHOULD MODIFY VERSION ONLY",
            "content": "    runtimeOnly \"io.netty:netty-codec-http:4.1.90.Final\"",
            "package": "io.netty:netty-handler", # Familia io.netty
            "var": "nettyCodecVersion",
            "expected": "    runtimeOnly \"io.netty:netty-codec-http:${nettyCodecVersion}\""
        },
         {
            "name": "Single Quote Version - SHOULD CONVERT TO DOUBLE QUOTES FOR INTERPOLATION",
            "content": "    implementation 'io.netty:netty-handler:4.1.100.Final'",
            "package": "io.netty:netty-handler",
            "var": "nettyCodecVersion",
            "expected": '    implementation "io.netty:netty-handler:${nettyCodecVersion}"'
        }
    ]
    
    passed = 0
    for case in cases:
        result, changed = VariableManager.substitute_literals(case["content"], case["package"], case["var"])
        if result.strip() == case["expected"].strip():
            print(f"✅ [PASS] {case['name']}")
            passed += 1
        else:
            print(f"❌ [FAIL] {case['name']}")
            print(f"    Target:   {case['content']}")
            print(f"    Expected: {case['expected']}")
            print(f"    Result:   {result}")
            
    print(f"\n📊 Resultado: {passed}/{len(cases)} pruebas superadas.")

if __name__ == "__main__":
    test_substitute_literals()
