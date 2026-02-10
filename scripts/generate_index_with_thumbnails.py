#!/usr/bin/env python3
"""
SignalRGB Model Index Generator with Thumbnails
This script generates index.json with thumbnail previews for models.
"""

import os
import json
import base64
from datetime import datetime
import requests
from PIL import Image
import io
import sys

def create_thumbnail_from_base64(base64_data, max_size=(80, 80)):
    """Create thumbnail from Base64 image"""
    try:
        # Remove data:image prefix if present
        if 'base64,' in base64_data:
            base64_data = base64_data.split('base64,')[1]
        
        # Decode Base64
        img_data = base64.b64decode(base64_data)
        img = Image.open(io.BytesIO(img_data))
        
        # Convert to RGB (handle transparency)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA':
                r, g, b, a = img.split()
                img_rgb = Image.merge('RGB', (r, g, b))
                background.paste(img_rgb, mask=a)
            else:
                background.paste(img)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Create thumbnail
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Convert back to Base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG", optimize=True, quality=85)
        return "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode()
    except Exception as e:
        print(f"  ⚠️ Base64 thumbnail failed: {str(e)[:50]}")
        return None

def create_thumbnail_from_url(url, max_size=(80, 80)):
    """Create thumbnail from URL"""
    try:
        # Set User-Agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (SignalRGB-Model-Indexer/1.0)'
        }
        
        # Download image
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Check size
        if len(response.content) > 5 * 1024 * 1024:
            print(f"  ⚠️ Image too large, skipping")
            return None
        
        img = Image.open(io.BytesIO(response.content))
        
        # Convert to RGB
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA':
                r, g, b, a = img.split()
                img_rgb = Image.merge('RGB', (r, g, b))
                background.paste(img_rgb, mask=a)
            else:
                background.paste(img)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Create thumbnail
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Convert back to Base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG", optimize=True, quality=85)
        return "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode()
    except Exception as e:
        print(f"  ⚠️ URL thumbnail failed: {str(e)[:50]}")
        return None

def generate_index():
    """Main function to generate index"""
    models_dir = "models"
    
    if not os.path.exists(models_dir):
        print(f"❌ Error: '{models_dir}' directory does not exist")
        return None
    
    # Get all JSON files
    model_files = []
    for filename in os.listdir(models_dir):
        if filename.lower().endswith('.json') and filename != 'index.json':
            model_files.append(filename)
    
    print(f"📁 Found {len(model_files)} model files")
    print("-" * 60)
    
    models = []
    thumbnails_generated = 0
    
    for filename in sorted(model_files):
        filepath = os.path.join(models_dir, filename)
        print(f"🔍 Processing: {filename}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Basic info
            model_info = {
                "name": filename,
                "title": data.get('ProductName', filename.replace('.json', '')),
                "leds": data.get('LedCount', 0),
                "width": data.get('Width', 0),
                "height": data.get('Height', 0),
                "brand": data.get('Brand', 'CompGen'),
                "download": f"https://cdn.jsdelivr.net/gh/601338232/signalrgb-models/main/models/{filename}",
                "imageType": "none",
                "thumbnail": None
            }
            
            # Handle images
            if 'Image' in data and data['Image']:
                # Base64 image
                thumbnail = create_thumbnail_from_base64(data['Image'])
                if thumbnail:
                    model_info["thumbnail"] = thumbnail
                    model_info["imageType"] = "base64"
                    thumbnails_generated += 1
                    print(f"    ✅ Base64 thumbnail generated")
                else:
                    model_info["imageType"] = "base64"
                    print(f"    ℹ️ Base64 image (thumbnail failed)")
            
            elif 'ImageUrl' in data and data['ImageUrl']:
                # URL image
                image_url = data['ImageUrl']
                model_info["imageType"] = "url"
                
                # Try to generate thumbnail for GitHub images
                if 'github.com' in image_url or 'raw.githubusercontent.com' in image_url:
                    thumbnail = create_thumbnail_from_url(image_url)
                    if thumbnail:
                        model_info["thumbnail"] = thumbnail
                        thumbnails_generated += 1
                        print(f"    ✅ GitHub image thumbnail generated")
                    else:
                        print(f"    ℹ️ GitHub image (thumbnail failed)")
                else:
                    print(f"    ℹ️ External URL image (skipped)")
            
            else:
                print(f"    ℹ️ No image")
            
            models.append(model_info)
            print(f"    📊 {model_info['leds']} LED, {model_info['width']}×{model_info['height']}")
            
        except json.JSONDecodeError:
            print(f"    ❌ JSON decode error")
            # Create basic info even if JSON fails
            models.append({
                "name": filename,
                "title": filename.replace('.json', ''),
                "leds": 0,
                "width": 0,
                "height": 0,
                "brand": "Error",
                "download": f"https://cdn.jsdelivr.net/gh/601338232/signalrgb-models/main/models/{filename}",
                "imageType": "none",
                "thumbnail": None
            })
        except Exception as e:
            print(f"    ❌ Processing failed: {str(e)[:50]}")
    
    # Build index data
    index_data = {
        "version": "2.0",
        "updated": datetime.now().isoformat(),
        "count": len(models),
        "thumbnails": thumbnails_generated,
        "models": models
    }
    
    # Write to file
    output_path = os.path.join(models_dir, "index.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)
    
    # Statistics
    print("=" * 60)
    print("📊 Generation statistics:")
    print(f"   Total models: {len(models)}")
    print(f"   Thumbnails generated: {thumbnails_generated}")
    
    # Count by type
    base64_count = sum(1 for m in models if m['imageType'] == 'base64')
    url_count = sum(1 for m in models if m['imageType'] == 'url')
    
    print(f"   Base64 images: {base64_count}")
    print(f"   URL images: {url_count}")
    print(f"   No images: {len(models) - base64_count - url_count}")
    
    file_size = os.path.getsize(output_path) / 1024
    print(f"   File size: {file_size:.1f} KB")
    
    if file_size > 1000:
        print("⚠️  Warning: Index file exceeds 1MB")
    
    print("✅ Index generation complete!")
    return index_data

if __name__ == "__main__":
    try:
        generate_index()
    except Exception as e:
        print(f"❌ Script execution failed: {e}")
        sys.exit(1)
