from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def gradient_image(size, start_color, end_color):
    width, height = size
    image = Image.new("RGB", size, start_color)
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(int(start_color[i] * (1 - ratio) + end_color[i] * ratio) for i in range(3))
        draw.line([(0, y), (width, y)], fill=color)
    return image


def add_geometry(image, colors):
    draw = ImageDraw.Draw(image, "RGBA")
    width, height = image.size
    draw.ellipse((width * 0.08, height * 0.15, width * 0.34, height * 0.72), fill=colors[0])
    draw.rectangle((width * 0.45, height * 0.18, width * 0.8, height * 0.42), fill=colors[1])
    draw.polygon([(width * 0.58, height * 0.85), (width * 0.9, height * 0.62), (width * 0.78, height * 0.28)], fill=colors[2])
    return image


def create_avatar(path: Path, base_color, accent_color):
    image = Image.new("RGB", (400, 400), base_color)
    draw = ImageDraw.Draw(image)
    draw.ellipse((120, 70, 280, 230), fill=accent_color)
    draw.rounded_rectangle((90, 220, 310, 360), radius=70, fill=(240, 240, 245))
    image.save(path, quality=92)


def create_pattern_bg(path: Path, size, background, accent):
    image = Image.new("RGB", size, background)
    draw = ImageDraw.Draw(image)
    for x in range(0, size[0], 120):
        for y in range(0, size[1], 120):
            draw.rectangle((x + 12, y + 12, x + 52, y + 52), outline=accent, width=2)
            draw.ellipse((x + 60, y + 24, x + 92, y + 56), outline=accent, width=2)
    image.save(path)


def create_logo(path: Path, primary, secondary):
    image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((72, 72, 440, 440), radius=96, fill=primary)
    draw.rectangle((164, 150, 236, 362), fill=(255, 255, 255, 230))
    draw.rectangle((274, 150, 346, 362), fill=secondary)
    draw.rectangle((164, 220, 346, 292), fill=(255, 255, 255, 200))
    image.save(path)


def create_banner(path: Path, size, start_color, end_color, geometry_colors):
    image = gradient_image(size, start_color, end_color)
    image = add_geometry(image, geometry_colors)
    image.save(path, quality=92)


def create_gallery(path: Path, palette):
    image = gradient_image((1280, 720), palette[0], palette[1])
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((120, 90, 520, 500), fill=palette[2])
    draw.rectangle((640, 140, 1120, 500), fill=palette[3])
    draw.polygon([(880, 600), (1180, 420), (1080, 180), (760, 340)], fill=palette[4])
    image.save(path, quality=92)


def main():
    basic_images = ROOT / "benchmark_site_basic" / "images"
    rich_images = ROOT / "benchmark_site_rich" / "images"
    ensure_dir(basic_images)
    ensure_dir(rich_images)

    create_banner(basic_images / "banner.jpg", (1400, 500), (54, 112, 196), (148, 202, 255), [(255, 255, 255, 110), (245, 229, 155, 120), (37, 82, 122, 120)])
    create_avatar(basic_images / "avatar.jpg", (230, 236, 246), (104, 132, 180))
    create_pattern_bg(basic_images / "bg.png", (1600, 900), (247, 250, 255), (198, 214, 236))
    create_logo(basic_images / "logo.png", (37, 87, 197, 255), (242, 102, 92, 230))

    create_banner(rich_images / "banner.jpg", (1600, 600), (30, 67, 102), (119, 91, 208), [(255, 255, 255, 100), (133, 222, 201, 110), (240, 196, 84, 120)])
    create_avatar(rich_images / "avatar1.jpg", (234, 241, 249), (96, 118, 190))
    create_avatar(rich_images / "avatar2.jpg", (244, 236, 248), (129, 88, 176))
    create_avatar(rich_images / "avatar3.jpg", (237, 244, 238), (88, 146, 112))
    create_pattern_bg(rich_images / "bg.png", (1920, 1080), (243, 246, 252), (201, 210, 228))
    create_logo(rich_images / "logo.png", (42, 77, 122, 255), (118, 84, 210, 220))
    create_gallery(rich_images / "gallery1.jpg", [(50, 110, 170), (144, 214, 255), (255, 255, 255, 110), (31, 70, 120, 130), (245, 196, 118, 140)])
    create_gallery(rich_images / "gallery2.jpg", [(146, 82, 210), (244, 171, 130), (255, 255, 255, 110), (89, 42, 146, 130), (82, 188, 179, 130)])


if __name__ == "__main__":
    main()
