import sys
import os
import uvicorn
from typing import List
from .ontology import OntologyManager
from .manager import VariableManager
from .init_project import initialize_project
from .lsp import run_lsp

def get_default_manager() -> VariableManager:
    om = OntologyManager()
    # Try multiple paths for ontologies
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

def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("Variable Manager with TestStand-inspired LinkML Type Palettes & Daemon API")
        print("Usage:")
        print("  variable-manager init <project_name>")
        print("  variable-manager serve [--host <host>] [--port <port>]")
        print("  variable-manager lsp")
        print("  variable-manager recommend <context> [limit]")
        print("  variable-manager search <keyword>")
        print("  variable-manager list [namespace]")
        print("  variable-manager set <namespace> <name> <value>")
        return

    command = args[0].lower()
    
    if command == "init":
        project_name = args[1] if len(args) > 1 else "electronic_test_project"
        initialize_project(project_name)

    elif command == "serve":
        host = "127.0.0.1"
        port = 8000
        for i in range(1, len(args)):
            if args[i] == "--host" and i + 1 < len(args):
                host = args[i + 1]
            elif args[i] == "--port" and i + 1 < len(args):
                port = int(args[i + 1])
        print(f"Starting Variable Manager daemon API on http://{host}:{port} ...")
        uvicorn.run("variable_manager.server:app", host=host, port=port, reload=False)

    elif command == "lsp":
        run_lsp()

    elif command == "recommend":
        vm = get_default_manager()
        context = args[1] if len(args) > 1 else "general"
        limit = int(args[2]) if len(args) > 2 else 5
        recs = vm.recommend_variables(context, limit)
        print(f"\nRecommendations for context '{context}':")
        for r in recs:
            print(f"  - Name: {r['suggested_name']} (Namespace: {r['namespace']})")
            print(f"    Concept: {r['ontology_concept']}")
            if r['description']:
                print(f"    Description: {r['description'][:100]}...")
            print()

    elif command == "search":
        vm = get_default_manager()
        keyword = args[1] if len(args) > 1 else ""
        results = vm.ontology_manager.search_concepts(keyword)
        print(f"\nOntology search results for '{keyword}':")
        for res in results[:10]:
            print(f"  - [{res['namespace']}] {res['label']} ({res['uri']})")
            if res['description']:
                print(f"    {res['description'][:100]}...")

    elif command == "list":
        vm = get_default_manager()
        ns = args[1] if len(args) > 1 else None
        variables = vm.list_variables(ns)
        print("\nVariables:")
        print(variables)

    elif command == "set":
        vm = get_default_manager()
        if len(args) < 4:
            print("Usage: variable-manager set <namespace> <name> <value>")
            return
        ns = args[1]
        name = args[2]
        val = args[3]
        vm.set_variable(ns, name, val)
        print(f"Set variable {ns}:{name} = {val}")

    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()



