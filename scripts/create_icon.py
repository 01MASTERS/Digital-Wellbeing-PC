"""Recreate the Windows application icon and multi-resolution ICO from the polished Time Balance mark."""

from pathlib import Path

from PIL import Image, ImageEnhance


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    master_candidates = [
        root / "assets" / "icon.png",
        root / "artifacts" / "polished_master_1024.png",
    ]
    master_path = next((p for p in master_candidates if p.is_file()), None)
    if master_path is None:
        raise FileNotFoundError("Master icon image not found in assets or artifacts")

    master = Image.open(master_path).convert("RGBA")
    sizes = [16, 32, 48, 64, 128, 256]
    imgs = {}
    for s in sizes:
        im = master.resize((s, s), Image.Resampling.LANCZOS)
        if s <= 32:
            im = ImageEnhance.Sharpness(im).enhance(1.25)
        imgs[s] = im

    target = root / "assets" / "icon.ico"
    target.parent.mkdir(exist_ok=True)

    im256 = imgs[256]
    others = [imgs[s] for s in [16, 32, 48, 64, 128]]
    im256.save(
        target,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=others,
    )
    print(f"Generated multi-resolution ICO: {target}")


if __name__ == "__main__":
    main()
