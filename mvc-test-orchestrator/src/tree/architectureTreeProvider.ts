import * as vscode from "vscode";
import * as path from "path";
import { ArchitectureNode } from "./architectureNode";
import { loadArchitectureJson } from "../utils/architectureLoader";

export class ArchitectureTreeProvider implements vscode.TreeDataProvider<ArchitectureNode> {
    private _onDidChangeTreeData: vscode.EventEmitter<ArchitectureNode | undefined | null | void> =
        new vscode.EventEmitter<ArchitectureNode | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<ArchitectureNode | undefined | null | void> =
        this._onDidChangeTreeData.event;

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: ArchitectureNode): vscode.TreeItem {
        return element;
    }

    getChildren(element?: ArchitectureNode): Thenable<ArchitectureNode[]> {
        if (!element) {
            return Promise.resolve(this.getTopLevelNodes());
        }

        return Promise.resolve(this.getChildNodesFor(element.label));
    }

    private getTopLevelNodes(): ArchitectureNode[] {
        return [
            new ArchitectureNode("🧩 Models", vscode.TreeItemCollapsibleState.Collapsed),
            new ArchitectureNode("🎨 Views", vscode.TreeItemCollapsibleState.Collapsed),
            new ArchitectureNode("🧠 Controllers", vscode.TreeItemCollapsibleState.Collapsed)
        ];
    }

    private getChildNodesFor(category: string): ArchitectureNode[] {
        const data = loadArchitectureJson();

        if (!data) return [];

        if (category.includes("Models")) {
            return data.model?.map((m: any) => new ArchitectureNode(m.name, vscode.TreeItemCollapsibleState.None)) ?? [];
        }
        if (category.includes("Views")) {
            return data.view?.map((v: any) => new ArchitectureNode(v.name, vscode.TreeItemCollapsibleState.None)) ?? [];
        }
        if (category.includes("Controllers")) {
            return data.controller?.map((c: any) => new ArchitectureNode(c.name, vscode.TreeItemCollapsibleState.None)) ?? [];
        }

        return [];
    }
}
