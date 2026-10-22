import sys
import json
import logging
import os
from typing import Dict, Any # , List, Optional

from .ontology import OntologyManager
from .manager import VariableManager

def get_default_manager() -> VariableManager:
    om = OntologyManager()
    possible_paths = [
        os.path.join(os.getcwd(), "ontologies", "iof-core.rdf"),
        os.path.join(os.path.dirname(__file__), "..", "..", "ontologies", "iof-core.rdf"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ontologies", "iof-core.rdf"))
    ]

    ontology_path = None
    for p in possible_paths:
        if os.path.exists(p):
            ontology_path = p
            break

    if ontology_path:
        om.load_ontology("iof", ontology_path)

    vm = VariableManager(om)
    return vm

logging.basicConfig(level=logging.INFO, filename="variable_manager_lsp.log", format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("VariableManagerLSP")

class VariableManagerLSP:
    def __init__(self):
        self.vm = get_default_manager()
        self.documents: Dict[str, str] = {} # uri -> content
        self.running = True

    def run(self):
        logger.info("Starting Variable Manager LSP Server...")
        while self.running:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue

                # Handle Content-Length header if present
                if line.startswith("Content-Length:"):
                    content_length = int(line.split(":")[1].strip())
                    # Read empty line
                    sys.stdin.readline()
                    content = sys.stdin.read(content_length)
                    message = json.loads(content)
                else:
                    # Direct JSON message
                    message = json.loads(line)

                self.handle_message(message)
            except Exception as e:
                logger.error(f"Error handling message: {e}", exc_info=True)

    def send_message(self, msg: Dict[str, Any]):
        content = json.dumps(msg)
        response = f"Content-Length: {len(content)}\r\n\r\n{content}"
        sys.stdout.write(response)
        sys.stdout.flush()

    def send_response(self, req_id: Any, result: Any = None, error: Any = None):
        resp = {
            "jsonrpc": "2.0",
            "id": req_id
        }
        if error:
            resp["error"] = error
        else:
            resp["result"] = result
        self.send_message(resp)

    def send_notification(self, method: str, params: Any):
        notif = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        self.send_message(notif)

    def handle_message(self, msg: Dict[str, Any]):
        method = msg.get("method")
        msg_id = msg.get("id")
        params = msg.get("params", {})

        if not method:
            return

        logger.info(f"Received method: {method} (id: {msg_id})")

        if method == "initialize":
            self.handle_initialize(msg_id, params)
        elif method == "initialized":
            pass
        elif method == "shutdown":
            self.handle_shutdown(msg_id)
        elif method == "exit":
            self.running = False
        elif method == "textDocument/didOpen":
            self.handle_did_open(params)
        elif method == "textDocument/didChange":
            self.handle_did_change(params)
        elif method == "textDocument/completion":
            self.handle_completion(msg_id, params)
        elif method == "textDocument/hover":
            self.handle_hover(msg_id, params)
        elif method == "workspace/executeCommand":
            self.handle_execute_command(msg_id, params)
        else:
            if msg_id is not None:
                self.send_response(msg_id, error={"code": -32601, "message": f"Method {method} not found"})

    def handle_initialize(self, msg_id: Any, params: Dict[str, Any]):
        capabilities = {
            "capabilities": {
                "textDocumentSync": 1, # Full sync
                "completionProvider": {
                    "triggerCharacters": [".", "$", "_", " "]
                },
                "hoverProvider": True,
                "executeCommandProvider": {
                    "commands": [
                        "variableManager.setVariable",
                        "variableManager.listVariables",
                        "variableManager.recommendVariables"
                    ]
                }
            }
        }
        self.send_response(msg_id, capabilities)

    def handle_shutdown(self, msg_id: Any):
        self.send_response(msg_id, None)

    def handle_did_open(self, params: Dict[str, Any]):
        doc = params.get("textDocument", {})
        uri = doc.get("uri")
        text = doc.get("text", "")
        if uri:
            self.documents[uri] = text
            self.validate_document(uri, text)

    def handle_did_change(self, params: Dict[str, Any]):
        doc = params.get("textDocument", {})
        uri = doc.get("uri")
        changes = params.get("contentChanges", [])
        if uri and changes:
            text = changes[-1].get("text", "")
            self.documents[uri] = text
            self.validate_document(uri, text)

    def validate_document(self, uri: str, text: str):
        diagnostics = []
        lines = text.splitlines()

        # Check for potential undefined variable references or variable usage
        # e.g., references to variables or syntax validation against known namespaces
        all_vars = set()
        for ns_name, vars_dict in self.vm.namespaces.items():
            for vname in vars_dict.keys():
                all_vars.add(vname)
                all_vars.add(f"{ns_name}.{vname}")

        # Simple diagnostic: check if words resembling variables or known tokens are valid or flagged
        # (For demonstration, we check usage of variable lookups or unknown variables if prefixed)
        for i, line in enumerate(lines):
            if "variable_manager.get_variable" in line or "vm.get_variable" in line:
                # Example heuristic check
                pass

        self.send_notification("textDocument/publishDiagnostics", {
            "uri": uri,
            "diagnostics": diagnostics
        })

    def handle_completion(self, msg_id: Any, params: Dict[str, Any]):
        items = []

        # Add all variables from variable manager
        for ns_name, vars_dict in self.vm.namespaces.items():
            for vname, vdata in vars_dict.items():
                val = vdata.get("value")
                vtype = vdata.get("type", "string")
                desc = vdata.get("description", "")
                concept = vdata.get("ontological_concept", "")

                detail = f"[{ns_name}] {vtype} = {val}"
                documentation = f"Ontological Concept: {concept}\nDescription: {desc}" if concept or desc else f"Variable in namespace {ns_name}"

                items.append({
                    "label": vname,
                    "kind": 6, # Variable kind in LSP
                    "detail": detail,
                    "documentation": {
                        "kind": "markdown",
                        "value": documentation
                    },
                    "insertText": vname
                })
                items.append({
                    "label": f"{ns_name}.{vname}",
                    "kind": 6,
                    "detail": f"Namespaced variable [{ns_name}]",
                    "insertText": f"{ns_name}.{vname}"
                })

        # Also add ontology-based recommendations if context words match
        # Let's provide standard recommendations for robot sequence contexts (move, grasp, assembly, weld, etc.)
        contexts = ["move", "grasp", "assembly", "weld", "inspect", "start", "stop"]
        for ctx in contexts:
            recs = self.vm.recommend_variables(ctx, limit=3)
            for r in recs:
                sname = r["suggested_name"]
                items.append({
                    "label": f"rec:{sname} ({ctx})",
                    "kind": 18, # Reference / Snippet
                    "detail": f"Recommended ({r['ontology_concept']}) for {ctx}",
                    "documentation": {
                        "kind": "markdown",
                        "value": f"**Ontology Concept**: {r['ontology_concept']}\n**Description**: {r['description']}\n**URI**: {r.get('ontology_uri', '')}"
                    },
                    "insertText": sname
                })

        self.send_response(msg_id, {"isIncomplete": False, "items": items})

    def handle_hover(self, msg_id: Any, params: Dict[str, Any]):
        position = params.get("position", {})
        text_doc = params.get("textDocument", {})
        uri = text_doc.get("uri")

        if uri not in self.documents:
            self.send_response(msg_id, None)
            return

        lines = self.documents[uri].splitlines()
        line_idx = position.get("line", 0)
        char_idx = position.get("character", 0)

        if line_idx >= len(lines):
            self.send_response(msg_id, None)
            return

        line = lines[line_idx]

        # Extract word around cursor
        start = char_idx
        while start > 0 and (line[start - 1].isalnum() or line[start - 1] in "_."):
            start -= 1
        end = char_idx
        while end < len(line) and (line[end].isalnum() or line[end] in "_."):
            end += 1

        word = line[start:end]
        if not word:
            self.send_response(msg_id, None)
            return

        # Check if word is a variable or namespaced variable
        var_info = None
        ns = "default"
        vname = word

        if "." in word:
            parts = word.split(".", 1)
            ns, vname = parts[0], parts[1]
            var_info = self.vm.get_variable(ns, vname)
        else:
            # Search across all namespaces
            for ns_name, vars_dict in self.vm.namespaces.items():
                if word in vars_dict:
                    ns = ns_name
                    vname = word
                    var_info = vars_dict[word]
                    break

        if var_info:
            content = f"### Variable: `{ns}.{vname}`\n"
            content += f"- **Type**: `{var_info.get('type', 'string')}`\n"
            content += f"- **Value**: `{var_info.get('value')}`\n"
            if var_info.get('ontological_concept'):
                content += f"- **Ontological Concept**: {var_info.get('ontological_concept')}\n"
            if var_info.get('description'):
                content += f"- **Description**: {var_info.get('description')}\n"

            self.send_response(msg_id, {
                "contents": {
                    "kind": "markdown",
                    "value": content
                }
            })
        else:
            # Check if it's an ontology concept
            results = self.vm.ontology_manager.search_concepts(word)
            if results:
                res = results[0]
                content = f"### Ontology Concept: `{res['label']}`\n"
                content += f"- **Namespace**: `{res['namespace']}`\n"
                content += f"- **URI**: `{res['uri']}`\n"
                if res.get('description'):
                    content += f"- **Description**: {res['description']}\n"
                self.send_response(msg_id, {
                    "contents": {
                        "kind": "markdown",
                        "value": content
                    }
                })
            else:
                self.send_response(msg_id, None)

    def handle_execute_command(self, msg_id: Any, params: Dict[str, Any]):
        command = params.get("command")
        args = params.get("arguments", [])

        try:
            if command == "variableManager.setVariable":
                # args: [namespace, name, value, type, ontological_concept, description]
                ns = args[0] if len(args) > 0 else "default"
                name = args[1] if len(args) > 1 else "new_var"
                val = args[2] if len(args) > 2 else None
                vtype = args[3] if len(args) > 3 else "string"
                concept = args[4] if len(args) > 4 else None
                desc = args[5] if len(args) > 5 else None

                self.vm.set_variable(ns, name, val, vtype, concept, desc)
                self.send_response(msg_id, {"status": "success", "message": f"Set variable {ns}.{name}"})
            elif command == "variableManager.listVariables":
                ns = args[0] if len(args) > 0 else None
                variables = self.vm.list_variables(ns)
                self.send_response(msg_id, {"variables": variables})
            elif command == "variableManager.recommendVariables":
                ctx = args[0] if len(args) > 0 else "general"
                limit = int(args[1]) if len(args) > 1 else 5
                recs = self.vm.recommend_variables(ctx, limit)
                self.send_response(msg_id, {"recommendations": recs})
            else:
                self.send_response(msg_id, error={"code": -32601, "message": f"Unknown command {command}"})
        except Exception as e:
            self.send_response(msg_id, error={"code": -32603, "message": str(e)})

def run_lsp():
    server = VariableManagerLSP()
    server.run()
