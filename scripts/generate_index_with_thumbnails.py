#!/usr/bin/env python3
"""
SignalRGB Model Index Generator with Thumbnails - 修复版
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
    """从Base64创建缩略图"""
    try:
        print(f"    处理Base64图片...")
        
        # 移除data:image前缀
        if 'base64,' in base64_data:
            base64_data = base64_data.split('base64,')[1]
        
        # 解码Base64
        img_data = base64.b64decode(base64_data)
        img = Image.open(io.BytesIO(img_data))
        print(f"      原始尺寸: {img.size}, 模式: {img.mode}")
        
        # 转换为RGB
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
        
        # 生成缩略图
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        print(f"      缩略图尺寸: {img.size}")
        
        # 转换为Base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG", optimize=True, quality=85)
        result = "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode()
        print(f"      成功生成缩略图")
        return result
        
    except Exception as e:
        print(f"    ❌ Base64缩略图失败: {str(e)}")
        return None

def create_thumbnail_from_url(url, max_size=(80, 80)):
    """从URL创建缩略图 - 修复版"""
    print(f"    处理URL图片: {url[:80]}...")
    
    try:
        # 设置User-Agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # 下载图片
        print(f"      正在下载...")
        response = requests.get(url, headers=headers, timeout=15, stream=True)
        response.raise_for_status()
        
        # 获取图片数据
        content = b''
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > 5 * 1024 * 1024:  # 5MB限制
                print(f"      ⚠️ 图片超过5MB，停止下载")
                return None
        
        if not content:
            print(f"      ❌ 下载内容为空")
            return None
        
        print(f"      下载完成: {len(content)} 字节")
        
        # 打开图片
        img = Image.open(io.BytesIO(content))
        print(f"      原始尺寸: {img.size}, 模式: {img.mode}")
        
        # 转换为RGB
        if img.mode in ('RGBA', 'LA', 'P'):
            print(f"      转换透明背景...")
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA':
                r, g, b, a = img.split()
                img_rgb = Image.merge('RGB', (r, g, b))
                background.paste(img_rgb, mask=a)
            else:
                background.paste(img)
            img = background
        elif img.mode != 'RGB':
            print(f"      转换到RGB...")
            img = img.convert('RGB')
        
        # 生成缩略图
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        print(f"      缩略图尺寸: {img.size}")
        
        # 转换为Base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG", optimize=True, quality=85)
        result = "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode()
        
        print(f"      ✅ URL缩略图生成成功")
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"      ❌ 网络请求失败: {e}")
        return None
    except Exception as e:
        print(f"      ❌ 图片处理失败: {str(e)}")
        return None

def generate_index():
    """主生成函数 - 修复版"""
    models_dir = "models"
    
    if not os.path.exists(models_dir):
        print(f"❌ 错误: '{models_dir}' 目录不存在")
        return None
    
    # 获取所有JSON文件
    model_files = []
    for filename in os.listdir(models_dir):
        if filename.lower().endswith('.json') and filename != 'index.json':
            model_files.append(filename)
    
    print(f"📁 找到 {len(model_files)} 个模型文件")
    print("-" * 60)
    
    models = []
    thumbnails_generated = 0
    stats = {"base64_success": 0, "base64_fail": 0, "url_success": 0, "url_fail": 0, "no_image": 0}
    
    for i, filename in enumerate(sorted(model_files), 1):
        filepath = os.path.join(models_dir, filename)
        print(f"[{i}/{len(model_files)}] 🔍 处理: {filename}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 基本信息
            model_info = {
                "name": filename,
                "title": data.get('ProductName', filename.replace('.json', '')),
                "leds": data.get('LedCount', 0),
                "width": data.get('Width', 0),
                "height": data.get('Height', 0),
                "brand": data.get('Brand', 'CompGen'),
                "download": f"https://cdn.jsdelivr.net/gh/601338232/signalrgb-models/@main/models/{filename}",
                "imageType": "none",
                "thumbnail": None
            }
            
            # 处理图片 - 关键逻辑
            if 'Image' in data and data['Image']:
                model_info["imageType"] = "base64"
                thumbnail = create_thumbnail_from_base64(data['Image'])
                if thumbnail:
                    model_info["thumbnail"] = thumbnail
                    thumbnails_generated += 1
                    stats["base64_success"] += 1
                else:
                    stats["base64_fail"] += 1
            
            elif 'ImageUrl' in data and data['ImageUrl']:
                model_info["imageType"] = "url"
                thumbnail = create_thumbnail_from_url(data['ImageUrl'])
                if thumbnail:
                    model_info["thumbnail"] = thumbnail
                    thumbnails_generated += 1
                    stats["url_success"] += 1
                else:
                    stats["url_fail"] += 1
            
            else:
                stats["no_image"] += 1
                print(f"    ℹ️ 无图片")
            
            models.append(model_info)
            print(f"    📊 {model_info['leds']} LED, {model_info['width']}×{model_info['height']}, {model_info['imageType']}")
            
        except json.JSONDecodeError:
            print(f"    ❌ JSON格式错误")
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
            stats["no_image"] += 1
        except Exception as e:
            print(f"    ❌ 处理失败: {str(e)[:50]}")
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
            stats["no_image"] += 1
    
    # 构建索引数据
    index_data = {
        "version": "2.0",
        "updated": datetime.now().isoformat(),
        "count": len(models),
        "thumbnails": thumbnails_generated,
        "statistics": stats,
        "models": models
    }
    
    # 写入文件
    output_path = os.path.join(models_dir, "index.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)
    
    # 统计信息
    print("=" * 60)
    print("📊 详细统计:")
    print(f"   模型总数: {len(models)}")
    print(f"   总缩略图: {thumbnails_generated}")
    print(f"   Base64图片: {stats['base64_success']} 成功, {stats['base64_fail']} 失败")
    print(f"   URL图片: {stats['url_success']} 成功, {stats['url_fail']} 失败")
    print(f"   无图片: {stats['no_image']}")
    
    file_size = os.path.getsize(output_path) / 1024
    print(f"   文件大小: {file_size:.1f} KB")
    
    print("✅ 索引生成完成！")
    return index_data

if __name__ == "__main__":
    try:
        generate_index()
    except Exception as e:
        print(f"❌ 脚本执行失败: {e}")
        sys.exit(1)
