import * as vscode from "vscode";

export class ArchitectureNode extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly contextValue: string = "architectureNode"
    ) {
        super(label, collapsibleState);
    }
}
