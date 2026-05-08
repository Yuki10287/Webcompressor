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


def create_gradient_gallery(path: Path, palette):
    image = gradient_image((1280, 720), palette[0], palette[1])
    draw = ImageDraw.Draw(image, "RGBA")
    width, height = image.size
    for index in range(6):
        offset = 80 + index * 150
        draw.ellipse((offset, 60 + index * 24, offset + 220, 260 + index * 24), fill=palette[2])
        draw.rectangle((offset + 120, 280, offset + 280, 540), outline=palette[3], width=4)
    for line_y in range(40, height, 72):
        draw.line((0, line_y, width, line_y + 18), fill=palette[4], width=3)
    image.save(path, quality=92)


def create_card_background(path: Path):
    image = Image.new("RGBA", (1000, 600), (244, 248, 255, 210))
    draw = ImageDraw.Draw(image, "RGBA")
    width, height = image.size
    for x in range(0, width, 120):
        for y in range(0, height, 120):
            draw.rounded_rectangle((x + 16, y + 18, x + 92, y + 94), radius=20, fill=(255, 255, 255, 82), outline=(172, 192, 228, 118), width=2)
            draw.line((x + 16, y + 102, x + 100, y + 46), fill=(151, 176, 222, 106), width=3)
    draw.ellipse((110, 80, 360, 320), fill=(255, 255, 255, 72))
    draw.ellipse((620, 220, 920, 520), fill=(199, 224, 255, 88))
    image.save(path)


def create_hero_pattern(path: Path):
    image = Image.new("RGBA", (1600, 600), (30, 67, 102, 255))
    draw = ImageDraw.Draw(image, "RGBA")
    width, height = image.size
    for x in range(0, width, 48):
        for y in range(0, height, 48):
            draw.ellipse((x + 8, y + 8, x + 14, y + 14), fill=(255, 255, 255, 70))
            draw.line((x + 18, y + 26, x + 42, y + 26), fill=(134, 202, 245, 72), width=2)
    for band in range(6):
        top = band * 100
        draw.rectangle((0, top, width, top + 42), fill=(108 + band * 8, 82 + band * 4, 180 + band * 7, 36))
    draw.polygon([(0, 540), (220, 420), (420, 520), (640, 360), (960, 460), (1240, 300), (1600, 430), (1600, 600), (0, 600)], fill=(255, 255, 255, 26))
    image.save(path)


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
    create_gradient_gallery(rich_images / "gallery3.jpg", [(38, 106, 169), (78, 188, 210), (255, 255, 255, 84), (16, 44, 86, 150), (255, 210, 110, 92)])
    create_gradient_gallery(rich_images / "gallery4.jpg", [(164, 76, 140), (244, 153, 94), (255, 255, 255, 78), (108, 34, 76, 150), (94, 215, 196, 88)])
    create_card_background(rich_images / "card_bg.png")
    create_hero_pattern(rich_images / "hero_pattern.png")


if __name__ == "__main__":
    main()
