from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel
from typing import Optional, Any, Dict, List
import os

from .ontology import OntologyManager
from .manager import VariableManager

app = FastAPI(
    title="Variable Manager Daemon",
    description="Ontology-backed multi-namespace variable manager for robot sequence editors and LSP integration",
    version="0.1.0"
)

# Initialize global managers
ontology_manager = OntologyManager()

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
    ontology_manager.load_ontology("iof", ontology_path)

variable_manager = VariableManager(ontology_manager)

class VariableSetRequest(BaseModel):
    namespace: str = "default"
    name: str
    value: Any
    ontological_concept: Optional[str] = None
    description: Optional[str] = None

@app.get("/health")
def health_check():
    return {"status": "healthy", "loaded_ontologies": list(ontology_manager.graphs.keys())}

@app.get("/recommend")
def recommend_variables(context: str = Query(..., description="Editing context (e.g., move, grasp, assembly)"), limit: int = Query(5, description="Max recommendations")):
    recs = variable_manager.recommend_variables(context, limit)
    return {"context": context, "recommendations": recs}

@app.get("/search")
def search_ontology(keyword: str = Query(..., description="Keyword to search in ontology concepts")):
    results = ontology_manager.search_concepts(keyword)
    return {"keyword": keyword, "results": results}

@app.get("/variables")
def list_variables(namespace: Optional[str] = Query(None, description="Optional namespace filter")):
    return {"variables": variable_manager.list_variables(namespace)}

@app.get("/variables/{namespace}/{name}")
def get_variable_value(namespace: str, name: str):
    var = variable_manager.get_variable(namespace, name)
    if not var:
        raise HTTPException(status_code=404, detail=f"Variable '{name}' in namespace '{namespace}' not found")
    return {"namespace": namespace, "name": name, **var}

@app.post("/variables")
def set_variable(req: VariableSetRequest):
    variable_manager.set_variable(req.namespace, req.name, req.value, req.ontological_concept, req.description)
    return {"status": "success", "namespace": req.namespace, "name": req.name, "value": req.value}

