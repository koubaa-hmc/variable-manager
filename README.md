# Variable Manager & Ontology-Backed Test Sequencing

The **Variable Manager** is a robust service designed to assist robot sequence editors during editing by providing context-aware variable recommendations, multi-namespace scope management, semantic grounding via the **Industrial Ontologies Foundry (IOF Core)**, and TestStand-inspired **LinkML Type Palettes**.

---

## Features

1. **Multi-Namespace Scopes**:
   - **`local`**: Scoped within an individual test case.
   - **`sequence_global`**: Scoped across the entire robot sequence.
   - **`station_globals`**: Defines testing sequence characteristics (such as concrete reachable devices and reachability configurations).
   - **`iof`**: Ontology-backed concepts and terms.

2. **Ontology-Backed Semantics (IOF Core)**:
   - Integrates the official Industrial Ontology Foundry (IOF) Core ontology (`ontologies/iof-core.rdf`).
   - Provides semantic search and context-aware variable recommendations (e.g. mapping editing actions like `move` or `grasp` to ontological classes).

3. **LinkML Type Palettes & Type Registry**:
   - TestStand-inspired **Type Palettes** defined in **LinkML YAML format** under `types/`.
   - Supports both generic primitives (`string`, `number`, `integer`, `boolean`, `array`, `object`) and registered domain types (`JointAngles`, `Pose`, `DeviceReference`).
   - **Automatic Defaults**: When a new variable is declared without an explicit value, the variable manager automatically populates it using the `ifabsent` default value defined in the LinkML type palette.

4. **Daemon API & IDE / LSP Integration**:
   - Runs as a FastAPI background daemon providing REST endpoints for IDE extensions and Language Server Protocol (LSP) clients.

---

## Installation & Setup

1. Initialize and sync dependencies using `uv`:
   ```bash
   uv sync
   ```

2. Start the Daemon API:
   ```bash
   uv run variable-manager serve --port 8000
   ```

3. Access Interactive API Docs (Swagger UI):
   Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.

---

## CLI Usage

- **Get Context-Aware Recommendations**:
  ```bash
  uv run variable-manager recommend move 3
  ```

- **Search Ontology Concepts**:
  ```bash
  uv run variable-manager search artifact
  ```

- **List Variables**:
  ```bash
  uv run variable-manager list
  ```

---

## API Endpoints

- `GET /health`: Server status and loaded ontologies.
- `GET /types`: List available generic and LinkML palette types.
- `GET /recommend?context=<ctx>&limit=<n>`: Context-aware variable recommendations.
- `GET /search?keyword=<kw>`: Search ontology concepts.
- `GET /variables`: List all variables across namespaces.
- `GET /variables/{namespace}/{name}`: Retrieve runtime value and metadata for execution.
- `POST /variables`: Register or declare a variable (automatically applies LinkML default values if omitted).

