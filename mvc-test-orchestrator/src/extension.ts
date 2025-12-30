// mvc-test-orchestrator/src/extension.ts

import * as vscode from "vscode";
import * as path from "path";
import { exec } from "child_process";
import * as fs from "fs";


// ============================================================
// SAFE ERROR LOGGING (Circular JSON önleme)
// ============================================================
function safeErrorToString(error: any): string {
    /**
     * Error objesini güvenli bir şekilde string'e çevirir.
     * Circular reference hatalarını önler.
     */
    if (!error) {
        return "Unknown error (null/undefined)";
    }
    
    // Eğer error bir string ise direkt döndür
    if (typeof error === "string") {
        return error;
    }
    
    // Error objesinden güvenli bilgileri al
    const errorInfo: any = {};
    
    if (error.message) errorInfo.message = error.message;
    if (error.name) errorInfo.name = error.name;
    if (error.code) errorInfo.code = error.code;
    if (error.stack && typeof error.stack === "string") {
        // Stack trace'i ilk 500 karakterle sınırla
        errorInfo.stack = error.stack.substring(0, 500);
    }
    
    try {
        return JSON.stringify(errorInfo, null, 2);
    } catch (jsonError) {
        // JSON.stringify bile başarısız olduysa sadece error.message döndür
        return error.message || String(error);
    }
}


// --- YARDIMCI FONKSİYON: Python Komutunu Çalıştırır ---
async function runPythonCommand(
    workspaceRoot: string, 
    commandName: string, 
    args: string, 
    outputFilename: string
) {
    try {
    const outputPath = path.join(workspaceRoot, "data", outputFilename);

    // Python env detection (aynı kaldı)
    let pythonExec = "python";
    const venvWin = path.join(workspaceRoot, ".venv", "Scripts", "python.exe");
    const venvUnix = path.join(workspaceRoot, ".venv", "bin", "python");

    if (fs.existsSync(venvWin)) pythonExec = `"${venvWin}"`;
    else if (fs.existsSync(venvUnix)) pythonExec = `"${venvUnix}"`;

    let outputArg = "";
    if (commandName === "create-srs" || commandName === "index-srs") {
        outputArg = `--output "${outputPath}"`;
    }

    const pythonCmd = `${pythonExec} -m src.cli.mvc_arch_cli ${commandName} ${args} ${outputArg}`;
    // Only show progress for long-running commands
    const showProgress = commandName === "extract" || commandName === "create-srs" || commandName === "generate-code";
    
    const runCommand = () => new Promise<void>((resolve, reject) => {
        try {
            // PYTHONIOENCODING=utf-8 eklenerek I/O hatası çözülür.
            const proc = exec(pythonCmd, { 
                cwd: workspaceRoot,
                env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
                // Timeout ayarları (120 saniye for long operations)
                timeout: commandName === "generate-code" ? 300000 : 120000, // 5 min for generate-code, 2 min for others
                maxBuffer: 1024 * 1024 * 10 // 10MB buffer
            }, (error) => {
                // Only log real errors, not expected ones (timeout is handled separately)
                if (error) {
                    const errorCode = String(error.code || '');
                    const errorSignal = String(error.signal || '');
                    if (errorCode !== 'ETIMEDOUT' && errorSignal !== 'SIGTERM') {
                        // Log to output channel only, not console
                        if (outputChannel) {
                            outputChannel.appendLine(`[${commandName}] Process error: ${safeErrorToString(error)}`);
                        }
                    }
                }
            });

            // Collect all output (stdout + stderr) for error reporting
            let allOutput = "";
            let allErrors = "";
            
            proc.stdout?.on("data", (d) => {
                const output = d.toString();
                allOutput += output;
                // Only log to output channel, not console (reduces noise)
                if (outputChannel) {
                    outputChannel.appendLine(`[${commandName}] ${output.trim()}`);
                }
            });
            
            proc.stderr?.on("data", (d) => {
                const errorOutput = d.toString();
                // Filter out common non-error messages
                const trimmed = errorOutput.trim();
                if (trimmed && !trimmed.match(/^\d+$/)) { // Ignore single numbers (like "2")
                    allErrors += errorOutput;
                    // Only log to output channel, not console
                    if (outputChannel) {
                        outputChannel.appendLine(`[${commandName} ERROR] ${errorOutput.trim()}`);
                    }
                }
            });

            proc.on("close", (code) => {
                if (code === 0) {
                    // Don't show notification for generate-code (extension handles it in chat)
                    if (commandName === "generate-code") {
                        // Silent - extension will show result in chat
                    } else if (commandName === "create-srs") {
                        vscode.window.showInformationMessage(`SRS created → data/srs_document.txt\nNext: Run "Extract Architecture" to generate architecture.`);
                    } else if (commandName === "extract" || commandName === "index-srs") {
                        vscode.window.showInformationMessage(`Architecture extracted → data/architecture_map.json`);
                    } else if (commandName === "scaffold") {
                        vscode.window.showInformationMessage("Scaffold created successfully in /scaffolds/mvc_skeleton/");
                    } else if (commandName === "audit" || commandName === "run-audit") {
                        vscode.window.showInformationMessage("Audit completed. Check data/final_audit_report.json");
                    } else if (commandName === "run-fix") {
                        // Silent - extension will show result in chat
                    }
                    resolve();
                } else {
                    // Only show errors for real failures (not null/timeout which might be handled)
                    const hasRealError = allErrors.trim().length > 0 && !allErrors.trim().match(/^\d+$/);
                    const exitCode = code ?? 'unknown';
                    
                    if (hasRealError) {
                        // Log to output channel only (not console)
                        if (outputChannel) {
                            outputChannel.appendLine(`\n========== COMMAND FAILED (exit ${exitCode}) ==========`);
                            if (allOutput.trim()) {
                                outputChannel.appendLine(`STDOUT:\n${allOutput}`);
                            }
                            if (allErrors.trim()) {
                                outputChannel.appendLine(`STDERR:\n${allErrors}`);
                            }
                            outputChannel.appendLine(`==========================================\n`);
                        }
                        
                        // Only show error message for non-timeout errors
                        if (code !== null && code !== undefined) {
                            vscode.window.showErrorMessage(
                                `Python CLI failed (exit ${code}). Check "MVC Orchestrator" output panel for details.`,
                                "Show Output"
                            ).then(selection => {
                                if (selection === "Show Output" && outputChannel) {
                                    outputChannel.show(true);
                                }
                            });
                        }
                    }
                    
                    resolve(); // Always resolve to continue pipeline
                }
            });
            
            proc.on("error", (err) => {
                // Only log real spawn errors to output channel
                if (outputChannel) {
                    outputChannel.appendLine(`[${commandName}] Process spawn error: ${safeErrorToString(err)}`);
                }
                vscode.window.showErrorMessage(`Failed to start Python process: ${err.message}`);
                resolve();
            });
        } catch (execError) {
            // Only log to output channel
            if (outputChannel) {
                outputChannel.appendLine(`[${commandName}] Exec error: ${safeErrorToString(execError)}`);
            }
            reject(execError);
        }
    });

    if (showProgress) {
        await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: `Running MVC Orchestrator (${commandName})...`,
                cancellable: false,
            },
            () => runCommand()
        );
    } else {
        await runCommand();
    }
    } catch (outerError) {
        console.error(`[runPythonCommand] Outer error:`, safeErrorToString(outerError));
        vscode.window.showErrorMessage(`Command failed: ${outerError instanceof Error ? outerError.message : String(outerError)}`);
    }
}


// Global Output Channel for Python stderr/stdout
let outputChannel: vscode.OutputChannel | null = null;

export function activate(context: vscode.ExtensionContext) {
    console.log("MVC Test Orchestrator VSCode extension activated.");

    // Create Output Channel for Python logs
    outputChannel = vscode.window.createOutputChannel("MVC Orchestrator");
    context.subscriptions.push(outputChannel);

    const workspaceFolders = vscode.workspace.workspaceFolders;
    const workspaceRoot = workspaceFolders?.[0]?.uri?.fsPath;

    if (!workspaceRoot) {
        return;
    }

    // ============================================================
    // COPILOT CHAT PARTICIPANT - Slash Commands Support
    // ============================================================
    const mvcChatParticipant = vscode.chat.createChatParticipant(
        "mvc-test-orchestrator.mvc",
        async (request, context, stream, token) => {
            const command = request.command;
            const userMessage = request.prompt;

            try {
                if (command === "create-srs") {
                    stream.markdown(`## 📝 SRS Creation - Interactive Mode\n\n`);
                    stream.markdown(`**Your Initial Idea**: ${userMessage}\n\n`);
                    
                    // Step 1: Ask clarification questions
                    stream.markdown(`**🤔 Clarification Phase**\n\n`);
                    stream.markdown(`Please answer these questions to create a better SRS:\n\n`);
                    
                    // === SORU 1: Platform ===
                    stream.markdown(`\n**Question 1/5: On which platform should the application run?**\n\n`);
                    stream.markdown(`Possible answers:\n`);
                    stream.markdown(`- (A) Web application\n`);
                    stream.markdown(`- (B) Mobile app (iOS)\n`);
                    stream.markdown(`- (C) Mobile app (Android)\n`);
                    stream.markdown(`- (D) Desktop app (Windows/Mac)\n`);
                    stream.markdown(`- (E) Multi-platform\n\n`);
                    stream.markdown(`*Recommended: A (most accessible)*\n\n`);
                    
                    const q1 = await vscode.window.showQuickPick([
                        { label: '(A) Web application', description: 'Recommended: Most accessible' },
                        { label: '(B) Mobile app (iOS)', description: 'Native iOS' },
                        { label: '(C) Mobile app (Android)', description: 'Native Android' },
                        { label: '(D) Desktop app (Windows/Mac)', description: 'Desktop native' },
                        { label: '(E) Multi-platform', description: 'All platforms' }
                    ], {
                        placeHolder: 'Select platform',
                        ignoreFocusOut: true
                    });
                    
                    if (!q1) {
                        stream.markdown(`❌ Cancelled`);
                        return {};
                    }
                    
                    // === SORU 2: User Types ===
                    stream.markdown(`\n**Question 2/5: Who are the main users?**\n\n`);
                    stream.markdown(`Possible answers:\n`);
                    stream.markdown(`- (A) End users/Customers\n`);
                    stream.markdown(`- (B) Administrators\n`);
                    stream.markdown(`- (C) Content managers\n`);
                    stream.markdown(`- (D) Guests (no login)\n\n`);
                    stream.markdown(`*Recommended: A + B*\n\n`);
                    
                    const q2 = await vscode.window.showQuickPick([
                        { label: '(A) End users/Customers', picked: true },
                        { label: '(B) Administrators', picked: true },
                        { label: '(C) Content managers' },
                        { label: '(D) Guests (no login)' }
                    ], {
                        placeHolder: 'Select user types (Space for multiple)',
                        canPickMany: true,
                        ignoreFocusOut: true
                    });
                    
                    if (!q2 || q2.length === 0) {
                        stream.markdown(`❌ At least one user type required`);
                        return {};
                    }
                    
                    // === SORU 3: Core Features ===
                    stream.markdown(`\n**Question 3/5: What are the core features?**\n\n`);
                    stream.markdown(`Possible answers:\n`);
                    stream.markdown(`- (A) User authentication & profiles\n`);
                    stream.markdown(`- (B) Data management (CRUD)\n`);
                    stream.markdown(`- (C) Search & filtering\n`);
                    stream.markdown(`- (D) Reporting & analytics\n`);
                    stream.markdown(`- (E) Real-time updates\n\n`);
                    stream.markdown(`*Recommended: A + B + C*\n\n`);
                    
                    const q3 = await vscode.window.showQuickPick([
                        { label: '(A) User authentication & profiles', picked: true },
                        { label: '(B) Data management (CRUD)', picked: true },
                        { label: '(C) Search & filtering', picked: true },
                        { label: '(D) Reporting & analytics' },
                        { label: '(E) Real-time updates' }
                    ], {
                        placeHolder: 'Select features (pick 2-4)',
                        canPickMany: true,
                        ignoreFocusOut: true
                    });
                    
                    if (!q3 || q3.length === 0) {
                        stream.markdown(`❌ At least one feature required`);
                        return {};
                    }
                    
                    // === SORU 4: Database ===
                    stream.markdown(`\n**Question 4/5: What type of database?**\n\n`);
                    stream.markdown(`Possible answers:\n`);
                    stream.markdown(`- (A) SQL (PostgreSQL, MySQL)\n`);
                    stream.markdown(`- (B) NoSQL (MongoDB, Firebase)\n`);
                    stream.markdown(`- (C) File-based (SQLite)\n`);
                    stream.markdown(`- (D) Not sure\n\n`);
                    stream.markdown(`*Recommended: A (reliable & structured)*\n\n`);
                    
                    const q4 = await vscode.window.showQuickPick([
                        { label: '(A) SQL (PostgreSQL, MySQL)', description: 'Recommended: Reliable & structured' },
                        { label: '(B) NoSQL (MongoDB, Firebase)', description: 'Flexible schema' },
                        { label: '(C) File-based (SQLite)', description: 'Simple, local' },
                        { label: '(D) Not sure', description: 'Let system decide' }
                    ], {
                        placeHolder: 'Select database type',
                        ignoreFocusOut: true
                    });
                    
                    // === SORU 5: Special Requirements ===
                    stream.markdown(`\n**Question 5/5: Any special requirements?**\n\n`);
                    stream.markdown(`Possible answers:\n`);
                    stream.markdown(`- (A) High security (encryption, JWT)\n`);
                    stream.markdown(`- (B) High performance (< 200ms response)\n`);
                    stream.markdown(`- (C) Scalability (handle growth)\n`);
                    stream.markdown(`- (D) Offline support\n`);
                    stream.markdown(`- (E) None (standard)\n\n`);
                    stream.markdown(`*Recommended: A + B*\n\n`);
                    
                    const q5 = await vscode.window.showQuickPick([
                        { label: '(A) High security', picked: true },
                        { label: '(B) High performance', picked: true },
                        { label: '(C) Scalability' },
                        { label: '(D) Offline support' },
                        { label: '(E) None (standard)' }
                    ], {
                        placeHolder: 'Select requirements (optional)',
                        canPickMany: true,
                        ignoreFocusOut: true
                    });
                    
                    // Build enriched context
                    const enrichedIdea = `
Project Idea: ${userMessage}

CLARIFICATION ANSWERS:

Q1. Platform: ${q1.label}
Q2. User Types: ${q2.map(x => x.label).join(', ')}
Q3. Core Features: ${q3.map(x => x.label).join(', ')}
Q4. Database: ${q4?.label || 'Not specified'}
Q5. Special Requirements: ${q5 && q5.length > 0 ? q5.map(x => x.label).join(', ') : 'None'}
`;
                    
                    stream.markdown(`\n**✅ Clarification Complete!**\n\n`);
                    stream.markdown(`**Enriched Context:**\n\`\`\`\n${enrichedIdea}\n\`\`\`\n\n`);
                    stream.markdown(`**🔄 Generating detailed SRS with Python Agent...**\n\n`);
                    
                    // Load prompt template
                    const promptPath = path.join(workspaceRoot, ".github", "prompts", "create_srs.prompt.md");
                    if (fs.existsSync(promptPath)) {
                        // Call Python agent with enriched context
                        const safeUserIdea = JSON.stringify(enrichedIdea);
                        const args = `--user-idea ${safeUserIdea}`;
                        
                        await runPythonCommand(workspaceRoot, "create-srs", args, "srs_document.txt");
                        
                        // Read the generated SRS
                        const srsPath = path.join(workspaceRoot, "data", "srs_document.txt");
                        if (fs.existsSync(srsPath)) {
                            const srsContent = fs.readFileSync(srsPath, "utf-8");
                            
                            stream.markdown(`✅ **SRS Successfully Created!**\n\n`);
                            stream.markdown(`📁 **Saved to**: \`data/srs_document.txt\`\n\n`);
                            stream.markdown(`---\n\n`);
                            stream.markdown(`## Generated SRS (Preview)\n\n`);
                            
                            // Show first 1000 characters as preview
                            const preview = srsContent.substring(0, 1000);
                            stream.markdown(`\`\`\`\n${preview}${srsContent.length > 1000 ? '\n...(truncated)' : ''}\n\`\`\`\n\n`);
                            
                            stream.markdown(`---\n\n`);
                            stream.markdown(`**📊 SRS Statistics:**\n`);
                            stream.markdown(`- Total characters: ${srsContent.length}\n`);
                            stream.markdown(`- Estimated pages: ${Math.ceil(srsContent.length / 3000)}\n\n`);
                            
                            stream.markdown(`**🎯 Next Steps:**\n`);
                            stream.markdown(`1. Review the SRS: Open \`data/srs_document.txt\`\n`);
                            stream.markdown(`2. Extract architecture: \`@mvc /extract\`\n`);
                            stream.markdown(`3. Generate scaffold: \`@mvc /scaffold\`\n`);
                        } else {
                            stream.markdown(`⚠️ **SRS created but file not found at expected location**\n`);
                        }
                    } else {
                        stream.markdown(`❌ Prompt file not found: ${promptPath}`);
                    }
                }
                else if (command === "extract") {
                    stream.markdown(`**🔄 Extracting MVC architecture (Architect Agent only)...**\n\n`);
                    
                    let srsPath = path.join(workspaceRoot, "data", "srs_document.txt");
                    
                    // Check if default SRS exists
                    if (!fs.existsSync(srsPath)) {
                        stream.markdown(`⚠️ No SRS found at \`data/srs_document.txt\`\n\n`);
                        
                        // Ask user: create new or upload existing?
                        const choice = await vscode.window.showQuickPick([
                            { label: '📝 Create new SRS', description: 'Use @mvc /create-srs command', value: 'create' },
                            { label: '📁 Upload existing SRS', description: 'Select an SRS file (.txt, .pdf)', value: 'upload' }
                        ], {
                            placeHolder: 'Choose how to provide SRS',
                            ignoreFocusOut: true
                        });
                        
                        if (!choice) {
                            stream.markdown(`❌ Cancelled`);
                            return {};
                        }
                        
                        if (choice.value === 'create') {
                            stream.markdown(`\n➡️ **Please use**: \`@mvc /create-srs <your idea>\` first\n`);
                            return {};
                        }
                        
                        if (choice.value === 'upload') {
                            // Let user select SRS file
                            const picked = await vscode.window.showOpenDialog({
                                title: 'Select SRS File',
                                canSelectMany: false,
                                filters: {
                                    'Text Files': ['txt'],
                                    'PDF Files': ['pdf'],
                                    'All Files': ['*']
                                },
                                defaultUri: vscode.Uri.file(workspaceRoot)
                            });
                            
                            if (!picked || picked.length === 0) {
                                stream.markdown(`❌ No file selected`);
                                return {};
                            }
                            
                            srsPath = picked[0].fsPath;
                            stream.markdown(`📂 **Selected SRS**: \`${path.basename(srsPath)}\`\n\n`);
                            
                            // Copy to data/ folder for consistency
                            const targetPath = path.join(workspaceRoot, "data", "srs_document.txt");
                            try {
                                fs.copyFileSync(srsPath, targetPath);
                                stream.markdown(`✅ Copied to: \`data/srs_document.txt\`\n\n`);
                                srsPath = targetPath;
                            } catch (err) {
                                console.error('[/extract] Copy error:', safeErrorToString(err));
                                stream.markdown(`⚠️ Could not copy file, using original location\n\n`);
                            }
                        }
                    } else {
                        stream.markdown(`📄 **Using existing SRS**: \`data/srs_document.txt\`\n\n`);
                    }
                    
                    // Now extract architecture (MODULAR: Only Architect Agent)
                    if (fs.existsSync(srsPath)) {
                        // Normalize paths - don't use JSON.stringify for Windows paths
                        const archPath = path.join(workspaceRoot, "data", "architecture_map.json");
                        // Use forward slashes and escape spaces/quotes properly
                        const normalizedSrsPath = srsPath.replace(/\\/g, '/');
                        const normalizedArchPath = archPath.replace(/\\/g, '/');
                        const args = `--srs-path "${normalizedSrsPath}" --output "${normalizedArchPath}"`;
                        await runPythonCommand(workspaceRoot, "extract", args, "extract_log.txt");
                        
                        stream.markdown(`✅ **Architecture extracted**: \`data/architecture_map.json\`\n\n`);
                        stream.markdown(`**Next step**: Use \`@mvc /scaffold\` to create skeleton files`);
                    } else {
                        stream.markdown(`❌ SRS file not accessible`);
                    }
                }
                else if (command === "upload-srs" || command === "load-srs") {
                    stream.markdown(`**📂 Upload Existing SRS**\n\n`);
                    
                    const picked = await vscode.window.showOpenDialog({
                        title: 'Select SRS File',
                        canSelectMany: false,
                        filters: {
                            'Text Files': ['txt'],
                            'PDF Files': ['pdf'],
                            'Markdown': ['md'],
                            'Word Documents': ['doc', 'docx'],
                            'All Files': ['*']
                        },
                        defaultUri: vscode.Uri.file(workspaceRoot)
                    });
                    
                    if (!picked || picked.length === 0) {
                        stream.markdown(`❌ No file selected`);
                        return {};
                    }
                    
                    const sourcePath = picked[0].fsPath;
                    const dataDir = path.join(workspaceRoot, "data");
                    if (!fs.existsSync(dataDir)) {
                        fs.mkdirSync(dataDir, { recursive: true });
                    }
                    const targetPath = path.join(dataDir, "srs_document.txt");
                    const fileExt = path.extname(sourcePath).toLowerCase();
                    
                    stream.markdown(`📄 **Selected**: \`${path.basename(sourcePath)}\` (${fileExt})\n\n`);
                    
                    try {
                        let content = '';
                        
                        // Handle different file types
                        if (fileExt === '.pdf') {
                            // PDF: Use Python to extract text
                            stream.markdown(`⚙️ Extracting text from PDF...\n\n`);
                            
                            // Check if Python has PyPDF2 or pdfplumber
                            const dataDir = path.join(workspaceRoot, "data");
                            if (!fs.existsSync(dataDir)) {
                                fs.mkdirSync(dataDir, { recursive: true });
                            }
                            
                            const pdfTxtPath = path.join(workspaceRoot, "data", "temp_pdf_extract.txt");
                            
                            // Try using Python to extract PDF (pdfplumber preferred, fallback to PyPDF2)
                            const pythonScript = `
import sys
text = ""

# Try pdfplumber first (better quality)
try:
    import pdfplumber
    with pdfplumber.open(r"${sourcePath}") as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + '\\n'
    if text.strip():
        with open(r"${pdfTxtPath}", 'w', encoding='utf-8') as out:
            out.write(text)
        print("SUCCESS")
        sys.exit(0)
except ImportError:
    pass
except Exception as e:
    print(f"WARN: pdfplumber failed: {e}")

# Fallback to PyPDF2
try:
    import PyPDF2
    with open(r"${sourcePath}", 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + '\\n'
    if text.strip():
        with open(r"${pdfTxtPath}", 'w', encoding='utf-8') as out:
            out.write(text)
        print("SUCCESS")
        sys.exit(0)
except ImportError:
    pass
except Exception as e:
    print(f"WARN: PyPDF2 failed: {e}")

# No PDF library available
print("ERROR: No PDF library installed. Install with: pip install pdfplumber PyPDF2")
`;
                            
                            const scriptPath = path.join(workspaceRoot, "data", "temp_pdf_extract.py");
                            fs.writeFileSync(scriptPath, pythonScript, 'utf-8');
                            
                            // Execute Python script
                            await new Promise<void>((resolve, reject) => {
                                let pythonExec = "python";
                                const venvWin = path.join(workspaceRoot, ".venv", "Scripts", "python.exe");
                                const venvUnix = path.join(workspaceRoot, ".venv", "bin", "python");
                                
                                if (fs.existsSync(venvWin)) pythonExec = `"${venvWin}"`;
                                else if (fs.existsSync(venvUnix)) pythonExec = `"${venvUnix}"`;
                                
                                exec(`${pythonExec} "${scriptPath}"`, { cwd: workspaceRoot }, (error, stdout, stderr) => {
                                    // Clean up temp script
                                    try { fs.unlinkSync(scriptPath); } catch {}
                                    
                                    if (stdout.includes("SUCCESS") && fs.existsSync(pdfTxtPath)) {
                                        content = fs.readFileSync(pdfTxtPath, 'utf-8');
                                        fs.unlinkSync(pdfTxtPath); // Clean up
                                        resolve();
                                    } else if (stdout.includes("No PDF library installed")) {
                                        stream.markdown(`⚠️ **PDF support requires pdfplumber or PyPDF2**\n\n`);
                                        stream.markdown(`Install with:\n\`\`\`bash\npip install pdfplumber PyPDF2\n\`\`\`\n\n`);
                                        stream.markdown(`Then restart VS Code.\n\n`);
                                        reject(new Error("PDF library not installed"));
                                    } else {
                                        stream.markdown(`❌ Could not extract PDF text\n\n`);
                                        if (stderr) stream.markdown(`Error: ${stderr}\n\n`);
                                        reject(new Error("PDF extraction failed"));
                                    }
                                });
                            });
                            
                        } else if (fileExt === '.doc' || fileExt === '.docx') {
                            stream.markdown(`⚠️ **Word documents not supported yet**\n\n`);
                            stream.markdown(`Please convert to .txt or .pdf first\n\n`);
                            return {};
                            
                        } else {
                            // Text-based files: Read directly
                            content = fs.readFileSync(sourcePath, 'utf-8');
                        }
                        
                        if (!content || content.trim().length === 0) {
                            stream.markdown(`❌ **Error**: File is empty or could not be read\n`);
                            return {};
                        }
                        
                        // Save to target path
                        fs.writeFileSync(targetPath, content, 'utf-8');
                        
                        // Show preview
                        const preview = content.substring(0, 500);
                        stream.markdown(`✅ **Uploaded to**: \`data/srs_document.txt\`\n\n`);
                        stream.markdown(`**Preview:**\n\`\`\`\n${preview}${content.length > 500 ? '\n...(truncated)' : ''}\n\`\`\`\n\n`);
                        stream.markdown(`📊 **Size**: ${content.length} characters\n\n`);
                        stream.markdown(`**🎯 Next Step**: Use \`@mvc /extract\` to extract MVC architecture\n`);
                        
                    } catch (err) {
                        console.error('[/upload-srs] File error:', safeErrorToString(err));
                        const errMsg = err instanceof Error ? err.message : String(err);
                        stream.markdown(`❌ **Error**: Could not read/copy file\n${errMsg}`);
                    }
                }
                else if (command === "scaffold") {
                    stream.markdown(`**🔄 Generating scaffold (Scaffolder Agent only - no LLM)...**\n\n`);
                    
                    const archPath = path.join(workspaceRoot, "data", "architecture_map.json");
                    if (fs.existsSync(archPath)) {
                        // Normalize path - don't use JSON.stringify for Windows paths
                        const normalizedArchPath = archPath.replace(/\\/g, '/');
                        const args = `--arch-path "${normalizedArchPath}"`;
                        await runPythonCommand(workspaceRoot, "scaffold", args, "scaffold_log.txt");
                        
                        stream.markdown(`✅ **Scaffold created**: \`scaffolds/mvc_skeleton/\`\n\n`);
                        stream.markdown(`**Next step**: Use \`@mvc /generate_code\` to implement code`);
                    } else {
                        stream.markdown(`❌ Architecture not found. Run \`@mvc /extract\` first.`);
                    }
                }
                else if (command === "generate_code") {
                    // Ask user: which category? (All files in that category will be processed)
                    const categoryChoice = await vscode.window.showQuickPick([
                        { label: '📊 Models', value: 'model', description: 'Process ALL model files' },
                        { label: '🎮 Controllers', value: 'controller', description: 'Process ALL controller files' },
                        { label: '🎨 Views', value: 'view', description: 'Process ALL view files' }
                    ], {
                        placeHolder: 'Select category to process (ALL files in category will be generated)',
                        ignoreFocusOut: true
                    });
                    
                    if (!categoryChoice) {
                        stream.markdown(`❌ Code generation cancelled`);
                        return {};
                    }
                    
                    const category = categoryChoice.value;
                    
                    stream.markdown(`⚙️ **Category**: ${categoryChoice.label}\n\n`);
                    stream.markdown(`**🔄 Generating code using LLM (Python Agent)...**\n\n`);
                    
                    try {
                        // Check architecture exists
                        const archPath = path.join(workspaceRoot, "data", "architecture_map.json");
                        if (!fs.existsSync(archPath)) {
                            stream.markdown(`❌ Architecture not found. Run \`@mvc /extract\` first.\n`);
                            return {};
                        }
                        
                        // Check scaffold directory exists
                        const scaffoldDir = path.join(workspaceRoot, "scaffolds", "mvc_skeleton", `${category}s`);
                        if (!fs.existsSync(scaffoldDir)) {
                            stream.markdown(`❌ Scaffold directory not found: \`${scaffoldDir}\`\n`);
                            stream.markdown(`Run \`@mvc /scaffold\` first.\n`);
                            return {};
                        }
                        
                        const scaffoldFiles = fs.readdirSync(scaffoldDir)
                            .filter(f => f.endsWith('.py'))
                            .sort();
                        
                        if (scaffoldFiles.length === 0) {
                            stream.markdown(`❌ No scaffold files found in \`${scaffoldDir}\`\n`);
                            stream.markdown(`Run \`@mvc /scaffold\` first.\n`);
                            return {};
                        }
                        
                        stream.markdown(`📋 **Found ${scaffoldFiles.length} file(s) to process**\n\n`);
                        stream.markdown(`**Generating code for all ${category} files using LLM...**\n\n`);
                        
                        // Call Python CLI to generate code
                        const normalizedArchPath = archPath.replace(/\\/g, '/');
                        const args = `--category ${category} --arch-path "${normalizedArchPath}"`;
                        await runPythonCommand(workspaceRoot, "generate-code", args, "generate_code_log.txt");
                        
                        // Check generated files
                        const generatedDir = path.join(workspaceRoot, "generated_src", `${category}s`);
                        if (fs.existsSync(generatedDir)) {
                            const generatedFiles = fs.readdirSync(generatedDir)
                                .filter(f => f.endsWith('.py'))
                                .sort();
                            
                            stream.markdown(`---\n\n`);
                            if (generatedFiles.length > 0) {
                                stream.markdown(`✅ **Code generation complete!**\n\n`);
                                stream.markdown(`📂 Generated ${generatedFiles.length} file(s) in: \`generated_src/${category}s/\`\n\n`);
                                stream.markdown(`**Generated files:**\n`);
                                generatedFiles.forEach((file, idx) => {
                                    stream.markdown(`${idx + 1}. \`${file}\`\n`);
                                });
                                stream.markdown(`\n`);
                            } else {
                                stream.markdown(`⚠️ **Warning**: Directory exists but no files were generated.\n`);
                                stream.markdown(`Check "MVC Orchestrator" output panel for Python errors.\n\n`);
                            }
                        } else {
                            stream.markdown(`---\n\n`);
                            stream.markdown(`⚠️ **Warning**: Generated directory not found at: \`generated_src/${category}s/\`\n\n`);
                            stream.markdown(`**Possible causes:**\n`);
                            stream.markdown(`1. Python CLI failed to create directory\n`);
                            stream.markdown(`2. Project root path calculation error\n`);
                            stream.markdown(`3. Permission issues\n\n`);
                            stream.markdown(`**Check:**\n`);
                            stream.markdown(`- Open "MVC Orchestrator" output panel (View → Output → Select "MVC Orchestrator")\n`);
                            stream.markdown(`- Look for Python error messages\n`);
                            stream.markdown(`- Verify scaffold files exist in: \`scaffolds/mvc_skeleton/${category}s/\`\n\n`);
                        }
                        
                    } catch (error) {
                        console.error('[/generate_code] Error:', safeErrorToString(error));
                        const errMsg = error instanceof Error ? error.message : String(error);
                        stream.markdown(`❌ **Error**: ${errMsg}\n`);
                    }
                }
                else if (command === "audit") {
                    stream.markdown(`**🔄 Running quality audit (Rules & Reviewer Agents only)...**\n\n`);
                    stream.markdown(`**Scanning current code files for violations...**\n\n`);
                    
                    const archPath = path.join(workspaceRoot, "data", "architecture_map.json");
                    // Normalize path - don't use JSON.stringify for Windows paths
                    const normalizedArchPath = archPath.replace(/\\/g, '/');
                    const args = `--arch-path "${normalizedArchPath}"`;
                    
                    // Ensure data directory exists
                    const dataDir = path.join(workspaceRoot, "data");
                    if (!fs.existsSync(dataDir)) {
                        fs.mkdirSync(dataDir, { recursive: true });
                    }
                    
                    await runPythonCommand(workspaceRoot, "audit", args, "audit_result.txt");
                    
                    // Wait a bit for file system to sync (Windows sometimes needs this)
                    await new Promise(resolve => setTimeout(resolve, 500));
                    
                    // Check if report was created/updated
                    const reportPath = path.join(workspaceRoot, "data", "final_audit_report.json");
                    
                    // Try multiple times in case of file system delay
                    let reportExists = false;
                    for (let i = 0; i < 3; i++) {
                        if (fs.existsSync(reportPath)) {
                            reportExists = true;
                            break;
                        }
                        await new Promise(resolve => setTimeout(resolve, 300));
                    }
                    
                    if (reportExists) {
                        try {
                            const reportContent = JSON.parse(fs.readFileSync(reportPath, 'utf-8'));
                            const passed = reportContent.passed || false;
                            const recommendations = reportContent.recommendations || [];
                            
                            stream.markdown(`✅ **Audit complete**\n\n`);
                            stream.markdown(`📄 **Report**: \`data/final_audit_report.json\`\n\n`);
                            
                            if (passed) {
                                stream.markdown(`✅ **Status**: PASSED - No violations detected\n\n`);
                            } else {
                                stream.markdown(`⚠️ **Status**: FAILED - ${recommendations.length} issue(s) found\n\n`);
                                if (recommendations.length > 0) {
                                    stream.markdown(`**Top Issues:**\n`);
                                    recommendations.slice(0, 3).forEach((rec: any, idx: number) => {
                                        stream.markdown(`${idx + 1}. **${rec.violation_type || 'Violation'}** in \`${rec.file || 'unknown'}\`\n`);
                                        stream.markdown(`   ${rec.problem || 'Issue detected'}\n\n`);
                                    });
                                    if (recommendations.length > 3) {
                                        stream.markdown(`... and ${recommendations.length - 3} more issue(s)\n\n`);
                                    }
                                }
                            }
                            
                            stream.markdown(`💡 **Tip**: Use \`@mvc /fix\` to automatically apply recommendations.\n\n`);
                            stream.markdown(`🔄 **Note**: Re-run \`@mvc /audit\` after making code changes to update the report.\n\n`);
                        } catch (err) {
                            stream.markdown(`✅ **Audit complete**. Check \`data/final_audit_report.json\`\n\n`);
                        }
                    } else {
                        stream.markdown(`⚠️ **Warning**: Audit completed but report file not found at: \`data/final_audit_report.json\`\n\n`);
                        stream.markdown(`**Possible causes:**\n`);
                        stream.markdown(`1. Python CLI failed silently\n`);
                        stream.markdown(`2. File system delay (Windows)\n`);
                        stream.markdown(`3. Permission issues\n\n`);
                        stream.markdown(`**Check:**\n`);
                        stream.markdown(`- Open "MVC Orchestrator" output panel (View → Output → Select "MVC Orchestrator")\n`);
                        stream.markdown(`- Look for Python error messages\n`);
                        stream.markdown(`- Verify \`generated_src/\` directory exists with Python files\n`);
                        stream.markdown(`- Try running \`@mvc /audit\` again\n\n`);
                    }
                }
                else if (command === "fix") {
                    stream.markdown(`**⚠️ Warning: This will modify files in \`generated_src/\` directory**\n\n`);
                    
                    const userChoice = await vscode.window.showWarningMessage(
                        "Apply audit recommendations? This will modify files in generated_src/ directory.",
                        { modal: true },
                        "Yes, Apply Fixes",
                        "Cancel"
                    );
                    
                    if (userChoice !== "Yes, Apply Fixes") {
                        stream.markdown(`❌ **Fix operation cancelled by user.**\n\n`);
                        return {};
                    }
                    
                    stream.markdown(`**🔧 Applying audit recommendations...**\n\n`);
                    await runPythonCommand(workspaceRoot, "run-fix", "", "fix_result.txt");
                    stream.markdown(`✅ **Fix complete**. Check output for details.\n\n`);
                }
                else {
                    // No command, show help
                    stream.markdown(`## 📋 MVC Test Orchestrator\n\n`);
                    stream.markdown(`### Available Commands:\n\n`);
                    stream.markdown(`**1. Create SRS (2 ways):**\n`);
                    stream.markdown(`- \`@mvc /create-srs <idea>\` - Interactive Q&A (5 questions)\n`);
                    stream.markdown(`- \`@mvc /upload-srs\` - Upload existing SRS file\n\n`);
                    stream.markdown(`**2. Sequential Workflow (MODULAR):**\n`);
                    stream.markdown(`- \`@mvc /extract\` - Extract architecture (Architect Agent only)\n`);
                    stream.markdown(`- \`@mvc /scaffold\` - Create skeleton files (Scaffolder Agent only, no LLM)\n`);
                    stream.markdown(`- \`@mvc /generate_code\` - Generate code using VS Code Agent (reads scaffolds/, writes to generated_src/)\n`);
                    stream.markdown(`- \`@mvc /audit\` - Run quality audit (Rules & Reviewer Agents only)\n`);
                    stream.markdown(`- \`@mvc /fix\` - Automatically apply audit recommendations\n\n`);
                    stream.markdown(`---\n\n`);
                    stream.markdown(`**Examples:**\n`);
                    stream.markdown(`\`\`\`\n@mvc /create-srs Library management system\n@mvc /upload-srs\n@mvc /extract\n\`\`\``);
                }
            } catch (error) {
                console.error('[Chat Participant] Error:', safeErrorToString(error));
                const errMsg = error instanceof Error ? error.message : String(error);
                stream.markdown(`❌ **Error**: ${errMsg}`);
            }

            return {};
        }
    );

    context.subscriptions.push(mvcChatParticipant);
}

export function deactivate() {}