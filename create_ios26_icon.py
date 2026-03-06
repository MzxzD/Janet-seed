#!/opt/homebrew/bin/python3
"""
Create iOS 26-style Janet icon for menu bar
Beautiful depth, gradients, and glow effects inspired by iOS 26 design language
"""
from PIL import Image, ImageDraw, ImageFilter
import math

def create_gradient(draw, bounds, color_start, color_end, direction='vertical'):
    """Create a smooth gradient"""
    x0, y0, x1, y1 = bounds
    if direction == 'vertical':
        for y in range(y0, y1):
            ratio = (y - y0) / (y1 - y0)
            r = int(color_start[0] * (1 - ratio) + color_end[0] * ratio)
            g = int(color_start[1] * (1 - ratio) + color_end[1] * ratio)
            b = int(color_start[2] * (1 - ratio) + color_end[2] * ratio)
            a = int(color_start[3] * (1 - ratio) + color_end[3] * ratio) if len(color_start) > 3 else 255
            draw.line([(x0, y), (x1, y)], fill=(r, g, b, a))
    else:  # horizontal
        for x in range(x0, x1):
            ratio = (x - x0) / (x1 - x0)
            r = int(color_start[0] * (1 - ratio) + color_end[0] * ratio)
            g = int(color_start[1] * (1 - ratio) + color_end[1] * ratio)
            b = int(color_start[2] * (1 - ratio) + color_end[2] * ratio)
            a = int(color_start[3] * (1 - ratio) + color_end[3] * ratio) if len(color_start) > 3 else 255
            draw.line([(x, y0), (x, y1)], fill=(r, g, b, a))

def add_glow(img, color, intensity=30):
    """Add iOS 26-style glow effect"""
    glow = Image.new('RGBA', img.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    
    # Create glow layers
    for i in range(intensity, 0, -2):
        alpha = int(255 * (i / intensity) * 0.3)
        glow_color = (*color[:3], alpha)
        
        # Draw glow around the edges
        for x in range(img.size[0]):
            for y in range(img.size[1]):
                if img.getpixel((x, y))[3] > 0:
                    # Add glow around non-transparent pixels
                    for dx in range(-i, i+1):
                        for dy in range(-i, i+1):
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < img.size[0] and 0 <= ny < img.size[1]:
                                if img.getpixel((nx, ny))[3] == 0:
                                    current = glow.getpixel((nx, ny))
                                    new_alpha = min(255, current[3] + alpha // 4)
                                    glow.putpixel((nx, ny), (*glow_color[:3], new_alpha))
    
    # Blur the glow
    glow = glow.filter(ImageFilter.GaussianBlur(radius=intensity//3))
    
    # Composite
    result = Image.alpha_composite(glow, img)
    return result

def create_ios26_janet_icon(size=88):
    """Create iOS 26-style Janet icon"""
    
    # Create base image with extra space for glow
    padding = size // 4
    canvas_size = size + padding * 2
    img = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Offset for centering
    offset = padding
    center = canvas_size // 2
    
    # iOS 26 Colors - Vibrant gradients
    cyan_light = (100, 230, 220, 255)    # Light turquoise
    cyan_dark = (30, 180, 200, 255)      # Deep turquoise
    pink_light = (255, 140, 200, 255)    # Light pink
    pink_dark = (255, 80, 150, 255)      # Deep pink
    skin_light = (255, 240, 220, 255)    # Light skin
    skin_dark = (255, 210, 180, 255)     # Darker skin
    
    # === Draw Twin Pigtails with Gradient ===
    pigtail_radius = size // 4
    pigtail_offset = size // 2.5
    
    # Left pigtail
    left_pigtail = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
    left_draw = ImageDraw.Draw(left_pigtail)
    
    # Create gradient pigtail
    for i in range(pigtail_radius, 0, -1):
        ratio = i / pigtail_radius
        r = int(cyan_light[0] * ratio + cyan_dark[0] * (1 - ratio))
        g = int(cyan_light[1] * ratio + cyan_dark[1] * (1 - ratio))
        b = int(cyan_light[2] * ratio + cyan_dark[2] * (1 - ratio))
        
        left_draw.ellipse(
            [center - pigtail_offset - i, center - i,
             center - pigtail_offset + i, center + i],
            fill=(r, g, b, 255)
        )
    
    # Add highlight
    highlight_size = pigtail_radius // 3
    left_draw.ellipse(
        [center - pigtail_offset - pigtail_radius//3, center - pigtail_radius//3,
         center - pigtail_offset + pigtail_radius//3, center + pigtail_radius//3],
        fill=(200, 255, 255, 100)
    )
    
    img = Image.alpha_composite(img, left_pigtail)
    
    # Right pigtail (mirror)
    right_pigtail = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
    right_draw = ImageDraw.Draw(right_pigtail)
    
    for i in range(pigtail_radius, 0, -1):
        ratio = i / pigtail_radius
        r = int(cyan_light[0] * ratio + cyan_dark[0] * (1 - ratio))
        g = int(cyan_light[1] * ratio + cyan_dark[1] * (1 - ratio))
        b = int(cyan_light[2] * ratio + cyan_dark[2] * (1 - ratio))
        
        right_draw.ellipse(
            [center + pigtail_offset - i, center - i,
             center + pigtail_offset + i, center + i],
            fill=(r, g, b, 255)
        )
    
    # Add highlight
    right_draw.ellipse(
        [center + pigtail_offset - pigtail_radius//3, center - pigtail_radius//3,
         center + pigtail_offset + pigtail_radius//3, center + pigtail_radius//3],
        fill=(200, 255, 255, 100)
    )
    
    img = Image.alpha_composite(img, right_pigtail)
    
    # === Draw Head with Gradient ===
    head_radius = size // 3
    head_layer = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
    head_draw = ImageDraw.Draw(head_layer)
    
    # Create gradient head
    for i in range(head_radius, 0, -1):
        ratio = i / head_radius
        r = int(skin_light[0] * ratio + skin_dark[0] * (1 - ratio))
        g = int(skin_light[1] * ratio + skin_dark[1] * (1 - ratio))
        b = int(skin_light[2] * ratio + skin_dark[2] * (1 - ratio))
        
        head_draw.ellipse(
            [center - i, center - i,
             center + i, center + i],
            fill=(r, g, b, 255)
        )
    
    # Add highlight on head
    highlight_offset = head_radius // 4
    head_draw.ellipse(
        [center - highlight_offset - head_radius//4, center - highlight_offset - head_radius//4,
         center - highlight_offset + head_radius//4, center - highlight_offset + head_radius//4],
        fill=(255, 255, 255, 120)
    )
    
    img = Image.alpha_composite(img, head_layer)
    
    # === Draw Eyes ===
    eye_radius = size // 20
    eye_offset_x = size // 8
    eye_offset_y = size // 15
    
    # Left eye with shine
    draw.ellipse(
        [center - eye_offset_x - eye_radius, center - eye_offset_y - eye_radius,
         center - eye_offset_x + eye_radius, center - eye_offset_y + eye_radius],
        fill=(40, 40, 60, 255)
    )
    # Eye shine
    draw.ellipse(
        [center - eye_offset_x - eye_radius//3, center - eye_offset_y - eye_radius//2,
         center - eye_offset_x + eye_radius//3, center - eye_offset_y],
        fill=(255, 255, 255, 200)
    )
    
    # Right eye with shine
    draw.ellipse(
        [center + eye_offset_x - eye_radius, center - eye_offset_y - eye_radius,
         center + eye_offset_x + eye_radius, center - eye_offset_y + eye_radius],
        fill=(40, 40, 60, 255)
    )
    # Eye shine
    draw.ellipse(
        [center + eye_offset_x - eye_radius//3, center - eye_offset_y - eye_radius//2,
         center + eye_offset_x + eye_radius//3, center - eye_offset_y],
        fill=(255, 255, 255, 200)
    )
    
    # === Draw Smile ===
    smile_width = size // 5
    smile_y = center + size // 12
    for i in range(3):
        draw.arc(
            [center - smile_width, smile_y - 2,
             center + smile_width, smile_y + 4],
            start=0,
            end=180,
            fill=(40, 40, 60, 255),
            width=2
        )
    
    # === Draw Tie with Gradient ===
    tie_width = size // 7
    tie_height = size // 5
    tie_y = center + head_radius - size // 20
    
    tie_layer = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
    tie_draw = ImageDraw.Draw(tie_layer)
    
    # Create gradient tie
    for y in range(tie_height):
        ratio = y / tie_height
        r = int(pink_light[0] * (1 - ratio) + pink_dark[0] * ratio)
        g = int(pink_light[1] * (1 - ratio) + pink_dark[1] * ratio)
        b = int(pink_light[2] * (1 - ratio) + pink_dark[2] * ratio)
        
        tie_draw.line(
            [(center - tie_width//2, tie_y + y), (center + tie_width//2, tie_y + y)],
            fill=(r, g, b, 255),
            width=1
        )
    
    # Tie outline
    tie_draw.rectangle(
        [center - tie_width//2, tie_y,
         center + tie_width//2, tie_y + tie_height],
        outline=(200, 60, 120, 255),
        width=2
    )
    
    # Tie highlight
    tie_draw.rectangle(
        [center - tie_width//4, tie_y + tie_height//4,
         center + tie_width//4, tie_y + tie_height//2],
        fill=(255, 200, 230, 100)
    )
    
    img = Image.alpha_composite(img, tie_layer)
    
    # === Add iOS 26 Glow Effect ===
    img = add_glow(img, cyan_light, intensity=20)
    
    # === Add Subtle Shadow ===
    shadow = Image.new('RGBA', img.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_offset = size // 20
    
    # Draw shadow
    shadow_draw.ellipse(
        [center - head_radius + shadow_offset, center + head_radius - shadow_offset,
         center + head_radius + shadow_offset, center + head_radius + shadow_offset * 2],
        fill=(0, 0, 0, 50)
    )
    
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=5))
    
    # Composite shadow under everything
    result = Image.new('RGBA', img.size, (0, 0, 0, 0))
    result = Image.alpha_composite(result, shadow)
    result = Image.alpha_composite(result, img)
    
    # Crop to final size (remove padding)
    final = result.crop((padding, padding, canvas_size - padding, canvas_size - padding))
    
    return final

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    print("🎨 Creating iOS 26-style Janet icons...")
    print()
    
    # Create icons in multiple sizes
    sizes = {
        22: "1x (standard)",
        44: "2x (retina)",
        88: "4x (super retina)"
    }
    
    output_dir = Path(__file__).parent
    
    for size, desc in sizes.items():
        print(f"Creating {size}x{size} icon ({desc})...")
        img = create_ios26_janet_icon(size)
        output_path = output_dir / f"janet_icon_ios26_{size}.png"
        img.save(output_path)
        print(f"  ✅ Saved: {output_path}")
    
    # Create the default small icon (44x44 for menu bar)
    print()
    print("Creating default menu bar icon (44x44)...")
    img = create_ios26_janet_icon(44)
    default_path = output_dir / "janet_icon_small.png"
    img.save(default_path)
    print(f"  ✅ Saved: {default_path}")
    
    print()
    print("🌟 iOS 26-style icons created!")
    print()
    print("Features:")
    print("  • Beautiful gradients (cyan pigtails, pink tie)")
    print("  • Depth and dimension")
    print("  • Soft glow effect")
    print("  • Glossy highlights")
    print("  • Subtle shadows")
    print("  • Transparent background")
    print()
    print("To use:")
    print("  1. Restart menu bar app:")
    print("     pkill -f janet_menubar")
    print("     /opt/homebrew/bin/python3 janet_menubar.py &")
    print()
    print("  2. Look for the new icon in menu bar!")
    print()
    print("✨ Enjoy your iOS 26-style Janet icon! ✨")
