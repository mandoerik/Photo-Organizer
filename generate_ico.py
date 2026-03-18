"""
Generate a Windows .ico file for the Photo Organizer app.
Creates a multi-resolution icon with the app's blue photo stack design.
Requires Pillow.
"""

from PIL import Image, ImageDraw


def create_icon_image(size):
    """Create the photo organizer icon at the given size."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    s = size / 512  # Scale factor

    # Background rounded rectangle (approximated as rectangle with rounded corners)
    bg_color = (74, 144, 226, 255)  # #4a90e2
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(60 * s), fill=bg_color)

    # Photo stack (3 white rectangles)
    white = (255, 255, 255, 255)
    light_gray = (248, 248, 248, 255)

    # Back card (rotated effect - draw slightly offset)
    draw.rounded_rectangle(
        [int(120 * s), int(120 * s), int(400 * s), int(370 * s)],
        radius=int(10 * s), fill=white
    )
    # Middle card
    draw.rounded_rectangle(
        [int(100 * s), int(110 * s), int(390 * s), int(360 * s)],
        radius=int(10 * s), fill=light_gray
    )
    # Front card
    draw.rounded_rectangle(
        [int(86 * s), int(106 * s), int(386 * s), int(356 * s)],
        radius=int(10 * s), fill=white
    )

    # Sun circle in photo
    draw.ellipse(
        [int(146 * s), int(156 * s), int(186 * s), int(196 * s)],
        fill=bg_color
    )

    # Mountain/landscape shape
    mountain_color = (45, 116, 196, 180)  # #2d74c4 with alpha
    points = [
        (int(86 * s), int(300 * s)),
        (int(186 * s), int(200 * s)),
        (int(236 * s), int(240 * s)),
        (int(386 * s), int(180 * s)),
        (int(386 * s), int(356 * s)),
        (int(86 * s), int(356 * s)),
    ]
    draw.polygon(points, fill=mountain_color)

    return img


def main():
    # Generate icon at multiple resolutions for Windows
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [create_icon_image(s) for s in sizes]

    # Save as .ico with all resolutions
    images[0].save(
        'photo_organizer.ico',
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )
    print(f"Generated photo_organizer.ico with sizes: {sizes}")


if __name__ == '__main__':
    main()
