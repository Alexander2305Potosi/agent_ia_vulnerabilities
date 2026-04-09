import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import os
import random

def generate_architectural_dataset(n_samples=3000):
    """
    Generates a dataset for architectural remediation decisions.
    
    Target Mapping:
    - 0: DIRECT_FIX (build.gradle)
    - 1: TRANSITIVE_FIX (dependencyMgmt.gradle)
    - 2: FRAMEWORK_ALIGNMENT (main.gradle)
    """
    data = []
    for _ in range(n_samples):
        # Features
        is_transitive = random.choice([0, 1])
        project_depth = random.randint(0, 5)
        has_dep_mgmt = random.choice([0, 1])
        has_main_gradle = random.choice([0, 1])
        severity = random.randint(1, 4)
        is_multi_version = random.choice([0, 1])
        is_group_scoped = random.choice([0, 1])
        is_spring_boot_parent = random.choice([0, 1]) # If the CVE is in Spring itself

        # Logic for Architectural Decision
        if is_spring_boot_parent == 1 and has_main_gradle == 1:
            label = 2  # Target main.gradle (Framework Alignment)
        elif is_group_scoped == 1 or is_transitive == 1 or is_multi_version == 1:
            label = 1  # Target dependencyMgmt.gradle (Transitive/Group enforcement)
        elif is_transitive == 0:
            label = 0  # Target build.gradle (Direct update)
        else:
            label = 1  # Default to transitive safety if unsure

        data.append([
            is_transitive, project_depth, has_dep_mgmt, has_main_gradle,
            severity, is_multi_version, is_group_scoped, is_spring_boot_parent,
            label
        ])
    
    columns = [
        'is_transitive', 'project_depth', 'has_dep_mgmt', 'has_main_gradle',
        'severity', 'is_multi_version', 'is_group_scoped', 'is_spring_boot_parent',
        'label'
    ]
    return pd.DataFrame(data, columns=columns)

def train_model():
    print("[*] Generating Architectural Remediation Dataset (v17)...")
    df = generate_architectural_dataset()
    
    X = df.drop('label', axis=1)
    y = df['label']
    
    print("[*] Training Multi-class Random Forest Classifier (v17)...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    accuracy = model.score(X, y)
    print(f"[*] Model Training Complete. Training Accuracy: {accuracy:.4f}")
    
    # Save the model
    output_path = os.path.join(os.path.dirname(__file__), 'remediation_model.joblib')
    joblib.dump(model, output_path)
    print(f"[OK] Architectural model v17 saved to {output_path}")

if __name__ == "__main__":
    train_model()
