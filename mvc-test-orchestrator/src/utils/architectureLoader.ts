import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";

export function loadArchitectureJson(): any | null {
    const workspaceFolders = vscode.workspace.workspaceFolders;

    if (!workspaceFolders) return null;

    const root = workspaceFolders[0].uri.fsPath;
    const filePath = path.join(root, "data", "architecture_map.json");

    if (!fs.existsSync(filePath)) return null;

    try {
        const raw = fs.readFileSync(filePath, "utf-8");
        return JSON.parse(raw);
    } catch (err) {
        console.error("Failed to read architecture_map.json", err);
        return null;
    }
}
