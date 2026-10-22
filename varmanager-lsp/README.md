# Variable Manager LSP for VS Code

This VS Code extension connects `.tseq` files to the [Variable Manager](../README.md) language server. TSEQ is a Robot Framework-based sequence format with additional ontology-specific terms. The extension provides variable and ontology-aware completions and hover information while editing.

## Features

- **Completions** for variables known to the language server, including namespace-qualified names such as `local.my_variable`.
- **Ontology-based suggestions** for common robot-sequence contexts, including `move`, `grasp`, `assembly`, and `inspect`.
- **Hover information** for known variables and ontology concepts.

The server currently keeps variables in memory for the lifetime of the language-server process. It does not yet provide document diagnostics.

## Requirements

- Visual Studio Code `1.140.0` or later.
- Python `3.12` or later.
- [`uv`](https://docs.astral.sh/uv/) to install the Variable Manager's Python dependencies.
- Node.js and npm to build and run this extension from source.
- macOS or Linux. The extension currently expects the workspace interpreter at `.venv/bin/python`; Windows virtual-environment paths are not supported yet.

## Use the extension from source

1. Clone the Variable Manager repository and open its **repository root** as your VS Code workspace. The extension looks for the Python environment in `.venv` under the first workspace folder.
2. From the repository root, install the Python dependencies:

   ```bash
   uv sync
   ```

   This creates the `.venv` that the extension uses to start the language server.

3. In a terminal, go to the `varmanager-lsp` directory, install the extension dependencies, and compile it:

   ```bash
   cd varmanager-lsp
   npm install
   npm run compile
   ```

4. Open the `varmanager-lsp` folder itself in a VS Code window. In **Run and Debug**, select **Run Extension** and click the green start button. This runs the compile task and opens an Extension Development Host with the Variable Manager repository root as its workspace. You can also use **Run > Start Debugging** or press `F5` (on some Mac keyboards, use `Fn+F5`).
5. In the new window, open a `.tseq` file. VS Code associates the `.tseq` extension with the TSEQ language ID, which activates this extension's language client. Type to request completions, or hover over a known variable or ontology concept to see its details.

The extension starts the server with `python -m variable_manager lsp`. You can also run that command directly from the repository root to start the language server over standard input/output; for editor integration, use a compatible LSP client.

## Troubleshooting

- **The server does not start:** Ensure you opened the Variable Manager repository root (not only the `varmanager-lsp` subdirectory) and ran `uv sync` there. The extension expects `.venv/bin/python` in the first workspace folder.
- **No Variable Manager completions appear:** The server starts with an in-memory variable manager, so variables set elsewhere are not automatically loaded into it. Completion suggestions also include ontology-based recommendations.

## Development

Run `npm run compile` to type-check, lint, and build the extension. Press `F5` to test it in an Extension Development Host.
