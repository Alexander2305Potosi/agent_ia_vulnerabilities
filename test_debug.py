import sys, os
sys.path.append(os.getcwd())
from agent_ia.scripts.run_master_certification import reset_env, MS_SALES_PATH, setup_cve, run_agent
import shutil

def cert_seamless_buildscript():
    reset_env()
    root_gradle = os.path.join(MS_SALES_PATH, "build.gradle")
    with open(root_gradle, 'w') as f:
        f.write("buildscript {\n    ext {\n        fakeVersion = '1.0'\n    }\n}\nplugins { id 'java' }\n")
        
    setup_cve([{
        "priority": "critical", "cve": "CVE-2026-ALIGN",
        "library": "io.netty:netty-codec-http",
        "safe_version": "4.1.132.Final",
        "microservice": "ms-sales"
    }])
    
    result = run_agent(["ms-sales"])
    
    with open(root_gradle, 'r') as f:
        print("--- ROOT CONTENT ---")
        print(f.read())
        
cert_seamless_buildscript()
