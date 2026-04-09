import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

def generate_synthetic_data(num_samples=1000):
    """
    Generates a synthetic dataset for security remediation strategies.
    
    Features:
    - is_transitive: 0 (Direct), 1 (Transitive)
    - project_depth: Depth of microservice in monorepo (0-3)
    - has_dep_mgmt: Does the MS have a dependencyMgmt.gradle (0, 1)
    - severity: 1 (Low) to 4 (Critical)
    - ms_complexity: Number of dependencies (approx)
    
    Target:
    - 0: DIRECT (Apply fix to build.gradle)
    - 1: TRANSITIVE (Apply fix to dependencyMgmt.gradle)
    """
    np.random.seed(42)
    
    # Random features
    is_transitive = np.random.randint(0, 2, num_samples)
    project_depth = np.random.randint(0, 4, num_samples)
    has_dep_mgmt = np.random.randint(0, 2, num_samples)
import random

def generate_dataset(n_samples=2000):
    data = []
    for _ in range(n_samples):
        # Features
        is_transitive = random.choice([0, 1])
        project_depth = random.randint(0, 5)
        has_dep_mgmt = random.choice([0, 1])
        severity = random.randint(1, 4) # 1: Low, 2: Medium, 3: High, 4: Critical
        ms_complexity = random.randint(1, 10)
        
        # NEW FEATURES
        is_multi_version = random.choice([0, 1])
        is_group_scoped = random.choice([0, 1])

        # Target Logic (Decision Tree Heuristics)
        # 1: TRANSITIVE, 0: DIRECT
        
        # Rule 1: Always use TRANSITIVE for multi-version or group-scoped (Safety first)
        if is_multi_version == 1 or is_group_scoped == 1:
            label = 1
        # Rule 2: Prefer TRANSITIVE for deep projects or if dep_mgmt already exists
        elif has_dep_mgmt == 1 or project_depth > 2:
            label = 1
        # Rule 3: Prefer TRANSITIVE for critical/transitive vulns
        elif severity >= 3 and is_transitive == 1:
            label = 1
        # Rule 4: Prefer DIRECT for root projects with direct deps
        else:
            label = 0
            
        data.append([
            is_transitive, project_depth, has_dep_mgmt, severity, 
            ms_complexity, is_multi_version, is_group_scoped, label
        ])
    
    columns = [
        'is_transitive', 'project_depth', 'has_dep_mgmt', 'severity', 
        'ms_complexity', 'is_multi_version', 'is_group_scoped', 'label'
    ]
    return pd.DataFrame(data, columns=columns)

def train_model():
    print("[*] Generating security remediation dataset (Enhanced)...")
    df = generate_dataset()
    
    X = df.drop('label', axis=1)
    y = df['label']
    
    print("[*] Training Random Forest Classifier (v12)...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    accuracy = model.score(X, y)
    print(f"[*] Model Training Complete. Training Accuracy: {accuracy:.4f}")
    
    # Save the model
    # Ensure we save it in the same directory as the script (librerias)
    output_path = os.path.join(os.path.dirname(__file__), 'remediation_model.joblib')
    joblib.dump(model, output_path)
    print(f"[OK] Enhanced model saved to {output_path}")

if __name__ == "__main__":
    train_model()
