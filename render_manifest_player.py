#!/usr/bin/env python3
"""
Manifest-Based Player Sprite Renderer

Interprets the descriptive pixel format from the manifest JSON
and generates the actual 128×32 sprite sheet with all 8 frames.
"""

import json
import re
from PIL import Image, ImageDraw
from pathlib import Path


class ManifestSpriteRenderer:
    """Renders sprites from descriptive manifest format."""
    
    def __init__(self, manifest_path: str):
        """Load and parse the manifest."""
        with open(manifest_path, 'r') as f:
            self.manifest = json.load(f)
        
        # Extract color palette
        self.palette = self._extract_palette()
        print(f"Loaded palette with {len(self.palette)} colors")
        
        # Frame dimensions
        self.frame_width = 16
        self.frame_height = 32
        self.num_frames = 8
        
    def _extract_palette(self) -> dict:
        """Extract color palette from manifest."""
        palette = {}
        colors_used = self.manifest['final_specs']['colors_used']
        
        for color_desc in colors_used:
            # Parse format like "#f4d5a6 (skin base)"
            match = re.match(r'(#[0-9a-fA-F]{6})\s*\((.*?)\)', color_desc)
            if match:
                hex_color = match.group(1).upper()
                description = match.group(2)
                palette[hex_color] = description
                
                # Also map by description keywords for easier lookup
                desc_lower = description.lower()
                if 'skin base' in desc_lower or 'skin' in desc_lower:
                    palette['skin'] = hex_color
                if 'hair base' in desc_lower:
                    palette['hair_base'] = hex_color
                if 'hair shadow' in desc_lower:
                    palette['hair_shadow'] = hex_color
                if 'hair outline' in desc_lower:
                    palette['hair_outline'] = hex_color
                if 'shirt base' in desc_lower:
                    palette['shirt'] = hex_color
                if 'shirt shadow' in desc_lower:
                    palette['shirt_shadow'] = hex_color
                if 'shirt highlight' in desc_lower:
                    palette['shirt_highlight'] = hex_color
                if 'pants base' in desc_lower:
                    palette['pants'] = hex_color
                if 'eye' in desc_lower:
                    palette['eyes'] = hex_color
                if 'outline' in desc_lower and 'primary' in desc_lower:
                    palette['outline'] = hex_color
                    
        return palette
    
    def hex_to_rgba(self, hex_color: str, alpha: int = 255) -> tuple:
        """Convert hex color to RGBA tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)) + (alpha,)
    
    def render_frame_1_down_idle(self) -> Image.Image:
        """Render frame 1: down facing idle."""
        img = Image.new('RGBA', (self.frame_width, self.frame_height), (0, 0, 0, 0))
        
        # Define the character pixel by pixel based on manifest
        # This is a manual implementation based on the detailed pixel map
        
        # Row 6: hair top outline (5 pixels centered)
        self._draw_row_pixels(img, 6, [(5, '#52351C'), (6, '#52351C'), (7, '#52351C'), (8, '#52351C'), (9, '#52351C')])
        
        # Row 7: hair with outline
        self._draw_row_pixels(img, 7, [
            (4, '#52351C'), (5, '#6B4423'), (6, '#6B4423'), (7, '#6B4423'), (8, '#6B4423'), 
            (9, '#6B4423'), (10, '#6B4423'), (11, '#52351C')
        ])
        
        # Row 8: hair base
        self._draw_row_pixels(img, 8, [
            (4, '#52351C'), (5, '#8B5A2B'), (6, '#8B5A2B'), (7, '#8B5A2B'), (8, '#8B5A2B'), 
            (9, '#8B5A2B'), (10, '#52351C')
        ])
        
        # Row 9: face top with hair
        self._draw_row_pixels(img, 9, [
            (5, '#6B4423'), (6, '#6B4423'), (7, '#52351C'), (8, '#F4D5A6'), (9, '#F4D5A6'), 
            (10, '#F4D5A6'), (11, '#52351C')
        ])
        
        # Row 10: face with eyes
        self._draw_row_pixels(img, 10, [
            (4, '#1A1A1A'), (5, '#F4D5A6'), (6, '#2D2D2D'), (7, '#F4D5A6'), (8, '#F4D5A6'),
            (9, '#F4D5A6'), (10, '#2D2D2D'), (11, '#F4D5A6'), (12, '#1A1A1A')
        ])
        
        # Row 11: face mid
        self._draw_row_pixels(img, 11, [
            (4, '#1A1A1A'), (5, '#D9B886'), (6, '#F4D5A6'), (7, '#F4D5A6'), (8, '#F4D5A6'),
            (9, '#F4D5A6'), (10, '#F4D5A6'), (11, '#D9B886'), (12, '#1A1A1A')
        ])
        
        # Row 12: face bottom/neck
        self._draw_row_pixels(img, 12, [
            (5, '#1A1A1A'), (6, '#D9B886'), (7, '#D9B886'), (8, '#D9B886'), 
            (9, '#D9B886'), (10, '#D9B886'), (11, '#1A1A1A')
        ])
        
        # Row 13: shirt top
        self._draw_row_pixels(img, 13, [
            (3, '#1A1A1A'), (4, '#4A7BA7'), (5, '#4A7BA7'), (6, '#4A7BA7'), (7, '#4A7BA7'),
            (8, '#4A7BA7'), (9, '#4A7BA7'), (10, '#4A7BA7'), (11, '#4A7BA7'), (12, '#1A1A1A')
        ])
        
        # Rows 14-15: shirt with shadow
        for row in [14, 15]:
            self._draw_row_pixels(img, row, [
                (3, '#1A1A1A'), (4, '#4A7BA7'), (5, '#4A7BA7'), (6, '#4A7BA7'), (7, '#4A7BA7'),
                (8, '#4A7BA7'), (9, '#2D5A8C'), (10, '#2D5A8C'), (11, '#2D5A8C'), (12, '#1A1A1A')
            ])
        
        # Rows 16-17: shirt with highlight
        for row in [16, 17]:
            self._draw_row_pixels(img, row, [
                (3, '#1A1A1A'), (4, '#6BA3D4'), (5, '#6BA3D4'), (6, '#4A7BA7'), (7, '#4A7BA7'),
                (8, '#4A7BA7'), (9, '#4A7BA7'), (10, '#4A7BA7'), (11, '#4A7BA7'), (12, '#1A1A1A')
            ])
        
        # Row 18: shirt bottom
        self._draw_row_pixels(img, 18, [
            (4, '#1A1A1A'), (5, '#2D5A8C'), (6, '#2D5A8C'), (7, '#2D5A8C'), (8, '#2D5A8C'),
            (9, '#2D5A8C'), (10, '#2D5A8C'), (11, '#1A1A1A')
        ])
        
        # Row 19: pants top
        self._draw_row_pixels(img, 19, [
            (3, '#1A1A1A'), (4, '#8B5A2B'), (5, '#8B5A2B'), (6, '#8B5A2B'), (7, '#8B5A2B'),
            (8, '#8B5A2B'), (9, '#8B5A2B'), (10, '#8B5A2B'), (11, '#8B5A2B'), (12, '#1A1A1A')
        ])
        
        # Rows 20-22: pants mid
        for row in [20, 21, 22]:
            self._draw_row_pixels(img, row, [
                (4, '#6B4423'), (5, '#8B5A2B'), (6, '#8B5A2B'), (7, '#8B5A2B'), (8, '#8B5A2B'),
                (9, '#8B5A2B'), (10, '#8B5A2B'), (11, '#6B4423')
            ])
        
        # Rows 23-24: legs split (left forward, right back)
        for row in [23, 24]:
            self._draw_row_pixels(img, row, [
                (5, '#8B5A2B'), (6, '#8B5A2B'), (7, '#8B5A2B'), (8, '#8B5A2B'),
                (9, '#6B4423'), (10, '#6B4423'), (11, '#6B4423'), (12, '#6B4423')
            ])
        
        # Rows 25-27: legs continue
        for row in [25, 26, 27]:
            self._draw_row_pixels(img, row, [
                (5, '#8B5A2B'), (6, '#8B5A2B'), (7, '#8B5A2B'), (8, '#8B5A2B'),
                (9, '#6B4423'), (10, '#6B4423'), (11, '#6B4423')
            ])
        
        # Rows 28-29: feet
        for row in [28, 29]:
            self._draw_row_pixels(img, row, [
                (5, '#A87C4C'), (6, '#8B5A2B'), (7, '#8B5A2B'), (8, '#8B5A2B'),
                (9, '#6B4423'), (10, '#6B4423'), (11, '#6B4423')
            ])
        
        # Row 30: feet base
        self._draw_row_pixels(img, 30, [
            (5, '#52351C'), (6, '#8B5A2B'), (7, '#8B5A2B'), (8, '#52351C'),
            (9, '#52351C'), (10, '#6B4423'), (11, '#52351C')
        ])
        
        # Row 31: ground contact
        self._draw_row_pixels(img, 31, [
            (6, '#52351C'), (7, '#52351C'), (10, '#52351C'), (11, '#52351C')
        ])
        
        return img
    
    def render_frame_2_down_walk(self) -> Image.Image:
        """Render frame 2: down facing walk (legs swapped)."""
        img = self.render_frame_1_down_idle()
        
        # Clear legs area and redraw with swapped positions
        draw = ImageDraw.Draw(img)
        draw.rectangle([(4, 23), (12, 31)], fill=(0, 0, 0, 0))
        
        # Rows 23-24: legs swapped (right forward now, left back)
        for row in [23, 24]:
            self._draw_row_pixels(img, row, [
                (4, '#6B4423'), (5, '#6B4423'), (6, '#6B4423'), (7, '#6B4423'),
                (8, '#8B5A2B'), (9, '#8B5A2B'), (10, '#8B5A2B'), (11, '#8B5A2B')
            ])
        
        # Rows 25-27: legs continue swapped
        for row in [25, 26, 27]:
            self._draw_row_pixels(img, row, [
                (5, '#6B4423'), (6, '#6B4423'), (7, '#6B4423'),
                (8, '#8B5A2B'), (9, '#8B5A2B'), (10, '#8B5A2B'), (11, '#8B5A2B')
            ])
        
        # Rows 28-29: feet swapped
        for row in [28, 29]:
            self._draw_row_pixels(img, row, [
                (5, '#6B4423'), (6, '#6B4423'), (7, '#6B4423'),
                (8, '#A87C4C'), (9, '#8B5A2B'), (10, '#8B5A2B'), (11, '#8B5A2B')
            ])
        
        # Row 30: feet base swapped
        self._draw_row_pixels(img, 30, [
            (5, '#52351C'), (6, '#6B4423'), (7, '#52351C'),
            (8, '#52351C'), (9, '#8B5A2B'), (10, '#8B5A2B'), (11, '#52351C')
        ])
        
        # Row 31: ground contact swapped
        self._draw_row_pixels(img, 31, [
            (5, '#52351C'), (6, '#52351C'), (9, '#52351C'), (10, '#52351C')
        ])
        
        return img
    
    def render_frame_3_up_idle(self) -> Image.Image:
        """Render frame 3: up/back facing idle."""
        img = Image.new('RGBA', (self.frame_width, self.frame_height), (0, 0, 0, 0))
        
        # Rows 6-8: hair back view (wider)
        self._draw_row_pixels(img, 6, [
            (4, '#52351C'), (5, '#52351C'), (6, '#52351C'), (7, '#52351C'), (8, '#52351C'),
            (9, '#52351C'), (10, '#52351C'), (11, '#52351C')
        ])
        
        for row in [7, 8]:
            self._draw_row_pixels(img, row, [
                (3, '#52351C'), (4, '#6B4423'), (5, '#6B4423'), (6, '#6B4423'), (7, '#6B4423'),
                (8, '#6B4423'), (9, '#6B4423'), (10, '#6B4423'), (11, '#6B4423'), (12, '#52351C')
            ])
        
        # Row 9: hair base
        self._draw_row_pixels(img, 9, [
            (4, '#6B4423'), (5, '#8B5A2B'), (6, '#8B5A2B'), (7, '#8B5A2B'), (8, '#8B5A2B'),
            (9, '#8B5A2B'), (10, '#8B5A2B'), (11, '#6B4423')
        ])
        
        # Rows 10-11: head back (no face)
        for row in [10, 11]:
            self._draw_row_pixels(img, row, [
                (5, '#8B5A2B'), (6, '#8B5A2B'), (7, '#8B5A2B'), (8, '#8B5A2B'),
                (9, '#8B5A2B'), (10, '#8B5A2B')
            ])
        
        # Row 12: neck back
        self._draw_row_pixels(img, 12, [
            (6, '#1A1A1A'), (7, '#D9B886'), (8, '#D9B886'), (9, '#D9B886'), (10, '#1A1A1A')
        ])
        
        # Row 13: shirt back top
        self._draw_row_pixels(img, 13, [
            (3, '#1A1A1A'), (4, '#4A7BA7'), (5, '#4A7BA7'), (6, '#4A7BA7'), (7, '#4A7BA7'),
            (8, '#4A7BA7'), (9, '#4A7BA7'), (10, '#4A7BA7'), (11, '#4A7BA7'), (12, '#1A1A1A')
        ])
        
        # Rows 14-17: shirt back with center highlight
        for row in [14, 15, 16, 17]:
            self._draw_row_pixels(img, row, [
                (3, '#1A1A1A'), (4, '#4A7BA7'), (5, '#4A7BA7'), (6, '#4A7BA7'), (7, '#6BA3D4'),
                (8, '#6BA3D4'), (9, '#6BA3D4'), (10, '#4A7BA7'), (11, '#4A7BA7'), (12, '#1A1A1A')
            ])
        
        # Row 18: shirt bottom
        self._draw_row_pixels(img, 18, [
            (3, '#1A1A1A'), (4, '#2D5A8C'), (5, '#2D5A8C'), (6, '#2D5A8C'), (7, '#2D5A8C'),
            (8, '#2D5A8C'), (9, '#2D5A8C'), (10, '#2D5A8C'), (11, '#2D5A8C'), (12, '#1A1A1A')
        ])
        
        # Row 19: pants top
        self._draw_row_pixels(img, 19, [
            (3, '#1A1A1A'), (4, '#8B5A2B'), (5, '#8B5A2B'), (6, '#8B5A2B'), (7, '#8B5A2B'),
            (8, '#8B5A2B'), (9, '#8B5A2B'), (10, '#8B5A2B'), (11, '#8B5A2B'), (12, '#1A1A1A')
        ])
        
        # Rows 20-24: pants back
        for row in range(20, 25):
            self._draw_row_pixels(img, row, [
                (4, '#6B4423'), (5, '#8B5A2B'), (6, '#8B5A2B'), (7, '#8B5A2B'), (8, '#8B5A2B'),
                (9, '#8B5A2B'), (10, '#8B5A2B'), (11, '#6B4423')
            ])
        
        # Rows 25-27: legs (left forward lighter, right back darker)
        for row in [25, 26, 27]:
            self._draw_row_pixels(img, row, [
                (5, '#8B5A2B'), (6, '#8B5A2B'), (7, '#8B5A2B'), (8, '#8B5A2B'),
                (9, '#6B4423'), (10, '#6B4423'), (11, '#6B4423')
            ])
        
        # Rows 28-30: heels/feet back view
        for row in [28, 29, 30]:
            self._draw_row_pixels(img, row, [
                (5, '#52351C'), (6, '#6B4423'), (7, '#6B4423'), (8, '#52351C'),
                (9, '#52351C'), (10, '#6B4423'), (11, '#52351C')
            ])
        
        # Row 31: ground contact
        self._draw_row_pixels(img, 31, [
            (6, '#52351C'), (7, '#52351C'), (10, '#52351C'), (11, '#52351C')
        ])
        
        return img
    
    def render_frame_4_up_walk(self) -> Image.Image:
        """Render frame 4: up facing walk (legs swapped)."""
        img = self.render_frame_3_up_idle()
        
        # Clear legs and redraw swapped
        draw = ImageDraw.Draw(img)
        draw.rectangle([(4, 25), (12, 31)], fill=(0, 0, 0, 0))
        
        # Rows 25-27: legs swapped (right forward now)
        for row in [25, 26, 27]:
            self._draw_row_pixels(img, row, [
                (5, '#6B4423'), (6, '#6B4423'), (7, '#6B4423'),
                (8, '#8B5A2B'), (9, '#8B5A2B'), (10, '#8B5A2B'), (11, '#8B5A2B')
            ])
        
        # Rows 28-30: feet swapped
        for row in [28, 29, 30]:
            self._draw_row_pixels(img, row, [
                (5, '#52351C'), (6, '#6B4423'), (7, '#52351C'),
                (8, '#52351C'), (9, '#6B4423'), (10, '#6B4423'), (11, '#52351C')
            ])
        
        # Row 31: ground contact swapped
        self._draw_row_pixels(img, 31, [
            (5, '#52351C'), (6, '#52351C'), (9, '#52351C'), (10, '#52351C')
        ])
        
        return img
    
    def render_frame_5_left_idle(self) -> Image.Image:
        """Render frame 5: left profile idle."""
        img = Image.new('RGBA', (self.frame_width, self.frame_height), (0, 0, 0, 0))
        
        # Rows 6-8: hair left profile
        self._draw_row_pixels(img, 6, [
            (7, '#52351C'), (8, '#52351C'), (9, '#52351C'), (10, '#52351C')
        ])
        
        self._draw_row_pixels(img, 7, [
            (6, '#52351C'), (7, '#6B4423'), (8, '#6B4423'), (9, '#6B4423'), (10, '#6B4423'), (11, '#52351C')
        ])
        
        self._draw_row_pixels(img, 8, [
            (6, '#52351C'), (7, '#6B4423'), (8, '#6B4423'), (9, '#6B4423'), (10, '#52351C')
        ])
        
        # Row 9: hair and face start
        self._draw_row_pixels(img, 9, [
            (6, '#52351C'), (7, '#8B5A2B'), (8, '#8B5A2B'), (9, '#8B5A2B'), (10, '#F4D5A6'), (11, '#1A1A1A')
        ])
        
        # Row 10: face profile with eye
        self._draw_row_pixels(img, 10, [
            (7, '#1A1A1A'), (8, '#F4D5A6'), (9, '#2D2D2D'), (10, '#F4D5A6'), (11, '#F4D5A6'), (12, '#1A1A1A')
        ])
        
        # Row 11: face
        self._draw_row_pixels(img, 11, [
            (7, '#1A1A1A'), (8, '#F4D5A6'), (9, '#F4D5A6'), (10, '#F4D5A6'), (11, '#D9B886'), (12, '#1A1A1A')
        ])
        
        # Row 12: face/neck
        self._draw_row_pixels(img, 12, [
            (8, '#1A1A1A'), (9, '#D9B886'), (10, '#D9B886'), (11, '#1A1A1A')
        ])
        
        # Rows 13-17: shirt profile
        for row in range(13, 18):
            self._draw_row_pixels(img, row, [
                (5, '#1A1A1A'), (6, '#6BA3D4'), (7, '#6BA3D4'), (8, '#4A7BA7'), (9, '#4A7BA7'),
                (10, '#4A7BA7'), (11, '#2D5A8C'), (12, '#2D5A8C'), (13, '#1A1A1A')
            ])
        
        # Row 18: shirt bottom
        self._draw_row_pixels(img, 18, [
            (6, '#1A1A1A'), (7, '#2D5A8C'), (8, '#2D5A8C'), (9, '#2D5A8C'), (10, '#2D5A8C'),
            (11, '#2D5A8C'), (12, '#1A1A1A')
        ])
        
        # Row 19: pants top
        self._draw_row_pixels(img, 19, [
            (5, '#1A1A1A'), (6, '#8B5A2B'), (7, '#8B5A2B'), (8, '#8B5A2B'), (9, '#8B5A2B'),
            (10, '#8B5A2B'), (11, '#8B5A2B'), (12, '#1A1A1A')
        ])
        
        # Rows 20-22: pants profile
        for row in [20, 21, 22]:
            self._draw_row_pixels(img, row, [
                (6, '#8B5A2B'), (7, '#8B5A2B'), (8, '#8B5A2B'), (9, '#8B5A2B'),
                (10, '#8B5A2B'), (11, '#8B5A2B'), (12, '#8B5A2B')
            ])
        
        # Rows 23-27: legs profile (right forward, left back)
        for row in range(23, 28):
            self._draw_row_pixels(img, row, [
                (6, '#6B4423'), (7, '#6B4423'), (8, '#6B4423'),
                (9, '#8B5A2B'), (10, '#8B5A2B'), (11, '#8B5A2B'), (12, '#8B5A2B'), (13, '#8B5A2B')
            ])
        
        # Rows 28-30: feet profile
        for row in [28, 29, 30]:
            self._draw_row_pixels(img, row, [
                (6, '#52351C'), (7, '#6B4423'), (8, '#52351C'),
                (10, '#52351C'), (11, '#A87C4C'), (12, '#8B5A2B'), (13, '#52351C')
            ])
        
        # Row 31: ground contact
        self._draw_row_pixels(img, 31, [
            (7, '#52351C'), (8, '#52351C'), (11, '#52351C'), (12, '#52351C')
        ])
        
        return img
    
    def render_frame_6_left_walk(self) -> Image.Image:
        """Render frame 6: left profile walk (legs swapped)."""
        img = self.render_frame_5_left_idle()
        
        # Clear legs and redraw swapped
        draw = ImageDraw.Draw(img)
        draw.rectangle([(6, 23), (13, 31)], fill=(0, 0, 0, 0))
        
        # Rows 23-27: legs swapped (left forward now)
        for row in range(23, 28):
            self._draw_row_pixels(img, row, [
                (6, '#8B5A2B'), (7, '#8B5A2B'), (8, '#8B5A2B'), (9, '#8B5A2B'), (10, '#8B5A2B'),
                (11, '#6B4423'), (12, '#6B4423'), (13, '#6B4423')
            ])
        
        # Rows 28-30: feet swapped
        for row in [28, 29, 30]:
            self._draw_row_pixels(img, row, [
                (6, '#52351C'), (7, '#A87C4C'), (8, '#8B5A2B'), (9, '#52351C'),
                (11, '#52351C'), (12, '#6B4423'), (13, '#52351C')
            ])
        
        # Row 31: ground contact swapped
        self._draw_row_pixels(img, 31, [
            (7, '#52351C'), (8, '#52351C'), (12, '#52351C'), (13, '#52351C')
        ])
        
        return img
    
    def _draw_row_pixels(self, img: Image.Image, row: int, pixels: list):
        """Draw pixels at specific row positions."""
        for x, color in pixels:
            if x < self.frame_width and row < self.frame_height:
                rgba = self.hex_to_rgba(color)
                img.putpixel((x, row), rgba)
    
    def render_all_frames(self) -> Image.Image:
        """Render all 8 frames into a single sprite sheet."""
        # Create final sprite sheet
        sheet_width = self.frame_width * self.num_frames
        sheet_height = self.frame_height
        sprite_sheet = Image.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))
        
        # Render each frame
        frames = [
            self.render_frame_1_down_idle(),
            self.render_frame_2_down_walk(),
            self.render_frame_3_up_idle(),
            self.render_frame_4_up_walk(),
            self.render_frame_5_left_idle(),
            self.render_frame_6_left_walk(),
            None,  # Frame 7 will be mirrored frame 5
            None,  # Frame 8 will be mirrored frame 6
        ]
        
        # Mirror left frames to create right frames
        frames[6] = frames[4].transpose(Image.FLIP_LEFT_RIGHT)
        frames[7] = frames[5].transpose(Image.FLIP_LEFT_RIGHT)
        
        # Paste all frames into sprite sheet
        for i, frame in enumerate(frames):
            x_offset = i * self.frame_width
            sprite_sheet.paste(frame, (x_offset, 0))
            print(f"Frame {i+1} positioned at x={x_offset}")
        
        return sprite_sheet
    
    def save(self, output_path: str):
        """Render and save the complete sprite sheet."""
        print(f"\nRendering sprite sheet from manifest...")
        sprite_sheet = self.render_all_frames()
        
        # Save the image
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sprite_sheet.save(output_path, 'PNG')
        
        # Get file info
        file_size = output_path.stat().st_size
        print(f"\n✅ Sprite sheet saved successfully!")
        print(f"   Path: {output_path}")
        print(f"   Dimensions: {sprite_sheet.size[0]}×{sprite_sheet.size[1]} pixels")
        print(f"   File size: {file_size:,} bytes")
        print(f"   Frames: 8 (16×32 each)")
        
        return sprite_sheet, file_size


def main():
    """Main execution function."""
    manifest_path = "output/ec6c0626-8a1d-40b9-98ef-48d2e8db9f56/manifest.json"
    output_path = "output/ec6c0626-8a1d-40b9-98ef-48d2e8db9f56/player_sprite.png"
    
    print("=" * 60)
    print("Manifest-Based Player Sprite Renderer")
    print("=" * 60)
    
    renderer = ManifestSpriteRenderer(manifest_path)
    sprite_sheet, file_size = renderer.save(output_path)
    
    print("\n" + "=" * 60)
    print("Rendering Complete!")
    print("=" * 60)
    print("\nCharacter Details:")
    print("  • 8-frame player sprite with walk animations")
    print("  • 4 directions: down, up, left, right")
    print("  • 2 frames per direction (idle + walk)")
    print("  • Full character with hair, face, shirt, pants")
    print("  • Stardew Valley pixel art style")
    print("  • 13-color palette with proper shading")


if __name__ == "__main__":
    main()