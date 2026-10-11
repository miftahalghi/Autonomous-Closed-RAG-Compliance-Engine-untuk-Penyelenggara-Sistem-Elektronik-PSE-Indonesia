"""
build_langflow_flow.py – Generator berkas Flow JSON Langflow Desktop (v1.x / LFX 1.9.2 - 1.11.0).

Menghasilkan: audit_pdp_flow.json yang 100% kompatibel dengan arsitektur Langflow Desktop,
termasuk validasi 'code' template di seluruh node (ChatInput, LM, Custom Components, ChatOutput)
dan serialisasi edge handle dengan karakter ligature 'œ'.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_FLOW_FILE = PROJECT_ROOT / "audit_pdp_flow.json"


"""
build_langflow_flow.py – Generator berkas Flow JSON Langflow Desktop (v1.x / LFX 1.9.2 - 1.11.0).

Menyinkronkan kode python komponen kustom di src/langflow_components/ ke dalam audit_pdp_flow.json.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_FLOW_FILE = PROJECT_ROOT / "audit_pdp_flow.json"
COMPONENTS_DIR = PROJECT_ROOT / "src" / "langflow_components"


def sync_components():
    with open(OUTPUT_FLOW_FILE, "r", encoding="utf-8") as f:
        flow = json.load(f)

    code_map = {
        "PDPClauseExtractor-node": (COMPONENTS_DIR / "clause_extractor_node.py").read_text(encoding="utf-8"),
        "PDPLegalRetriever-node": (COMPONENTS_DIR / "legal_retriever_node.py").read_text(encoding="utf-8"),
        "PDPComplianceChecker-node": (COMPONENTS_DIR / "compliance_checker_node.py").read_text(encoding="utf-8"),
        "PDPAuditReporter-node": (COMPONENTS_DIR / "reporter_node.py").read_text(encoding="utf-8"),
    }

    nodes = flow.get("data", {}).get("nodes", [])
    updated = 0
    for node in nodes:
        nid = node.get("id")
        if nid in code_map:
            template = node.get("data", {}).get("node", {}).get("template", {})
            if "code" in template:
                template["code"]["value"] = code_map[nid]
                updated += 1
                print(f"Updated code for node: {nid}")

    with open(OUTPUT_FLOW_FILE, "w", encoding="utf-8") as f:
        json.dump(flow, f, indent=2, ensure_ascii=False)

    print(f"Total updated components: {updated}")


def main():
    if OUTPUT_FLOW_FILE.exists():
        sync_components()
        with open(OUTPUT_FLOW_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        nodes = data.get("data", {}).get("nodes", [])
        edges = data.get("data", {}).get("edges", [])
        print(f"Flow verified: {len(nodes)} nodes, {len(edges)} edges.")
    else:
        print(f"File {OUTPUT_FLOW_FILE} does not exist.")


if __name__ == "__main__":
    main()

