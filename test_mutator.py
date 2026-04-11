import re

def substitute_literal_with_variable(content, package, var_name):
    verbs = "implementation|runtimeOnly|runtime|compileOnly|compile|api|testImplementation|testRuntimeOnly|testCompileOnly"
    pattern = rf"^(\s*)({verbs})(\s*)['\"]{re.escape(package)}(?::[^'\"]+)?['\"]"
    
    def replace_literal_fn(match):
        return f"{match.group(1)}{match.group(2)}{match.group(3)}\"{package}:${{{var_name}}}\""
        
    new_content, count = re.subn(pattern, replace_literal_fn, content, flags=re.MULTILINE)
    return new_content

test_content = """
dependencies {
    implementation 'io.netty:netty-codec-http:4.1.68.Final'
    testImplementation "org.junit:junit:4.13"
    api 'com.google.guava:guava:30.1-jre'
    implementation project(':')
}
"""

print("--- ORIGINAL ---")
print(test_content)

result = substitute_literal_with_variable(test_content, "io.netty:netty-codec-http", "nettyCodecHttpVersion")
result = substitute_literal_with_variable(result, "org.junit:junit", "junitVersion")
result = substitute_literal_with_variable(result, "com.google.guava:guava", "guavaVersion")

print("--- RESULT ---")
print(result)

# Quick assertions
assert 'implementation "io.netty:netty-codec-http:${nettyCodecHttpVersion}"' in result
assert 'testImplementation "org.junit:junit:${junitVersion}"' in result
assert 'api "com.google.guava:guava:${guavaVersion}"' in result
assert "implementation project(':')" in result
print("--- SUCCESS ---")
