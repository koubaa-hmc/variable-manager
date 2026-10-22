# import pytest
from fastapi.testclient import TestClient
from variable_manager.ontology import OntologyManager
from variable_manager.manager import VariableManager
from variable_manager.types import TypeRegistry
from variable_manager.server import app

client = TestClient(app)

def test_type_registry_and_palettes():
    registry = TypeRegistry()
    # Check generics
    assert registry.get("string") is not None
    assert registry.get("number") is not None
    assert registry.get("boolean") is not None

    # Check LinkML loaded registered types
    voltage_meas_type = registry.get("VoltageMeasurement")
    assert voltage_meas_type is not None
    assert voltage_meas_type.category == "registered"
    assert voltage_meas_type.default_value == {"nominal_value": 5.0, "upper_limit": 5.25, "lower_limit": 4.75, "unit": "V"}

    # Test validation
    assert registry.validate_value("string", "hello") is True
    assert registry.validate_value("string", 123) is False
    assert registry.validate_value("VoltageMeasurement", {"nominal_value": 3.3}) is True

def test_variable_manager_namespaces_and_defaults():
    om = OntologyManager()
    vm = VariableManager(om)

    # Test setting variable with explicit value
    vm.set_variable("local", "test_var", 42, type_name="integer")
    var = vm.get_variable("local", "test_var")
    assert var is not None
    assert var["value"] == 42
    assert var["type"] == "integer"

    # Test setting variable without value (uses LinkML palette default)
    vm.set_variable("sequence_global", "vcc_test", type_name="VoltageMeasurement")
    var_meas = vm.get_variable("sequence_global", "vcc_test")
    assert var_meas is not None
    assert var_meas["value"] == {"nominal_value": 5.0, "upper_limit": 5.25, "lower_limit": 4.75, "unit": "V"}

def test_ontology_manager():
    om = OntologyManager()
    # If ontology is present, test search
    import os
    ontology_path = os.path.join(os.getcwd(), "ontologies", "iof-core.rdf")
    if os.path.exists(ontology_path):
        om.load_ontology("iof", ontology_path)
        results = om.search_concepts("process")
        assert isinstance(results, list)

def test_fastapi_server_endpoints():
    # Health check
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

    # List types
    response = client.get("/types")
    assert response.status_code == 200
    assert len(response.json()["types"]) > 0

    # Recommend variables
    response = client.get("/recommend?context=move&limit=2")
    assert response.status_code == 200
    assert "recommendations" in response.json()

    # Set and get variable via API
    set_res = client.post("/variables", json={
        "namespace": "station_globals",
        "name": "test_station",
        "value": "cell_1",
        "type": "string"
    })
    assert set_res.status_code == 200

    get_res = client.get("/variables/station_globals/test_station")
    assert get_res.status_code == 200
    assert get_res.json()["value"] == "cell_1"

def test_init_project(tmp_path):
    from variable_manager.init_project import initialize_project
    proj_dir = tmp_path / "electronic_test_sequence_project"
    initialize_project(str(proj_dir))

    assert (proj_dir / "types" / "standard_test_palette.yaml").exists()
    assert (proj_dir / "sequences" / "test_calibration_sequence.py").exists()
    assert (proj_dir / "sequences" / "test_calibration_sequence.tseq").exists()
    assert (proj_dir / "station" / "station_config.yaml").exists()
