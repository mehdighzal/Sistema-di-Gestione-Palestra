from PIL import Image, ImageDraw, ImageFont
import os

def create_placeholder_images():
    # Ensure the images directory exists
    images_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images')
    os.makedirs(images_dir, exist_ok=True)

    # Create icon.png (29x29)
    icon = Image.new('RGBA', (29, 29), (255, 255, 255, 0))
    draw = ImageDraw.Draw(icon)
    # Draw a simple dumbbell icon
    draw.ellipse([2, 10, 12, 20], fill='#4285f4')  # Left weight
    draw.ellipse([17, 10, 27, 20], fill='#4285f4')  # Right weight
    draw.rectangle([10, 13, 19, 17], fill='#4285f4')  # Bar
    icon.save(os.path.join(images_dir, 'icon.png'))

    # Create logo.png (160x50)
    logo = Image.new('RGBA', (160, 50), (255, 255, 255, 0))
    draw = ImageDraw.Draw(logo)
    # Draw a simple text logo
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    draw.text((10, 10), "YOUR GYM", fill='#4285f4', font=font)
    logo.save(os.path.join(images_dir, 'logo.png'))

    # Create strip.png (312x123)
    strip = Image.new('RGBA', (312, 123), (255, 255, 255, 0))
    draw = ImageDraw.Draw(strip)
    # Draw a gradient-like background
    for y in range(123):
        # Create a gradient from blue to white
        r = int(66 + (255-66) * y/123)
        g = int(133 + (255-133) * y/123)
        b = int(244 + (255-244) * y/123)
        draw.line([(0, y), (312, y)], fill=(r, g, b, 255))
    # Add some decorative elements
    draw.rectangle([10, 10, 302, 113], outline='white', width=2)
    strip.save(os.path.join(images_dir, 'strip.png'))

    # Create hero.png (312x123) - optional
    hero = Image.new('RGBA', (312, 123), (255, 255, 255, 0))
    draw = ImageDraw.Draw(hero)
    # Draw a simple fitness-themed background
    for y in range(123):
        # Create a darker gradient
        r = int(33 + (66-33) * y/123)
        g = int(66 + (133-66) * y/123)
        b = int(122 + (244-122) * y/123)
        draw.line([(0, y), (312, y)], fill=(r, g, b, 255))
    # Add some decorative elements
    draw.rectangle([20, 20, 292, 103], outline='white', width=2)
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except:
        font = ImageFont.load_default()
    draw.text((40, 40), "FITNESS", fill='white', font=font)
    hero.save(os.path.join(images_dir, 'hero.png'))

    print("Placeholder images generated successfully in:", images_dir)

if __name__ == '__main__':
    create_placeholder_images() 