import * as path from 'path';
import * as vscode from 'vscode';
import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
} from 'vscode-languageclient/node';

let client: LanguageClient;

export function activate(context: vscode.ExtensionContext) {
    // Determine python path: check workspace folders first, fallback to absolute path
    let pythonPath = "/Users/ot2661/Documents/varmanager/.venv/bin/python";
    
    if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
        const workspaceFolder = vscode.workspace.workspaceFolders[0].uri.fsPath;
        const localPython = path.join(workspaceFolder, ".venv", "bin", "python");
        // You can check if fs exists, or use it directly
        pythonPath = localPython;
    }

    const serverOptions: ServerOptions = {
        run: { command: pythonPath, args: ["-m", "variable_manager", "lsp"] },
        debug: { command: pythonPath, args: ["-m", "variable_manager", "lsp"] }
    };

    const clientOptions: LanguageClientOptions = {
        documentSelector: [{ scheme: 'file', language: 'tseq' }]
    };

    client = new LanguageClient(
        'varManagerLSP',
        'Variable Manager LSP',
        serverOptions,
        clientOptions
    );

    client.start();
}

export function deactivate(): Promise<void> | undefined {
    if (!client) {
        return undefined;
    }
    return client.stop();
}
