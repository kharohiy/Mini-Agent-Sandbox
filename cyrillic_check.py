import os, re

def find_cyrillic(path):
    cyrillic_pattern = re.compile(r'[а-яА-ЯёЁ]')
    for root, _, files in os.walk(path):
        if '.git' in root or '.system_generated' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith(('.py', '.yaml', '.json')): # excluded .md because README.md and TESTS.md are legitimately in Russian.
                full_path = os.path.join(root, file)
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if cyrillic_pattern.search(content):
                        print(f"Found Cyrillic in: {full_path}")

find_cyrillic('.')
