import re

def parse_gradle_dependencies(output):
    lines = output.splitlines()
    graph = {}
    stack = [] # Stores (indent_level, artifact)
    
    for line in lines:
        if '---' not in line:
            continue
            
        # Determine indent level (number of characters before +--- or \---)
        match = re.search(r'([|+\s]*)[\+\\]--- ([\w\.\-\:]+)', line)
        if match:
            prefix = match.group(1)
            artifact_raw = match.group(2)
            # Remove version info from artifact name for easier matching
            artifact = ":".join(artifact_raw.split(':')[:2])
            
            indent = len(prefix)
            
            # Pop from stack until we find the parent (lower indent)
            while stack and stack[-1][0] >= indent:
                stack.pop()
            
            parent = stack[-1][1] if stack else "ROOT"
            
            if artifact not in graph:
                graph[artifact] = set()
            graph[artifact].add(parent)
            
            stack.append((indent, artifact))
            
    return graph

# Test with a snippet of the actual output
sample = """
|    +--- org.springframework.boot:spring-boot-starter-reactor-netty:3.3.4
|    |    \--- io.projectreactor.netty:reactor-netty-http:1.1.22
|    |         +--- io.netty:netty-codec-http:4.1.112.Final -> 4.1.140.Final FAILED
"""

g = parse_gradle_dependencies(sample)
print(g)
