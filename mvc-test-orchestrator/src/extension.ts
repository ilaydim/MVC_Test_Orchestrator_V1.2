// mvc-test-orchestrator/src/extension.ts

import * as vscode from "vscode";
import * as path from "path";
import { exec } from "child_process";
import * as fs from "fs";
import { MVCTreeProvider } from "./tree/MVCTreeProvider";

export function activate(context: vscode.ExtensionContext) {
    console.log("MVC Test Orchestrator VSCode extension activated.");

    // ------------------------------------------------------
    // 1) Extract MVC Architecture Command
    // ------------------------------------------------------
    const extractCmd = vscode.commands.registerCommand(
        "mvc-test-orchestrator.extractArchitectureFromSRS",
        async () => {
            const workspaceFolders = vscode.workspace.workspaceFolders;
            if (!workspaceFolders || workspaceFolders.length === 0) {
                vscode.window.showErrorMessage(
                    "Önce Python backend projesini workspace olarak açmalısın!"
                );
                return;
            }

            const workspaceRoot = workspaceFolders[0].uri.fsPath;

            // SRS PDF seçtir
            const picked = await vscode.window.showOpenDialog({
                title: "SRS PDF seç",
                canSelectMany: false,
                filters: { "PDF Files": ["pdf"] },
                defaultUri: vscode.Uri.file(path.join(workspaceRoot, "data")),
            });

            if (!picked || picked.length === 0) return;

            const srsPath = picked[0].fsPath;
            const outputPath = path.join(workspaceRoot, "data", "architecture_map.json");

            // Python env detection
            let pythonExec = "python";
            const venvWin = path.join(workspaceRoot, ".venv", "Scripts", "python.exe");
            const venvUnix = path.join(workspaceRoot, ".venv", "bin", "python");

            if (fs.existsSync(venvWin)) pythonExec = `"${venvWin}"`;
            else if (fs.existsSync(venvUnix)) pythonExec = `"${venvUnix}"`;

            const pythonCmd = `${pythonExec} -m src.cli.mvc_arch_cli extract --srs-path "${srsPath}" --output "${outputPath}"`;

            // Progress bar
            await vscode.window.withProgress(
                {
                    location: vscode.ProgressLocation.Notification,
                    title: "Extracting MVC Architecture...",
                    cancellable: false,
                },
                () =>
                    new Promise<void>((resolve) => {
                        const proc = exec(pythonCmd, { cwd: workspaceRoot });

                        proc.stdout?.on("data", (d) => console.log("[extract stdout]", d.toString()));
                        proc.stderr?.on("data", (d) => console.error("[extract stderr]", d.toString()));

                        proc.on("close", (code) => {
                            if (code === 0) {
                                vscode.commands.executeCommand("mvc-test-orchestrator.refreshTree");
                                vscode.window.showInformationMessage(
                                    `Architecture extracted → ${path.relative(workspaceRoot, outputPath)}`
                                );
                            } else {
                                vscode.window.showErrorMessage(
                                    `Python CLI failed (exit ${code})`
                                );
                            }
                            resolve();
                        });
                    })
            );
        }
    );

    context.subscriptions.push(extractCmd);

    // ------------------------------------------------------
    // 2) Generate Scaffold Command
    // ------------------------------------------------------
    const scaffoldCmd = vscode.commands.registerCommand(
        "mvc-test-orchestrator.generateScaffold",
        async () => {
            const workspaceFolders = vscode.workspace.workspaceFolders;
            if (!workspaceFolders || workspaceFolders.length === 0) {
                vscode.window.showErrorMessage("Workspace bulunamadı.");
                return;
            }

            const workspaceRoot = workspaceFolders[0].uri.fsPath;
            const archPath = path.join(workspaceRoot, "data", "architecture_map.json");

            if (!fs.existsSync(archPath)) {
                vscode.window.showErrorMessage(
                    "architecture_map.json bulunamadı. Önce Extract komutunu çalıştır."
                );
                return;
            }

            let pythonExec = "python";
            const venvWin = path.join(workspaceRoot, ".venv", "Scripts", "python.exe");
            const venvUnix = path.join(workspaceRoot, ".venv", "bin", "python");

            if (fs.existsSync(venvWin)) pythonExec = `"${venvWin}"`;
            else if (fs.existsSync(venvUnix)) pythonExec = `"${venvUnix}"`;

            const cmd = `${pythonExec} -m src.cli.mvc_arch_cli scaffold --arch-path "${archPath}"`;

            await vscode.window.withProgress(
                {
                    location: vscode.ProgressLocation.Notification,
                    title: "Generating Scaffold...",
                    cancellable: false,
                },
                () =>
                    new Promise<void>((resolve) => {
                        const proc = exec(cmd, { cwd: workspaceRoot });

                        proc.stdout?.on("data", (d) => console.log("[scaffold stdout]", d.toString()));
                        proc.stderr?.on("data", (d) => console.error("[scaffold stderr]", d.toString()));

                        proc.on("close", (code) => {
                            if (code === 0) {
                                vscode.window.showInformationMessage(
                                    "Scaffold generated under /scaffolds/mvc_skeleton/"
                                );
                            } else {
                                vscode.window.showErrorMessage(
                                    `Scaffold failed (exit ${code})`
                                );
                            }
                            resolve();
                        });
                    })
            );
        }
    );

    context.subscriptions.push(scaffoldCmd);

    // ------------------------------------------------------
    // 3) Register Single Tree Provider
    // ------------------------------------------------------
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0].uri.fsPath ?? "";
    const mvcTree = new MVCTreeProvider(workspaceRoot);

    vscode.window.registerTreeDataProvider("mvcArchitectureView", mvcTree);

    // Refresh command
    context.subscriptions.push(
        vscode.commands.registerCommand("mvc-test-orchestrator.refreshTree", () => {
            mvcTree.refresh();
        })
    );
}

export function deactivate() {}
