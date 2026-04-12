import subprocess
import json
import os
import shutil
import re

# --- CONFIGURACIÓN ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AGENT_CMD = ["python3", os.path.join(PROJECT_ROOT, "remediation_agent.py"), "--folders", "ms-auth"]
CVE_REPORT_PATH = os.path.join(PROJECT_ROOT, "agent_ia", "data", "cve", "snyk_monorepo.json")
MS_AUTH_PATH = os.path.join(PROJECT_ROOT, "backend_sales_products", "ms-auth")
BUILD_GRADLE = os.path.join(MS_AUTH_PATH, "build.gradle")
DEP_MGMT = os.path.join(MS_AUTH_PATH, "dependencyMgmt.gradle")

# Backup de estado original para asegurar pruebas atómicas
BG_BACKUP = None
if os.path.exists(BUILD_GRADLE):
    with open(BUILD_GRADLE, 'r') as f:
        BG_BACKUP = f.read()

def reset_ms_state():
    """ Restaura el microservicio a un estado 'limpio' antes de cada test. """
    if BG_BACKUP:
        with open(BUILD_GRADLE, 'w') as f:
            f.write(BG_BACKUP)
    if os.path.exists(DEP_MGMT):
        os.remove(DEP_MGMT)
    if os.path.exists(CVE_REPORT_PATH):
        os.remove(CVE_REPORT_PATH)

def run_agent():
    env = os.environ.copy()
    env["AGENT_IA_LAB_MODE"] = "true"
    result = subprocess.run(AGENT_CMD, cwd=PROJECT_ROOT, env=env, capture_output=True, text=True)
    return result

def setup_cve(cves):
    with open(CVE_REPORT_PATH, 'w') as f:
        json.dump(cves, f, indent=4)

def check_file_contains(file_path, text):
    if not os.path.exists(file_path): return False
    with open(file_path, 'r') as f:
        return text in f.read()

def test_rule_3_2_sanitization():
    reset_ms_state()
    print("[*] Regla 3.2: Sanitización de Versiones (Pick strictly ONE)")
    setup_cve([{
        "priority": "high", "cve": "CVE-2026-MULTI",
        "library": "io.netty:netty-handler",
        "vulnerable_version": "4.1.130.Final", 
        "safe_version": "4.1.155, 4.2.0", # Multiple versions in report
        "description": "Rule 3.2: Selection of branch-appropriate version"
    }])
    run_agent()
    with open(BUILD_GRADLE, 'r') as f:
        content = f.read()
        if "4.1.155" in content and "4.2.0" not in content:
            print("✅ [PASS] Rule 3.2: Correct branch-specific version selected (4.1.155).")
            return True
        else:
            print(f"❌ [FAIL] Rule 3.2: Sanitization failed. Content preview: {content[:200]}...")
            return False

def test_rule_3_3_audit_cleanliness():
    reset_ms_state()
    print("[*] Regla 3.3: Estándar de Auditoría (No accumulation)")
    # 1. Pre-poblar con una razón vieja y usando COMILLAS DOBLES para estresar el buscador de v3.3
    with open(DEP_MGMT, 'w') as f:
        f.write('configurations.all {\n    resolutionStrategy.eachDependency { details -> \n')
        f.write('        if (details.requested.group == "com.fasterxml.jackson.core") { \n')
        f.write('            details.useVersion "${jacksonCoreVersion}" \n')
        f.write('            details.because "Fix: OLD-CVE" \n')
        f.write('        }\n    }\n}\n')
    
    setup_cve([{
        "priority": "critical", "cve": "CVE-NEW-2026",
        "library": "com.fasterxml.jackson.core:jackson-databind",
        "vulnerable_version": "2.17.0", "safe_version": "2.18.9",
        "description": "Rule 3.3: Audit message reset"
    }])
    run_agent()
    
    with open(DEP_MGMT, 'r') as f:
        content = f.read()
        if "Fix: CVE-NEW-2026" in content and "OLD-CVE" not in content:
            print("✅ [PASS] Rule 3.3: Audit message replaced correctly (no accumulation).")
            return True
        else:
            print(f"❌ [FAIL] Rule 3.3: Accumulation detected or replace failed. Content: {content}")
            return False

def test_rule_6_infrastructure_recovery():
    reset_ms_state()
    print("[*] Regla 6: Auto-Curación de Infraestructura (Automatic Rebirth)")
    # El reset_ms_state ya borra DEP_MGMT
    
    setup_cve([{
        "priority": "medium", "cve": "CVE-TRANSITIVE-RECOVER",
        "library": "org.yaml:snakeyaml",
        "vulnerable_version": "1.30", "safe_version": "2.0",
        "description": "Rule 6: Auto-creation of missing dependencyMgmt.gradle"
    }])
    run_agent()
    
    if os.path.exists(DEP_MGMT) and check_file_contains(DEP_MGMT, "details.useVersion"):
        print("✅ [PASS] Rule 6: dependencyMgmt.gradle recreated successfully.")
        return True
    else:
        print("❌ [FAIL] Rule 6: Failed to recreate infrastructure.")
        return False

def test_rule_3_4_family_mapping():
    reset_ms_state()
    print("[*] Regla 3.4: Mapeo de Familias (Coordinated Update)")
    setup_cve([{
        "priority": "high", "cve": "CVE-NETTY-FAMILY",
        "library": "io.netty:netty-handler",
        "vulnerable_version": "4.1.130.Final", "safe_version": "4.1.160.Final",
        "description": "Rule 3.4: Family variable synchronization"
    }])
    run_agent()
    if check_file_contains(BUILD_GRADLE, "nettyCodecVersion = '4.1.160.Final'"):
        print("✅ [PASS] Rule 3.4: Family variable 'nettyCodecVersion' used for direct dependency.")
        return True
    else:
        print("❌ [FAIL] Rule 3.4: Incorrect variable used or not updated.")
        return False

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🛡️ SUITE DE PRUEBAS DE CONFIANZA v3.3 - AGENTE IA")
    print("="*50)
    
    results = [
        test_rule_3_2_sanitization(),
        test_rule_3_3_audit_cleanliness(),
        test_rule_6_infrastructure_recovery(),
        test_rule_3_4_family_mapping()
    ]
    
    if all(results):
        print("\n🏆 [ESTADO FINAL] REGLAS CUMPLIDAS AL 100%")
    else:
        print("\n⚠️ [ESTADO FINAL] FALLOS DETECTADOS EN LA SUITE.")
    
    print("="*50)
    print("[*] Validation Suite Finished.")
