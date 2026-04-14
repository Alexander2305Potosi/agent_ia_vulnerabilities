from agent_ia.core.mutator import VariableManager
content = """buildscript {\n    ext {\n        fakeVersion = '1.0'\n    }\n}\nplugins { id 'java' }\n"""
v_name = "nettyCodecHttpVersion"
safe_v = "4.1.132.Final"
nc, success = VariableManager.update_variable(content, v_name, safe_v, is_root=True)
print(f"Success: {success}")
print("--- CONTENT ---")
print(nc)
