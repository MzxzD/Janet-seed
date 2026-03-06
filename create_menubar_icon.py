#!/usr/bin/env python3
"""
Create a simplified Janet icon optimized for macOS menu bar
Based on the Hatsune Miku style but simplified for small sizes
"""
from PIL import Image, ImageDraw

def create_janet_menubar_icon(size=44):
    """Create a simplified Janet icon for menu bar"""
    
    # Create image with transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors (based on Hatsune Miku style)
    cyan = (57, 197, 187)  # Turquoise hair
    pink = (255, 105, 180)  # Pink tie
    skin = (255, 228, 196)  # Light skin
    dark = (20, 20, 40)     # Dark outline
    
    # Scale factors
    center = size // 2
    
    # Draw head (circle)
    head_radius = size // 3
    draw.ellipse(
        [center - head_radius, center - head_radius,
         center + head_radius, center + head_radius],
        fill=skin,
        outline=dark,
        width=2
    )
    
    # Draw twin pigtails (simplified as circles on sides)
    pigtail_radius = size // 5
    pigtail_offset = size // 3
    
    # Left pigtail
    draw.ellipse(
        [center - pigtail_offset - pigtail_radius, center - pigtail_radius,
         center - pigtail_offset + pigtail_radius, center + pigtail_radius],
        fill=cyan,
        outline=dark,
        width=2
    )
    
    # Right pigtail
    draw.ellipse(
        [center + pigtail_offset - pigtail_radius, center - pigtail_radius,
         center + pigtail_offset + pigtail_radius, center + pigtail_radius],
        fill=cyan,
        outline=dark,
        width=2
    )
    
    # Draw eyes (simple dots)
    eye_radius = 2
    eye_offset_x = size // 8
    eye_offset_y = size // 12
    
    # Left eye
    draw.ellipse(
        [center - eye_offset_x - eye_radius, center - eye_offset_y - eye_radius,
         center - eye_offset_x + eye_radius, center - eye_offset_y + eye_radius],
        fill=dark
    )
    
    # Right eye
    draw.ellipse(
        [center + eye_offset_x - eye_radius, center - eye_offset_y - eye_radius,
         center + eye_offset_x + eye_radius, center - eye_offset_y + eye_radius],
        fill=dark
    )
    
    # Draw smile (small arc)
    mouth_width = size // 6
    mouth_y = center + size // 10
    draw.arc(
        [center - mouth_width, mouth_y - 3,
         center + mouth_width, mouth_y + 3],
        start=0,
        end=180,
        fill=dark,
        width=2
    )
    
    # Draw tie (small pink rectangle)
    tie_width = size // 8
    tie_height = size // 6
    tie_y = center + head_radius - 2
    draw.rectangle(
        [center - tie_width // 2, tie_y,
         center + tie_width // 2, tie_y + tie_height],
        fill=pink,
        outline=dark,
        width=1
    )
    
    return img

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Create icons in multiple sizes
    sizes = [22, 44, 88]  # 1x, 2x, 4x for retina displays
    
    output_dir = Path(__file__).parent
    
    for size in sizes:
        img = create_janet_menubar_icon(size)
        output_path = output_dir / f"janet_icon_{size}.png"
        img.save(output_path)
        print(f"✅ Created {output_path}")
    
    # Create the default small icon
    img = create_janet_menubar_icon(44)
    default_path = output_dir / "janet_icon_small.png"
    img.save(default_path)
    print(f"✅ Created default icon: {default_path}")
    
    print("\n🎨 Janet menu bar icons created!")
    print("Restart the menu bar app to see the new icon.")
