import os
from rdflib import Graph, RDF, RDFS, OWL, SKOS
from typing import List, Dict, Any, Optional

class OntologyManager:
    def __init__(self):
        self.graphs: Dict[str, Graph] = {}

    def load_ontology(self, name: str, filepath: str, format: Optional[str] = None) -> Graph:
        g = Graph()
        if os.path.exists(filepath):
            # Infer format if not given
            if not format:
                if filepath.endswith('.rdf') or filepath.endswith('.xml'):
                    format = 'xml'
                elif filepath.endswith('.ttl'):
                    format = 'turtle'
                elif filepath.endswith('.owl'):
                    format = 'xml'
            g.parse(filepath, format=format)
            self.graphs[name] = g
        return g

    def search_concepts(self, keyword: str, namespace: Optional[str] = None) -> List[Dict[str, str]]:
        results = []
        graphs_to_search = {namespace: self.graphs[namespace]} if namespace and namespace in self.graphs else self.graphs

        keyword_lower = keyword.lower()
        for ns_name, g in graphs_to_search.items():
            # Query classes with rdfs:label or local name matching keyword
            query = """
            SELECT DISTINCT ?cls ?label ?comment WHERE {
                ?cls a owl:Class .
                OPTIONAL { ?cls rdfs:label ?label . }
                OPTIONAL { ?cls rdfs:comment ?comment . }
            }
            """
            for row in g.query(query):
                class_uri = str(row.cls)
                label = str(row.label) if row.label else class_uri.split('/')[-1].split('#')[-1]
                comment = str(row.comment) if row.comment else ""
                
                if keyword_lower in label.lower() or keyword_lower in class_uri.lower() or keyword_lower in comment.lower():
                    results.append({
                        "namespace": ns_name,
                        "uri": class_uri,
                        "label": label,
                        "description": comment
                    })
        return results

    def get_ontology_summary(self, name: str) -> Dict[str, Any]:
        if name not in self.graphs:
            return {}
        g = self.graphs[name]
        class_count = len(list(g.subjects(RDF.type, OWL.Class)))
        return {
            "name": name,
            "classes_count": class_count,
            "triples_count": len(g)
        }
