# src/utils/add_violation_import.py
"""
Utility script to add a violation import to Cart.py for testing audit functionality.
"""
from pathlib import Path

def add_violation_to_cart():
    """Adds a forbidden import to Cart.py for testing."""
    project_root = Path(__file__).resolve().parents[2]
    cart_file = project_root / "generated_src" / "models" / "Cart.py"
    
    if not cart_file.exists():
        print(f"[ERROR] Cart.py not found at: {cart_file}")
        return False
    
    content = cart_file.read_text(encoding="utf-8")
    
    # Check if import already exists
    if "from generated_src.views.ProductListingView import ProductListingView" in content:
        print("[INFO] Violation import already exists in Cart.py")
        return True
    
    # Find the first import statement and add after it
    lines = content.splitlines()
    violation_import = "from generated_src.views.ProductListingView import ProductListingView"
    
    # Find where to insert (after first import block)
    insert_index = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("import ") or line.strip().startswith("from "):
            insert_index = i + 1
            # Continue until we find a non-import line
            while insert_index < len(lines) and (lines[insert_index].strip().startswith("import ") or 
                                                  lines[insert_index].strip().startswith("from ") or
                                                  lines[insert_index].strip() == ""):
                insert_index += 1
            break
    
    # Insert the violation import
    lines.insert(insert_index, violation_import)
    
    # Write back
    cart_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"[SUCCESS] Added violation import to {cart_file}")
    return True

if __name__ == "__main__":
    add_violation_to_cart()

