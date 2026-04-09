import os
import shutil

root_dir = "/Volumes/Macintosh HD - Data/repaso/laboratorio/IA/laboratorio agente/backend_sales_products"

# Valid empty shell for dependencyMgmt.gradle
RESET_CONTENT = """// Standardized Dependency Management - Centralized AI Security Rules
configurations.all {
    resolutionStrategy.eachDependency { DependencyResolveDetails details ->
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
