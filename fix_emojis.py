"""
Fix all emoji characters in Python files to work with Windows console
Replaces Unicode emojis with ASCII equivalents
"""

from pathlib import Path
import re

# Emoji replacements
EMOJI_REPLACEMENTS = {
    '\u2713': '[+]',  # ✓ checkmark
    '\u2717': '[-]',  # ✗ X mark
    '\u26a0': '[!]',  # ⚠ warning
    '\u2192': '->',   # → rightward arrow
    '\u23f3': '[~]',  # ⏳ hourglass
    '\U0001f50d': '[SEARCH]',  # 🔍 magnifying glass
    '\U0001f4ca': '[CHART]',  # 📊 bar chart
    '\U0001f4be': '[DISK]',  # 💾 floppy disk
    '\U0001f4c4': '[FILE]',  # 📄 document
    '\U0001f4e6': '[BOX]',   # 📦 package
    '\U0001f4cb': '[LIST]',  # 📋 clipboard
    '\ufe0f': '',  # Variation selector - remove it
    '\u2265': '>=',  # ≥ greater than or equal to
    '\u2264': '<=',  # ≤ less than or equal to
    '\u2699': '[*]',  # ⚙️ gear
    '\U0001f9e0': '[BRAIN]',  # 🧠 brain
    '\u2705': '[OK]',  # ✅ white heavy checkmark
    '\u274c': '[X]',  # ❌ cross mark
}

def fix_file(file_path: Path) -> bool:
    """Fix emojis in a single file. Returns True if changes were made."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Replace each emoji
        for emoji, replacement in EMOJI_REPLACEMENTS.items():
            content = content.replace(emoji, replacement)

        # Check if any changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Fix all Python files in the project"""
    root = Path(__file__).parent

    print("Fixing emoji characters in Python files...")
    print("=" * 70)

    files_changed = []

    #Focus on key directories
    directories_to_scan = [
        root / "agents",
        root / "state_machines",
        root / "tools",
        root / "evaluation",
        root / "tests",
    ]

    for directory in directories_to_scan:
        if directory.exists():
            for py_file in directory.rglob("*.py"):
                if fix_file(py_file):
                    rel_path = py_file.relative_to(root)
                    files_changed.append(str(rel_path))
                    print(f"[FIXED] {rel_path}")

    print("=" * 70)
    print(f"\nFixed {len(files_changed)} files")

    if files_changed:
        print("\nFiles changed:")
        for f in files_changed:
            print(f"  - {f}")

    print("\n[OK] All emoji characters replaced with ASCII equivalents")


if __name__ == "__main__":
    main()
