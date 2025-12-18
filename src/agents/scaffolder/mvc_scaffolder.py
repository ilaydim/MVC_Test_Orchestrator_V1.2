from pathlib import Path
from typing import Dict, List, Any


class MVCScaffolder:
    """
    Generates a sandbox project skeleton (models / views / controllers)
    from the already extracted architecture JSON.

    IMPORTANT:
    - It does NOT invent new classes.
    - It uses ONLY the names/descriptions found in the architecture map,
      which should itself be derived from the SRS.
    - All generated files are written under a 'scaffolds/' directory so
      they do not pollute the main src/ tree or Git history.

    Default layout (relative to project root):
    scaffolds/
      mvc_skeleton/
        models/
        views/
        controllers/
    """

    def __init__(
        self,
        project_root: Path | None = None,
        scaffold_root: Path | None = None,
    ) -> None:
        # Default project root: repo root (folder that contains src/, ui/, data/, etc.)
        # mvc_scaffolder.py is in src/agents/scaffolder/, so parents[3] = project root
        if project_root is None:
            self.project_root = Path(__file__).resolve().parents[3]
        else:
            self.project_root = Path(project_root).resolve()

        # Default scaffold root: <project_root>/scaffolds/mvc_skeleton
        if scaffold_root is None:
            self.scaffold_root = self.project_root / "scaffolds" / "mvc_skeleton"
        else:
            self.scaffold_root = Path(scaffold_root).resolve()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def scaffold_all(self, architecture: Dict[str, Any]) -> Dict[str, List[Path]]:
        """
        Creates model, view, and controller skeleton files based on
        the provided architecture map.
        
        This is a rule-based operation (no LLM). Only reads architecture_map.json
        and creates empty .py files in scaffolds/mvc_skeleton/.

        Returns:
            {
              "models": [Path(...), ...],
              "views": [Path(...), ...],
              "controllers": [Path(...), ...]
            }
        """
        # Validate architecture structure
        if not isinstance(architecture, dict):
            raise ValueError(f"Invalid architecture: expected dict, got {type(architecture)}")
        
        required_keys = ["model", "view", "controller"]
        missing_keys = [key for key in required_keys if key not in architecture]
        if missing_keys:
            raise ValueError(f"Missing required architecture keys: {missing_keys}")
        
        self._ensure_base_dirs()

        created_models = self._scaffold_models(architecture.get("model", []))
        created_views = self._scaffold_views(architecture.get("view", []))
        created_controllers = self._scaffold_controllers(architecture.get("controller", [])
        )

        return {
            "models": created_models,
            "views": created_views,
            "controllers": created_controllers,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_base_dirs(self) -> None:
        """
        Ensures that the base scaffold directory and subfolders exist:
        - scaffolds/mvc_skeleton/models/
        - scaffolds/mvc_skeleton/views/
        - scaffolds/mvc_skeleton/controllers/
        """
        (self.scaffold_root / "models").mkdir(parents=True, exist_ok=True)
        (self.scaffold_root / "views").mkdir(parents=True, exist_ok=True)
        (self.scaffold_root / "controllers").mkdir(parents=True, exist_ok=True)

    def _safe_class_name(self, raw_name: str) -> str:
        """
        Normalizes a raw SRS / architecture name into a safe class/file name.

        Examples:
        - "Homepage / Product Listing Screen" -> "HomepageProductListingScreen"
        - "Hidden Products and Categories"    -> "HiddenProductsAndCategories"
        - "AI Chatbot"                        -> "AIChatbot"
        """
        if not raw_name:
            return "Unnamed"

        # Replace separators with spaces, then title-case and remove spaces
        cleaned = raw_name.replace("/", " ").replace("-", " ")
        cleaned = " ".join(cleaned.split())  # collapse multiple spaces
        return "".join(word[0].upper() + word[1:] for word in cleaned.split())

    # ------------------------------------------------------------------
    # MODEL SCAFFOLDING
    # ------------------------------------------------------------------
    def _scaffold_models(self, models: List[Dict[str, Any]]) -> List[Path]:
        """
        Creates model skeleton files under scaffolds/mvc_skeleton/models.
        """
        created_files: List[Path] = []
        models_dir = self.scaffold_root / "models"

        for model in models:
            raw_name = model.get("name", "UnnamedModel")
            class_name = self._safe_class_name(raw_name)
            description = model.get("description", "").strip()

            file_path = models_dir / f"{class_name}.py"
            if file_path.exists():
                # Do not overwrite silently – skip existing files
                continue

            content_lines = [
                '"""',
                "Auto-generated Model skeleton from SRS.",
                "",
                f"Entity: {raw_name}",
                f"Description: {description}" if description else "",
                '"""',
                "",
                f"class {class_name}:",
                '    """Domain model entity derived from SRS."""',
                "",
                "    def __init__(self) -> None:",
                "        # TODO: add fields based on SRS attributes (if needed).",
                "        pass",
                "",
            ]
            content = "\n".join(line for line in content_lines if line is not None)

            file_path.write_text(content, encoding="utf-8")
            created_files.append(file_path)

        return created_files

    # ------------------------------------------------------------------
    # VIEW SCAFFOLDING
    # ------------------------------------------------------------------
    def _scaffold_views(self, views: List[Dict[str, Any]]) -> List[Path]:
        """
        Creates view skeleton files under scaffolds/mvc_skeleton/views.
        These are deliberately framework-agnostic (no specific UI library).
        """
        created_files: List[Path] = []
        views_dir = self.scaffold_root / "views"

        for view in views:
            raw_name = view.get("name", "UnnamedView")
            class_name = self._safe_class_name(raw_name) + "View"
            description = view.get("description", "").strip()

            file_path = views_dir / f"{class_name}.py"
            if file_path.exists():
                continue

            content_lines = [
                '"""',
                "Auto-generated View skeleton from SRS.",
                "",
                f"Screen: {raw_name}",
                f"Description: {description}" if description else "",
                '"""',
                "",
                f"class {class_name}:",
                '    """UI view abstraction derived from SRS."""',
                "",
                "    def render(self) -> None:",
                '        """Render the view (framework-specific implementation goes here)."""',
                "        # TODO: Implement rendering logic (e.g., web, desktop, mobile).",
                "        pass",
                "",
            ]
            content = "\n".join(line for line in content_lines if line is not None)

            file_path.write_text(content, encoding="utf-8")
            created_files.append(file_path)

        return created_files

    # ------------------------------------------------------------------
    # CONTROLLER SCAFFOLDING
    # ------------------------------------------------------------------
    def _scaffold_controllers(self, controllers: List[Dict[str, Any]]) -> List[Path]:
        """
        Creates controller skeleton files under scaffolds/mvc_skeleton/controllers.

        If the architecture JSON contains multiple actions for the same controller
        name, we merge them into a single file with multiple method stubs.
        """
        created_files: List[Path] = []
        controllers_dir = self.scaffold_root / "controllers"

        # Group actions by controller name
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for ctrl in controllers:
            raw_name = ctrl.get("name", "UnnamedController")
            grouped.setdefault(raw_name, []).append(ctrl)

        for raw_name, actions in grouped.items():
            base_name = self._safe_class_name(raw_name)
            if not base_name.endswith("Controller"):
                base_name += "Controller"

            file_path = controllers_dir / f"{base_name}.py"
            if file_path.exists():
                continue

            # Build methods for each action
            methods: List[str] = []
            for action in actions:
                action_name = action.get("action", "unnamed_action")
                safe_action_name = self._to_snake_case(action_name)
                description = action.get("description", "").strip()

                methods.extend(
                    [
                        f"    def {safe_action_name}(self, *args, **kwargs):",
                        '        """',
                        (
                            f"        {description}"
                            if description
                            else "        Controller action derived from SRS."
                        ),
                        '        """',
                        "        # TODO: Implement action logic based on SRS behavior.",
                        "        pass",
                        "",
                    ]
                )

            header = [
                '"""',
                "Auto-generated Controller skeleton from SRS.",
                "",
                f"Controller: {raw_name}",
                '"""',
                "",
                f"class {base_name}:",
                '    """Application controller coordinating models and views."""',
                "",
            ]

            content = "\n".join(header + methods)
            file_path.write_text(content, encoding="utf-8")
            created_files.append(file_path)

        return created_files

    def _to_snake_case(self, name: str) -> str:
        """
        Converts a human-readable action name into a snake_case method name.

        Examples:
        - 'viewProfile'            -> 'view_profile'
        - 'Add Address'            -> 'add_address'
        - 'Start Checkout Process' -> 'start_checkout_process'
        """
        if not name:
            return "unnamed_action"

        # Replace separators with spaces
        cleaned = name.replace("/", " ").replace("-", " ")

        # Insert underscores before camelCase transitions
        snake = ""
        prev_lower = False
        for ch in cleaned:
            if ch.isupper() and prev_lower:
                snake += "_"
            snake += ch
            prev_lower = ch.islower()

        # Normalize: spaces -> underscore, lower-case
        snake = snake.replace(" ", "_")
        snake = "_".join(part for part in snake.split("_") if part)  # remove extra _
        return snake.lower()
