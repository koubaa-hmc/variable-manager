import sys
import os
from typing import List
from .ontology import OntologyManager
from .manager import VariableManager

def get_default_manager() -> VariableManager:
    om = OntologyManager()
    # Load IOF Core ontology if present
    ontology_path = os.path.join(os.getcwd(), "ontologies", "iof-core.rdf")
    if os.path.exists(ontology_path):
        om.load_ontology("iof", ontology_path)
    
    vm = VariableManager(om)
    return vm

def main() -> None:
    vm = get_default_manager()
    
    args = sys.argv[1:]
    if not args:
        print("Variable Manager with Ontology Support (IOF)")
        print("Usage:")
        print("  variable-manager recommend <context> [limit]")
        print("  variable-manager search <keyword>")
        print("  variable-manager list [namespace]")
        print("  variable-manager set <namespace> <name> <value>")
        return

    command = args[0].lower()
    
    if command == "recommend":
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
        keyword = args[1] if len(args) > 1 else ""
        results = vm.ontology_manager.search_concepts(keyword)
        print(f"\nOntology search results for '{keyword}':")
        for res in results[:10]:
            print(f"  - [{res['namespace']}] {res['label']} ({res['uri']})")
            if res['description']:
                print(f"    {res['description'][:100]}...")

    elif command == "list":
        ns = args[1] if len(args) > 1 else None
        variables = vm.list_variables(ns)
        print("\nVariables:")
        print(variables)

    elif command == "set":
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

