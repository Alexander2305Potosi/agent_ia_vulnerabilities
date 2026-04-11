import os
import shutil

# Determinar la raíz del proyecto de forma dinámica (dos niveles arriba de este script)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
root_dir = os.path.join(PROJECT_ROOT, "backend_sales_products")

# Valid empty shell for dependencyMgmt.gradle
RESET_CONTENT = """// Standardized Dependency Management - Centralized AI Security Rules
configurations.all {
    resolutionStrategy.eachDependency { DependencyResolveDetails details ->
        // Inject rules here
    }
}
"""

def cleanup():
    print("[*] Starting systematic cleanup of monorepo...")
    
    for root, dirs, files in os.walk(root_dir):
        # 1. Remove all backups
        for f in files:
            if f.endswith(".bak") or f.endswith(".gradle.bak"):
                path = os.path.join(root, f)
                print(f"    [-] Removing backup: {f}")
                os.remove(path)
        
        # 2. Reset dependencyMgmt.gradle
        if "dependencyMgmt.gradle" in files:
            path = os.path.join(root, "dependencyMgmt.gradle")
            print(f"    [!] Resetting corrupted file: {path}")
            with open(path, 'w') as f:
                f.write(RESET_CONTENT)

    print("[OK] Cleanup complete. Ready for hardened remediation.")

if __name__ == "__main__":
    cleanup()
