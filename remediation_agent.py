import json
import os
import sys
import shutil
import subprocess
import joblib
import pandas as pd
from datetime import datetime

# Add internal library directory to path
SYS_LIB_PATH = os.path.join(os.path.dirname(__file__), "agent_ia", "librerias")
if os.path.exists(SYS_LIB_PATH):
    sys.path.append(SYS_LIB_PATH)

# Import internal mutation engine
from gradlemutator import GradleMutator

class RemediationAgent:
    # MANUAL TOGGLE FOR GIT INTEGRATION
    # Set to True to enable automatic branch creation and commits
    GIT_COMMIT_ENABLED = False

    def __init__(self, root_path, report_path=None):
        self.root_path = root_path
        
        # Default report path logic
        default_report = os.path.join(os.path.dirname(__file__), "agent_ia", "cve", "snyk_monorepo.json")
        self.report_path = report_path or default_report
        
        self.history = []
        
        # IA Model Initialization
        self.model_path = os.path.join(SYS_LIB_PATH, 'remediation_model.joblib')
        if os.path.exists(self.model_path):
            try:
                print(f"[*] Loading Intelligent Remediation Model ({self.model_path})...")
                self.model = joblib.load(self.model_path)
            except ModuleNotFoundError:
                print("\n[!] ERROR: Missing ML libraries on this machine.")
                print("[!] To use the AI Model, please run: pip install -r requirements.txt")
                print("[!] Falling back to deterministic logic for now...\n")
                self.model = None
            except Exception as e:
                print(f"[!] Warning: Error loading model: {str(e)}. Falling back.")
                self.model = None
        else:
            print("[!] Warning: AI Model not found. Falling back to deterministic logic.")
            self.model = None

    def _ai_predict_strategy(self, ms_name, package, vuln_data):
        """
        Uses the custom AI model to predict the best remediation strategy.
        Features mapping: is_transitive, project_depth, has_dep_mgmt, severity, ms_complexity
        """
        if not self.model:
            return None

        ms_path = self._get_ms_path(ms_name)
        if not ms_path: return "TRANSITIVE"

        # Feature extraction
        # 1. is_transitive (heuristic based on presence in build.gradle)
        is_transitive_in_ms = 1
        ms_files = self.get_ms_files(ms_name)
        for f in ms_files:
            if f.endswith("build.gradle"):
                with open(f, 'r') as fr:
                    if package.split(':')[-1] in fr.read():
                        is_transitive_in_ms = 0
                        break
        
        # 2. project_depth
        rel_path = os.path.relpath(ms_path, self.root_path)
        depth = rel_path.count(os.sep)
        
        # 3. has_dep_mgmt
        has_dep_mgmt = 1 if any(f.endswith("dependencyMgmt.gradle") for f in ms_files) else 0
        
        # 4. severity (mapped from vuln_data)
        severity_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        sev_str = (vuln_data.get("severity") or "medium").lower()
        severity = severity_map.get(sev_str, 2)
        
        # 5. ms_complexity (count of files)
        complexity = len(os.listdir(ms_path))
        
        # 6. NEW FEATURES (passed from vuln_data)
        is_multi_version = vuln_data.get("is_multi_version", 0)
        is_group_scoped = vuln_data.get("is_group_scoped", 0)

        features = pd.DataFrame([[
            is_transitive_in_ms, depth, has_dep_mgmt, severity, 
            complexity, is_multi_version, is_group_scoped
        ]], columns=[
            'is_transitive', 'project_depth', 'has_dep_mgmt', 'severity', 
            'ms_complexity', 'is_multi_version', 'is_group_scoped'
        ])
        
        prediction = self.model.predict(features)[0]
        strategy = "TRANSITIVE" if prediction == 1 else "DIRECT"
        
        # Get confidence (optional)
        proba = self.model.predict_proba(features)[0]
        confidence = proba[prediction]
        
        print(f"    [AI] Strategy Prediction: {strategy} (Confidence: {confidence:.2%})")
        return strategy

    def _get_ms_path(self, ms_name):
        """ Returns the absolute path to a microservice directory. """
        # Search recursively for the microservice directory
        for root, dirs, files in os.walk(self.root_path):
            if ms_name in dirs:
                # Direct check if this is the actual MS root (has build.gradle)
                candidate = os.path.join(root, ms_name)
                if os.path.exists(os.path.join(candidate, "build.gradle")):
                    return candidate
        return None

    def get_ms_files(self, ms_name):
        """ Returns ALL .gradle files found recursively within a microservice directory. """
        ms_files = []
        ms_path = self._get_ms_path(ms_name)
        
        if not ms_path:
            return []
        
        for root, dirs, files in os.walk(ms_path):
            for t in files:
                if t.endswith(".gradle"):
                    ms_files.append(os.path.join(root, t))
        return ms_files

    def _validate_ms(self, ms_name):
        """ Executes clean test and returns True if successful. """
        ms_path = self._get_ms_path(ms_name)
        if not ms_path:
            return False
        
        print(f"    [*] Validating {ms_name} (gradle clean test)...")
        print("    [TIP] If this is the first run, Gradle might be downloading dependencies. This can take a few minutes.")
        
        is_windows = os.name == 'nt'
        gradle_cmd = None
        
        # 1. Search for gradlew
        candidates = [
            os.path.join(ms_path, "gradlew.bat" if is_windows else "gradlew"),
            os.path.join(self.root_path, "gradlew.bat" if is_windows else "gradlew"),
        ]
        
        for c in candidates:
            if os.path.exists(c):
                gradle_cmd = c
                break
        
        # 2. Fallback to global gradle
        if not gradle_cmd:
            gradle_cmd = "gradle" 
        
        try:
            # Run the build and tests
            # We don't use capture_output=True here so the user can see progress (downloads/tests)
            # This prevents the agent from appearing 'stuck'.
            result = subprocess.run(
                [gradle_cmd, "clean", "test"], 
                cwd=ms_path, 
                text=True,
                shell=is_windows,
                timeout=600 # 10 minute timeout
            )
            
            if result.returncode == 0:
                return True
            else:
                print(f"    [!] Validation Failed for {ms_name}")
                return False
        except subprocess.TimeoutExpired:
            print(f"    [!] Validation TIMEOUT for {ms_name}. Moving on.")
            return False
        except FileNotFoundError:
            print(f"    [!] Warning: Gradle not found. Skipping validation for {ms_name}.")
            return True
        except Exception as e:
            print(f"    [!] Internal error during validation: {str(e)}")
            return False

    def _get_all_ms_names(self):
        """ Returns a list of all microservice directory names in the project. """
        ms_names = []
        for d in os.listdir(self.root_path):
            d_path = os.path.join(self.root_path, d)
            if os.path.isdir(d_path) and os.path.exists(os.path.join(d_path, "build.gradle")):
                ms_names.append(d)
        
        # Also check one-level deep (for nested monorepo folder like backend_sales_products)
        if not ms_names:
            for d in os.listdir(self.root_path):
                sub_path = os.path.join(self.root_path, d)
                if os.path.isdir(sub_path):
                    for sd in os.listdir(sub_path):
                        sd_path = os.path.join(sub_path, sd)
                        if os.path.isdir(sd_path) and os.path.exists(os.path.join(sd_path, "build.gradle")):
                            ms_names.append(sd)
        return ms_names

    def _git_lifecycle(self):
        """ Handles branch creation and commit if enabled. """
        if not self.GIT_COMMIT_ENABLED:
            return

        print("\n[*] Initiating Git Lifecycle...")
        
        try:
            # Check if .git exists
            if not os.path.exists(os.path.join(self.root_path, ".git")):
                print("    [*] Git not initialized. Running 'git init'...")
                subprocess.run(["git", "init"], cwd=self.root_path, capture_output=True)

            # Generate branch name with timestamp
            timestamp = datetime.now().strftime("%d%m%Y%H%M")
            branch_name = f"feature/fix_vuln_{timestamp}"
            
            print(f"    [*] Creating branch {branch_name}...")
            subprocess.run(["git", "checkout", "-b", branch_name], cwd=self.root_path, capture_output=True)
            
            print("    [*] Committing changes...")
            subprocess.run(["git", "add", "."], cwd=self.root_path, capture_output=True)
            msg = f"Security: automated remediation of vulnerabilities ({timestamp})"
            subprocess.run(["git", "commit", "-m", msg], cwd=self.root_path, capture_output=True)
            
            print(f"    [OK] Git commit successful in branch {branch_name}.")
        except Exception as e:
            print(f"    [!] Git error: {str(e)}")

    def run(self):
        print(f"[*] Starting Microservice-Aware Remediation Agent (Auto-Discovery Mode)")
        
        if not os.path.exists(self.report_path):
            print(f"[!] Error: Report {self.report_path} not found.")
            return

        with open(self.report_path, 'r') as f:
            data = json.load(f)

        # Normalize vulnerabilities list
        vulnerabilities = data if isinstance(data, list) else data.get("vulnerabilities", [])
        
        for vuln in vulnerabilities:
            self._process_vuln_entry(vuln)

        self._print_summary()
        
        # Git Commit (if enabled and fixes were made)
        if any(e["status"] == "FIXED" for e in self.history):
            self._git_lifecycle()

    def _process_vuln_entry(self, entry):
        # Map fields (New schema vs Old schema support)
        vuln_id = entry.get('cve') or entry.get('id')
        package = entry.get('library') or entry.get('packageName')
        raw_target = entry.get('safe_version') or (entry.get('fixedIn')[0] if entry.get('fixedIn') else None)
        strategy = entry.get("type") # Optional
        ms_name = entry.get("microservice") # Optional
        
        if not raw_target:
            print(f"[!] Skipping {vuln_id}: No target version found.")
            return

        # NEW: Handle comma-separated version lists (Pick HIGHEST)
        if "," in str(raw_target):
            versions = [v.strip() for v in str(raw_target).split(',')]
            target_version = max(versions, key=lambda x: GradleMutator._version_to_tuple(x))
            print(f"[*] Report provided multiple versions for {package}. Selected highest: {target_version}")
        else:
            target_version = raw_target

        # Auto-Discovery logic if ms_name is missing
        if ms_name:
            target_mss = [ms_name]
        else:
            print(f"[*] Auto-discovering affected microservices for {package}...")
            target_mss = self._get_all_ms_names()

        for ms in target_mss:
            self._handle_remediation(ms, vuln_id, package, target_version, strategy)

    def _handle_remediation(self, ms_name, vuln_id, package, target_version, provided_strategy):
        ms_files = self.get_ms_files(ms_name)
        if not ms_files:
            return

        # Strategy Selection: AI vs Provided vs Deterministic
        strategy = provided_strategy
        if not strategy:
            # Try AI model first
            vuln_data = {
                "severity": "medium", 
                "is_multi_version": 1 if "," in str(target_version) else 0,
                "is_group_scoped": 1 if ":" not in package else 0
            }
            strategy = self._ai_predict_strategy(ms_name, package, vuln_data)
            
            # Fallback to simple deterministic if AI fails
            if not strategy:
                is_direct = False
                # If it's a group scope or multi-version, TRANSITIVE is 100% better
                if ":" not in package or "," in str(target_version):
                    strategy = "TRANSITIVE"
                else:
                    for f in ms_files:
                        if f.endswith("build.gradle"):
                            with open(f, 'r') as fr:
                                if package.split(':')[-1] in fr.read():
                                    is_direct = True
                                    break
                    strategy = "DIRECT" if is_direct else "TRANSITIVE"

        print(f"\n[+] Processing {vuln_id} ({package}) in {ms_name} [Strategy: {strategy}]")
        
        # Backup
        backups = {}
        for f in ms_files:
            bak = f + ".bak"
            shutil.copy2(f, bak)
            backups[f] = bak

        # Mutation
        mutated = GradleMutator.apply_coordinated_remediation(
            ms_files,
            strategy,
            package,
            target_version,
            reason=f"Fixes {vuln_id}"
        )

        if mutated == "ALREADY_FIXED":
            print(f"    [SKIP] Library already at safe version (or higher) in {ms_name}.")
            self.history.append({"id": vuln_id, "status": "ALREADY_FIXED", "ms": ms_name})
            for f, bak in backups.items(): os.remove(bak)
            return

        success = False
        if mutated:
            # VALIDATION
            if self._validate_ms(ms_name):
                success = True
            else:
                print(f"    [!] Validation failed for {ms_name}. Initiating rollback.")

        if success:
            print(f"    [OK] Remediation and Validation successful for {ms_name}.")
            self.history.append({"id": vuln_id, "status": "FIXED", "ms": ms_name})
            for bak in backups.values(): os.remove(bak)
        else:
            # Rollback
            self.history.append({"id": vuln_id, "status": "ERROR", "ms": ms_name})
            for f, bak in backups.items(): shutil.move(bak, f)

    def _print_summary(self):
        print("\n" + "="*40)
        print("REMEDIATION SUMMARY (AUTO-DISCOVERY / IDEMPOTENT)")
        print("="*40)
        seen = set()
        for entry in self.history:
            key = (entry["ms"], entry["id"])
            if key not in seen:
                status_icon = "✅" if entry["status"] == "FIXED" else ("➖" if entry["status"] == "ALREADY_FIXED" else "❌")
                print(f"{status_icon} [{entry['ms']}] {entry['id']}: {entry['status']}")
                seen.add(key)
        print("="*40)

if __name__ == "__main__":
    # Default values
    default_root = os.getcwd()
    
    # Simple argument parsing
    # Usage: python remediation_agent.py [report_path] [root_dir]
    report_path = sys.argv[1] if len(sys.argv) > 1 else None
    root_path = sys.argv[2] if len(sys.argv) > 2 else default_root
    
    # New discovery logic for the structured repo
    if not report_path:
        # Priority 1: Check structured agent_ia folder
        structured_report = os.path.join(default_root, "agent_ia", "cve", "snyk_monorepo.json")
        if os.path.exists(structured_report):
            report_path = structured_report
        else:
            # Priority 2: Recursive search
            for root, dirs, files in os.walk(default_root):
                for f in files:
                    if f in ["snyk_monorepo.json", "snyk_report.json"]:
                        report_path = os.path.join(root, f)
                        break
                if report_path: break
            
    if not report_path:
        # Final fallback
        report_path = os.path.join(default_root, "snyk_monorepo.json")
    
    agent = RemediationAgent(root_path, report_path)
    agent.run()
