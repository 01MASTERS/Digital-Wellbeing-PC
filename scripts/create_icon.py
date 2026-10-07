"""Recreate the Windows application icon from the dashboard mark."""

from pathlib import Path

from PIL import Image, ImageDraw


def main() -> None:
    size = 256
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=56, fill=255)

    gradient = Image.new("RGBA", (size, size))
    pixels = gradient.load()
    assert pixels is not None
    for y in range(size):
        for x in range(size):
            blend = (x + y) / (2 * (size - 1))
            pixels[x, y] = (
                int(167 * (1 - blend) + 100 * blend),
                int(143 * (1 - blend) + 81 * blend),
                int(250 * (1 - blend) + 206 * blend),
                255,
            )
    image.paste(gradient, (0, 0), mask)
    draw = ImageDraw.Draw(image)
    draw.arc((50, 50, 206, 206), 33, 342, fill="white", width=18)
    draw.line(((178, 68), (178, 105), (216, 105)), fill="white", width=18, joint="curve")
    draw.ellipse((112, 112, 144, 144), fill="white")

    target = Path(__file__).resolve().parent.parent / "assets" / "icon.ico"
    target.parent.mkdir(exist_ok=True)
    image.save(target, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(target)


if __name__ == "__main__":
    main()
