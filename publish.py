#!/usr/bin/env python3
"""
微信公众号草稿发布脚本
从 Markdown 生成 HTML 并发布到微信草稿箱
"""

import os
import sys
import json
import re
import yaml
import requests
from pathlib import Path

# 配置
APPID = os.environ.get('WECHAT_APPID')
SECRET = os.environ.get('WECHAT_SECRET')

if not APPID or not SECRET:
    print("错误：请设置 WECHAT_APPID 和 WECHAT_SECRET 环境变量")
    sys.exit(1)

# Token 缓存
_token = None
_token_expires = 0

def get_access_token():
    """获取微信 access_token"""
    global _token, _token_expires
    
    import time
    now = time.time()
    
    if _token and now < _token_expires:
        return _token
    
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={SECRET}"
    resp = requests.get(url)
    data = resp.json()
    
    if 'access_token' not in data:
        raise ValueError(f"获取 token 失败: {data}")
    
    _token = data['access_token']
    _token_expires = now + data.get('expires_in', 7200) - 300
    return _token

def upload_image(token, image_path):
    """上传图片到微信，返回 URL"""
    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}"
    
    with open(image_path, 'rb') as f:
        files = {'media': f}
        resp = requests.post(url, files=files)
    
    data = resp.json()
    if 'url' not in data:
        raise ValueError(f"上传图片失败: {data}")
    
    return data['url']

def upload_thumb(token, image_path):
    """上传封面图，返回 media_id"""
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=thumb"
    
    with open(image_path, 'rb') as f:
        files = {'media': f}
        resp = requests.post(url, files=files)
    
    data = resp.json()
    if 'media_id' not in data:
        raise ValueError(f"上传封面失败: {data}")
    
    return data['media_id']

def markdown_to_html(md_text):
    """简单 Markdown 转 HTML（适配微信）"""
    import re
    
    # 提取标题
    title_match = re.search(r'^#\s+(.+)$', md_text, re.MULTILINE)
    title = title_match.group(1) if title_match else "无标题"
    
    # 移除 H1
    md_text = re.sub(r'^#\s+.+$\n?', '', md_text, flags=re.MULTILINE)
    
    # 转换标题
    md_text = re.sub(r'^##\s+(.+)$', r'<h2 style="font-size:20px;font-weight:bold;margin:20px 0 10px;">\1</h2>', md_text, flags=re.MULTILINE)
    md_text = re.sub(r'^###\s+(.+)$', r'<h3 style="font-size:17px;font-weight:bold;margin:15px 0 8px;">\1</h3>', md_text, flags=re.MULTILINE)
    
    # 转换粗体
    md_text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', md_text)
    
    # 转换分隔线
    md_text = re.sub(r'^---+$', '<hr style="border:none;border-top:1px solid #e0e0e0;margin:20px 0;">', md_text, flags=re.MULTILINE)
    
    # 转换段落
    paragraphs = md_text.split('\n\n')
    html_parts = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if p.startswith('<h') or p.startswith('<hr'):
            html_parts.append(p)
        else:
            # 处理换行
            p = p.replace('\n', '<br>')
            html_parts.append(f'<p style="font-size:16px;line-height:1.8;margin:10px 0;color:#333;">{p}</p>')
    
    html = '\n'.join(html_parts)
    return html, title

def create_draft(token, title, html, digest, thumb_media_id=None, author=""):
    """创建微信草稿"""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    
    article = {
        "title": title,
        "author": author,
        "digest": digest,
        "content": html,
        "show_cover_pic": 0
    }
    
    if thumb_media_id:
        article["thumb_media_id"] = thumb_media_id
    
    body = {"articles": [article]}
    
    resp = requests.post(
        url,
        data=json.dumps(body, ensure_ascii=False).encode('utf-8'),
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    
    data = resp.json()
    if data.get('errcode', 0) != 0:
        raise ValueError(f"创建草稿失败: {data}")
    
    return data['media_id']

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python publish.py <文章.md> [封面图.jpg]")
        sys.exit(1)
    
    md_path = sys.argv[1]
    cover_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # 读取 Markdown
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()
    
    # 转换 HTML
    html, title = markdown_to_html(md_text)
    
    # 生成摘要（前 120 字符）
    plain_text = re.sub(r'<[^>]+>', '', html)
    digest = plain_text[:120].replace('\n', ' ')
    
    print(f"标题: {title}")
    print(f"摘要: {digest[:50]}...")
    
    # 获取 token
    token = get_access_token()
    print("Token 获取成功")
    
    # 上传封面
    thumb_media_id = None
    if cover_path and os.path.exists(cover_path):
        print(f"上传封面: {cover_path}")
        thumb_media_id = upload_thumb(token, cover_path)
        print(f"封面 media_id: {thumb_media_id}")
    
    # 创建草稿
    print("创建草稿...")
    media_id = create_draft(token, title, html, digest, thumb_media_id, author="宋神仙")
    
    print(f"✅ 草稿创建成功！")
    print(f"media_id: {media_id}")
    print(f"请在公众号后台查看草稿")

if __name__ == '__main__':
    main()
