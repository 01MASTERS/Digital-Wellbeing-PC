"""CLI entrypoint to create Windows Desktop and Start Menu shortcuts."""

from __future__ import annotations

from digital_wellbeing.shortcuts import create_shortcuts

if __name__ == "__main__":
    shortcuts = create_shortcuts()
    if shortcuts:
        print("Created shortcuts:")
        for s in shortcuts:
            print(f"  - {s}")
    else:
        print("Failed to create shortcuts.")
