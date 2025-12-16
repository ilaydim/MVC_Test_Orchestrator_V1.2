// mvc-test-orchestrator/src/extension.ts

import * as vscode from "vscode";
import * as path from "path";
import { exec } from "child_process";
import * as fs from "fs";
// import { MVCTreeProvider } from "./tree/MVCTreeProvider"; // <-- KALDIRILDI


// --- YARDIMCI FONKSİYON: Python Komutunu Çalıştırır ---
async function runPythonCommand(
    workspaceRoot: string, 
    commandName: string, 
    args: string, 
    outputFilename: string // Bu hala zorunlu ama sadece isimlendirme amaçlı
) {
    const outputPath = path.join(workspaceRoot, "data", outputFilename);

    // Python env detection (aynı kaldı)
    let pythonExec = "python";
    const venvWin = path.join(workspaceRoot, ".venv", "Scripts", "python.exe");
    const venvUnix = path.join(workspaceRoot, ".venv", "bin", "python");

    if (fs.existsSync(venvWin)) pythonExec = `"${venvWin}"`;
    else if (fs.existsSync(venvUnix)) pythonExec = `"${venvUnix}"`;

    let outputArg = "";
    // KRİTİK DÜZELTME: Sadece Extraction komutları --output gerektirir.
    if (commandName === "create-srs" || commandName === "index-srs") {
        outputArg = `--output "${outputPath}"`;
    }

    const pythonCmd = `${pythonExec} -m src.cli.mvc_arch_cli ${commandName} ${args} ${outputArg}`;
    await vscode.window.withProgress(
        {
            location: vscode.ProgressLocation.Notification,
            title: `Running MVC Orchestrator (${commandName})...`,
            cancellable: false,
        },
        () =>
            new Promise<void>((resolve) => {
                // PYTHONIOENCODING=utf-8 eklenerek I/O hatası çözülür.
                const proc = exec(pythonCmd, { 
                    cwd: workspaceRoot,
                    env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
                });

                proc.stdout?.on("data", (d) => console.log(`[${commandName} stdout]`, d.toString()));
                proc.stderr?.on("data", (d) => console.error(`[${commandName} stderr]`, d.toString()));

                proc.on("close", (code) => {
                    if (code === 0) {
                        
                        // ÖNEMLİ DÜZELTME: Hata veren refresh komutunu kaldırdık.
                        // vscode.commands.executeCommand("mvc-test-orchestrator.refreshTree"); 
                        
                        // YENİ DÜZELTME: Komuta göre doğru başarı mesajını göster.
                        let successMessage = `Command '${commandName}' executed successfully.`;
                        
                        if (commandName === "create-srs") {
                            successMessage = `SRS created → data/srs_document.txt\nNext: Run "Extract Architecture from Existing SRS" to generate architecture.`;
                        } else if (commandName === "index-srs") {
                            successMessage = `Architecture extracted → data/architecture_map.json`;
                        } else if (commandName === "scaffold") {
                            successMessage = "Scaffold created successfully in /scaffolds/mvc_skeleton/";
                        } else if (commandName === "run-code") {
                            successMessage = "Code generation complete! Check /scaffolds/mvc_skeleton/";
                        } else if (commandName === "run-audit") {
                            successMessage = "Audit completed. Check data/final_audit_report.json";
                        }
                        
                        vscode.window.showInformationMessage(successMessage);
                    } else {
                        vscode.window.showErrorMessage(
                            `Python CLI failed (exit ${code}). Check Developer Console for details.`
                        );
                    }
                    resolve();
                });
            })
    );
}


export function activate(context: vscode.ExtensionContext) {
    console.log("MVC Test Orchestrator VSCode extension activated.");

    const workspaceFolders = vscode.workspace.workspaceFolders;
    const workspaceRoot = workspaceFolders?.[0]?.uri?.fsPath;

    if (!workspaceRoot) {
        return;
    }


    // ------------------------------------------------------
    // 1a) CREATE SRS ONLY (from user idea)
    // ------------------------------------------------------
    const createCmd = vscode.commands.registerCommand(
        "mvc-test-orchestrator.createSrsAndExtract",
        async () => {
            const userIdea = await vscode.window.showInputBox({
                prompt: "Enter the high-level software idea:",
                placeHolder: "E.g., A simple e-commerce site for selling books.",
            });
            
            if (!userIdea) return;
            
            const safeUserIdea = JSON.stringify(userIdea);
            const args = `--user-idea ${safeUserIdea}`;

            // YENİ: create-srs artık sadece SRS üretiyor, output SRS dosyası olmalı
            await runPythonCommand(workspaceRoot, "create-srs", args, "srs_document.txt");
        }
    );

    // ------------------------------------------------------
    // 1b) EXTRACT ARCHITECTURE FROM SRS (index-srs)
    // ------------------------------------------------------
    const indexCmd = vscode.commands.registerCommand(
        "mvc-test-orchestrator.indexSrsAndExtract",
        async () => {
            // Önce kullanıcıya seçenek sun: Az önce oluşturulan SRS mi, yoksa dosya seçimi mi?
            const defaultSrsPath = path.join(workspaceRoot, "data", "srs_document.txt");
            const defaultSrsExists = fs.existsSync(defaultSrsPath);
            
            let srsPath: string | undefined;
            
            if (defaultSrsExists) {
                // Quick pick ile seçenek sun
                const choice = await vscode.window.showQuickPick([
                    {
                        label: "$(file-text) Use recently created SRS",
                        description: `data/srs_document.txt`,
                        detail: "Use the SRS file created in Step 1a",
                        value: "default"
                    },
                    {
                        label: "$(folder-opened) Select SRS file from disk",
                        description: "Choose a different .txt or .pdf file",
                        detail: "Browse and select any SRS file",
                        value: "browse"
                    }
                ], {
                    placeHolder: "How do you want to select the SRS file?",
                    ignoreFocusOut: true
                });
                
                if (!choice) return; // Kullanıcı iptal etti
                
                if (choice.value === "default") {
                    srsPath = defaultSrsPath;
                } else {
                    // Dosya seçim dialogunu aç
                    const picked = await vscode.window.showOpenDialog({
                        title: "Select Existing SRS (.txt, .pdf) File",
                        canSelectMany: false,
                        filters: { 
                            "SRS Files": ["txt", "pdf"],
                            "All Files": ["*"]
                        },
                        defaultUri: vscode.Uri.file(path.join(workspaceRoot, "data")),
                    });
                    
                    if (!picked || picked.length === 0) return;
                    srsPath = picked[0].fsPath;
                }
            } else {
                // Default SRS yoksa direkt dosya seçimi yap
                const picked = await vscode.window.showOpenDialog({
                    title: "Select Existing SRS (.txt, .pdf) File",
                    canSelectMany: false,
                    filters: { 
                        "SRS Files": ["txt", "pdf"],
                        "All Files": ["*"]
                    },
                    defaultUri: vscode.Uri.file(path.join(workspaceRoot, "data")),
                });
                
                if (!picked || picked.length === 0) return;
                srsPath = picked[0].fsPath;
            }
            
            if (!srsPath) return;
            
            // Dosyanın gerçekten var olduğunu kontrol et
            if (!fs.existsSync(srsPath)) {
                vscode.window.showErrorMessage(`SRS file not found: ${srsPath}`);
                return;
            }
            
            const safeSrsPath = JSON.stringify(srsPath);
            const args = `--srs-path ${safeSrsPath}`;
            
            // index-srs mimari çıkarır ve architecture_map.json oluşturur
            await runPythonCommand(workspaceRoot, "index-srs", args, "architecture_map.json");
        }
    );

    context.subscriptions.push(createCmd, indexCmd);


    // ------------------------------------------------------
    // 2) Generate Scaffold Command
    // ------------------------------------------------------
    const scaffoldCmd = vscode.commands.registerCommand(
        "mvc-test-orchestrator.generateScaffold",
        async () => {
            const archPath = path.join(workspaceRoot, "data", "architecture_map.json");

            if (!fs.existsSync(archPath)) {
                vscode.window.showErrorMessage(
                    "architecture_map.json not found. Run an Extract command first."
                );
                return;
            }

            let pythonExec = "python";
            const venvWin = path.join(workspaceRoot, ".venv", "Scripts", "python.exe");
            const venvUnix = path.join(workspaceRoot, ".venv", "bin", "python");

            if (fs.existsSync(venvWin)) pythonExec = `"${venvWin}"`;
            else if (fs.existsSync(venvUnix)) pythonExec = `"${venvUnix}"`;

            // Scaffold komutu --output almadığı için doğrudan çağrılır
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
    // 3) Run Code Command
    // ------------------------------------------------------
    const codeCmd = vscode.commands.registerCommand(
        "mvc-test-orchestrator.runCode",
        async () => {
            const args = ""; 
            await runPythonCommand(workspaceRoot, "run-code", args, "code_generation_log.txt");
        }
    );

    // ------------------------------------------------------
    // 4) Run Audit Command
    // ------------------------------------------------------
    const auditCmd = vscode.commands.registerCommand(
        "mvc-test-orchestrator.runAudit",
        async () => {
            const archPath = path.join(workspaceRoot, "data", "architecture_map.json");

            if (!fs.existsSync(archPath)) {
                vscode.window.showErrorMessage(
                    "architecture_map.json not found. Run an Extract command first."
                );
                return;
            }

            const safeArchPath = JSON.stringify(archPath);
            const args = `--arch-path ${safeArchPath}`;

            await runPythonCommand(workspaceRoot, "run-audit", args, "audit_result.txt");
        }
    );
    
    context.subscriptions.push(auditCmd, codeCmd);
    
    // YENİ EK: mvcTree ve refreshTree komutları kaldırıldı.
    // RefreshTree komutunun çağrılmasına gerek kalmadı.
}

export function deactivate() {}