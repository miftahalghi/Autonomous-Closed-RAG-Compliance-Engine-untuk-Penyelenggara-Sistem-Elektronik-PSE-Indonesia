import json

with open(r'C:\Users\Lenovo\audit-pdp-poc\audit_pdp_flow.json', 'r', encoding='utf-8') as f:
    flow = json.load(f)

nodes = flow.get('data', {}).get('nodes', [])
print(f'Total nodes: {len(nodes)}')

for i, node in enumerate(nodes):
    data = node.get('data', {})
    node_id = node.get('id')
    node_name = data.get('node', {}).get('display_name') or data.get('type')
    code = data.get('node', {}).get('template', {}).get('code', {}).get('value', '')
    if not code:
        print(f'[{i}] Node {node_id} ({node_name}): No code.value')
        continue
    lines = code.split('\n')
    print(f'[{i}] Node {node_id} ({node_name}): {len(lines)} lines')
    try:
        compile(code, f'<{node_name}>', 'exec')
        print(f'     -> compile OK')
    except SyntaxError as e:
        print(f'     -> SYNTAX ERROR: {e} at line {e.lineno}')
        if e.lineno and 0 <= e.lineno - 1 < len(lines):
            for offset in range(-5, 6):
                l_idx = e.lineno - 1 + offset
                if 0 <= l_idx < len(lines):
                    print(f'        line {l_idx+1}: {repr(lines[l_idx])}')
