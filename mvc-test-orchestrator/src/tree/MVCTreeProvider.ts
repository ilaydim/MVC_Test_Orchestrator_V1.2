import * as vscode from "vscode";
import * as path from "path";
import * as fs from "fs";

export class MVCTreeProvider implements vscode.TreeDataProvider<TreeItemNode> {
    private _onDidChangeTreeData: vscode.EventEmitter<TreeItemNode | undefined | void> =
        new vscode.EventEmitter<TreeItemNode | undefined | void>();
    readonly onDidChangeTreeData: vscode.Event<TreeItemNode | undefined | void> =
        this._onDidChangeTreeData.event;

    private workspaceRoot: string;

    constructor(workspaceRoot: string) {
        this.workspaceRoot = workspaceRoot;
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: TreeItemNode): vscode.TreeItem {
        return element;
    }

    getChildren(element?: TreeItemNode): Thenable<TreeItemNode[]> {
        if (!this.workspaceRoot) {
            vscode.window.showInformationMessage("No workspace folder found");
            return Promise.resolve([]);
        }

        // ROOT SEVİYE: Models / Views / Controllers
        if (!element) {
            return Promise.resolve([
                new TreeItemNode("Models", vscode.TreeItemCollapsibleState.Collapsed, "models"),
                new TreeItemNode("Views", vscode.TreeItemCollapsibleState.Collapsed, "views"),
                new TreeItemNode(
                    "Controllers",
                    vscode.TreeItemCollapsibleState.Collapsed,
                    "controllers",
                ),
            ]);
        }

        // ÇOCUKLAR: sadece models / views / controllers için dosya oku
        const folderName = element.contextValue ?? "";

        // Dosya item’leri için children üretmiyoruz
        if (folderName !== "models" && folderName !== "views" && folderName !== "controllers") {
            return Promise.resolve([]);
        }

        const scaffoldDir = path.join(
            this.workspaceRoot,
            "scaffolds",
            "mvc_skeleton",
            folderName,
        );

        if (!fs.existsSync(scaffoldDir)) {
            return Promise.resolve([]);
        }

        const files = fs.readdirSync(scaffoldDir).filter((f) => f.endsWith(".py"));

        return Promise.resolve(
            files.map((f) => {
                const fullPath = path.join(scaffoldDir, f);

                return new TreeItemNode(
                    f.replace(".py", ""), // sol panelde gözüken label
                    vscode.TreeItemCollapsibleState.None,
                    "file",
                    vscode.Uri.file(fullPath),
                    {
                        command: "vscode.open",
                        title: "Open File",
                        arguments: [vscode.Uri.file(fullPath)],
                    },
                );
            }),
        );
    }
}

class TreeItemNode extends vscode.TreeItem {
    constructor(
        label: string,
        collapsibleState: vscode.TreeItemCollapsibleState,
        contextValue: string,
        resourceUri?: vscode.Uri,
        command?: vscode.Command,
    ) {
        super(label, collapsibleState);
        this.contextValue = contextValue;
        this.resourceUri = resourceUri;
        this.command = command;
    }
}
