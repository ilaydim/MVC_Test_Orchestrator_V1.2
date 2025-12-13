// mvc-test-orchestrator/src/extension.ts

import * as vscode from "vscode";
import * as path from "path";
import { exec } from "child_process";
import * as fs from "fs";
import { MVCTreeProvider } from "./tree/MVCTreeProvider";

export function activate(context: vscode.ExtensionContext) {
    console.log("MVC Test Orchestrator VSCode extension activated.");

    // ------------------------------------------------------
    // 1) Extract MVC Architecture Command (GÜNCELLENDİ)
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

            // YENİ: Kullanıcıdan Fikir (User Idea) al (PDF seçme kaldırıldı)
            const userIdea = await vscode.window.showInputBox({
                prompt: "Lütfen yazılımınızın temel fikrini buraya girin (Örn: Bir E-ticaret platformu).",
                placeHolder: "Kullanıcı fikri",
            });

            if (!userIdea) return;
            
            // Çıktı yolu
            const outputPath = path.join(workspaceRoot, "data", "architecture_map.json");

            // Python env detection (Aynı kaldı)
            let pythonExec = "python";
            const venvWin = path.join(workspaceRoot, ".venv", "Scripts", "python.exe");
            const venvUnix = path.join(workspaceRoot, ".venv", "bin", "python");

            if (fs.existsSync(venvWin)) pythonExec = `"${venvWin}"`;
            else if (fs.existsSync(venvUnix)) pythonExec = `"${venvUnix}"`;

            // 1. Türkçe Karakterleri ve Güvenli Olmayan Karakterleri Geçici Olarak URL-Encoded yapalım (Opsiyonel ama önerilir)
            const encodedIdea = encodeURIComponent(userIdea);
            const encodedOutput = encodeURIComponent(outputPath); 

            // 2. Python Komutunu oluştururken, Python CLI'nın bu kodları alabilmesi için
            // argümanları tırnak içine alıyoruz.
            // Ayrıca, -m ile başlayan komutu, Windows'un tek bir dize olarak işlemesi için
            // tüm komutu tek bir çift tırnak içine alabiliriz. Ancak bu bazen karışır.

            // Daha güvenli yaklaşım: userIdea argümanını tek tırnakla sarmak.
            const pythonCmd = `${pythonExec} -m src.cli.mvc_arch_cli extract --user-idea '${encodedIdea}' --output '${encodedOutput}'`;

            await vscode.window.withProgress(
                {
                    location: vscode.ProgressLocation.Notification,
                    title: "Extracting MVC Architecture...",
                    cancellable: false,
                },
                () =>
                    new Promise<void>((resolve) => {
                        const proc = exec(pythonCmd, { 
                            cwd: workspaceRoot,
                            // Python'a çıktı için UTF-8 kullanmasını söyler
                            env: { ...process.env, PYTHONIOENCODING: 'utf-8' } 
                        });
                        
                        // HATA YAKALAMAYI GÜÇLENDİR: stderr çıktısını logla
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
                                    `Python CLI failed (exit ${code}). Detaylar için Developer Console'u kontrol edin.`
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
    // 2) Generate Scaffold Command (Aynı kaldı)
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
    // 3) Register Single Tree Provider (Aynı kaldı)
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