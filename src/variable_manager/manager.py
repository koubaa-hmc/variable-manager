import json
import os
from typing import List, Dict, Any, Optional
from .ontology import OntologyManager

class VariableManager:
    def __init__(self, ontology_manager: OntologyManager, storage_file: str = "variables.json"):
        self.ontology_manager = ontology_manager
        self.storage_file = storage_file
        # Namespace -> Dict[variable_name, metadata]
        # Metadata includes: value, ontological_concept, description, etc.
        self.namespaces: Dict[str, Dict[str, Dict[str, Any]]] = {
            "default": {},
            "robot": {},
            "iof": {}
        }
        self.load_from_file()

    def add_namespace(self, name: str):
        if name not in self.namespaces:
            self.namespaces[name] = {}

    def set_variable(self, namespace: str, name: str, value: Any, ontological_concept: Optional[str] = None, description: Optional[str] = None):
        if namespace not in self.namespaces:
            self.add_namespace(namespace)
        
        self.namespaces[namespace][name] = {
            "value": value,
            "ontological_concept": ontological_concept or "",
            "description": description or ""
        }
        self.save_to_file()

    def get_variable(self, namespace: str, name: str) -> Optional[Dict[str, Any]]:
        if namespace in self.namespaces and name in self.namespaces[namespace]:
            return self.namespaces[namespace][name]
        return None

    def list_variables(self, namespace: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        if namespace:
            return {namespace: self.namespaces.get(namespace, {})}
        return self.namespaces

    def save_to_file(self):
        try:
            with open(self.storage_file, "w") as f:
                json.dump(self.namespaces, f, indent=2)
        except Exception as e:
            print(f"Error saving variables to {self.storage_file}: {e}")

    def load_from_file(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        for ns, vars_dict in data.items():
                            self.namespaces[ns] = vars_dict
            except Exception as e:
                print(f"Error loading variables from {self.storage_file}: {e}")

    def recommend_variables(self, context: str, limit: int = 5) -> List[Dict[str, Any]]:

        """
        Recommend variable names and semantics based on robot sequence editing context 
        and loaded ontologies (e.g. IOF core).
        """
        recommendations = []
        
        # Map common editing context keywords to ontology search terms
        context_mapping = {
            "move": ["position", "location", "trajectory", "coordinate", "motion"],
            "grasp": ["artifact", "object", "material", "gripper", "component"],
            "assembly": ["assembly", "component", "process", "product", "part"],
            "weld": ["process", "tool", "material", "equipment"],
            "inspect": ["quality", "characteristic", "feature", "sensor"],
            "start": ["event", "state", "condition"],
            "stop": ["event", "state", "condition"],
            "general": ["specification", "agent", "role", "action"]
        }

        search_terms = context_mapping.get(context.lower(), [context])
        
        seen_labels = set()
        for term in search_terms:
            concepts = self.ontology_manager.search_concepts(term)
            for concept in concepts:
                label = concept["label"]
                # Convert label to snake_case variable name
                var_name = label.strip().lower().replace(" ", "_").replace("-", "_")
                # Clean special chars
                var_name = "".join(c for c in var_name if c.isalnum() or c == '_')
                
                if var_name and var_name not in seen_labels and len(var_name) > 2:
                    seen_labels.add(var_name)
                    recommendations.append({
                        "suggested_name": var_name,
                        "namespace": concept["namespace"] if concept["namespace"] in self.namespaces else "iof",
                        "ontology_concept": label,
                        "ontology_uri": concept["uri"],
                        "description": concept["description"] or f"Derived from IOF ontology concept: {label}"
                    })
                    if len(recommendations) >= limit:
                        return recommendations

        # Fallback recommendations if ontology doesn't yield enough
        if not recommendations:
            fallback_map = {
                "move": [{"suggested_name": "target_position", "ontology_concept": "Target Location"}],
                "grasp": [{"suggested_name": "payload_object", "ontology_concept": "Material Artifact"}],
                "assembly": [{"suggested_name": "component_part", "ontology_concept": "Assembly Component"}],
            }
            defaults = fallback_map.get(context.lower(), [{"suggested_name": f"{context}_parameter", "ontology_concept": "Process Parameter"}])
            for d in defaults:
                recommendations.append({
                    "suggested_name": d["suggested_name"],
                    "namespace": "robot",
                    "ontology_concept": d["ontology_concept"],
                    "ontology_uri": "",
                    "description": f"Standard recommended variable for {context} context."
                })

        return recommendations
