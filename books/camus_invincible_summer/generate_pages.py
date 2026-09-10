#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成第23本书《我身上有个不可战胜的夏天》的精华页和研报页
"""
import re
import os

# 路径配置
REPORT_PATH = '/app/data/所有对话/主对话/camus_invincible_summer/summer_report.md'
ESSENCE_PATH = '/app/data/所有对话/主对话/gh-publish/books/camus_invincible_summer/index.html'
REPORT_HTML_PATH = '/app/data/所有对话/主对话/gh-publish/books/camus_invincible_summer/report.html'

# 读取研报内容
with open(REPORT_PATH, 'r', encoding='utf-8') as f:
    md_content = f.read()

# ===== 颜色主题：地中海夏日风格 =====
THEME = {
    'primary': '#1e6091',          # 地中海深蓝
    'primary_light': '#2a8fbd',    # 浅海蓝
    'primary_dark': '#0f3b5f',     # 深海蓝
    'accent': '#e8a838',           # 金黄阳光
    'accent_light': '#f5c86b',     # 浅金色
    'hero_grad': 'linear-gradient(135deg, #0f3b5f 0%, #1e6091 25%, #2a8fbd 55%, #e8a838 100%)',
    'hero_grad_rich': 'linear-gradient(135deg, #0d2137 0%, #153e5c 20%, #1e6091 45%, #2a8fbd 70%, #e8a838 100%)',
    'golden_quote_bg1': '#1e609112',
    'golden_quote_bg2': '#e8a83822',
    'golden_quote_border': '#1e6091',
}

def inline_markdown_to_html(text):
    """将行内Markdown转为HTML"""
    # 先处理引用链接 [(文本)](url) -> 去掉括号内容
    text = re.sub(r'\[\(([^)]+)\)\]\([^)]+\)', r'\1', text)
    # 普通链接 [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', text)
    # 加粗 **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # 斜体 *text* （避免匹配**）
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
    # 行内代码 `code`
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    return text

def parse_markdown_to_blocks(md_text):
    """解析Markdown为块级元素列表"""
    lines = md_text.split('\n')
    blocks = []
    i = 0
    in_quote = False
    quote_lines = []
    in_list = False
    list_items = []
    list_type = 'ul'
    
    def flush_list():
        nonlocal in_list, list_items, list_type
        if in_list and list_items:
            blocks.append({'type': 'list', 'items': list_items, 'list_type': list_type})
            list_items = []
            in_list = False
    
    def flush_quote():
        nonlocal in_quote, quote_lines
        if in_quote and quote_lines:
            blocks.append({'type': 'quote', 'text': '\n'.join(quote_lines)})
            quote_lines = []
            in_quote = False
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # 空行
        if not stripped:
            flush_list()
            flush_quote()
            i += 1
            continue
        
        # 标题
        if stripped.startswith('#'):
            flush_list()
            flush_quote()
            level = len(re.match(r'^#+', stripped).group())
            text = re.sub(r'^#+\s*', '', stripped)
            blocks.append({'type': 'heading', 'level': level, 'text': text})
            i += 1
            continue
        
        # 分割线
        if re.match(r'^---+\s*$', stripped):
            flush_list()
            flush_quote()
            blocks.append({'type': 'hr'})
            i += 1
            continue
        
        # 引用
        if stripped.startswith('> '):
            flush_list()
            if not in_quote:
                in_quote = True
            quote_text = re.sub(r'^>\s*', '', stripped)
            # 处理引用中的链接
            quote_text = re.sub(r'\[\(([^)]+)\)\]\([^)]+\)', '', quote_text)
            quote_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', quote_text)
            quote_lines.append(quote_text)
            i += 1
            continue
        else:
            flush_quote()
        
        # 列表
        if re.match(r'^[-*]\s+', stripped) or re.match(r'^\d+\.\s+', stripped):
            if re.match(r'^\d+\.\s+', stripped):
                curr_list_type = 'ol'
                item_text = re.sub(r'^\d+\.\s+', '', stripped)
            else:
                curr_list_type = 'ul'
                item_text = re.sub(r'^[-*]\s+', '', stripped)
            
            if not in_list:
                in_list = True
                list_type = curr_list_type
            elif list_type != curr_list_type:
                flush_list()
                in_list = True
                list_type = curr_list_type
            
            list_items.append(item_text)
            i += 1
            continue
        else:
            flush_list()
        
        # 普通段落
        blocks.append({'type': 'paragraph', 'text': stripped})
        i += 1
    
    flush_list()
    flush_quote()
    return blocks

def render_essence_content(blocks):
    """精华页内容渲染"""
    # 精华页只取核心内容：核心框架 + 金句 + 售前精华
    # 先按章节分组
    sections = []
    current_h2 = None
    current_h3 = None
    current_h3_content = []
    current_h2_h3s = []
    
    for block in blocks:
        if block['type'] == 'heading' and block['level'] == 2:
            if current_h2:
                if current_h3:
                    current_h2_h3s.append({'title': current_h3, 'content': current_h3_content})
                    current_h3 = None
                    current_h3_content = []
                sections.append({'title': current_h2, 'subsections': current_h2_h3s})
            current_h2 = block['text']
            current_h2_h3s = []
            current_h3 = None
            current_h3_content = []
        elif block['type'] == 'heading' and block['level'] == 3:
            if current_h3:
                current_h2_h3s.append({'title': current_h3, 'content': current_h3_content})
            current_h3 = block['text']
            current_h3_content = []
        elif block['type'] != 'heading' or block['level'] > 3:
            if current_h3 is not None and current_h2 is not None:
                current_h3_content.append(block)
            elif current_h2 is not None:
                # h2下直接的内容
                current_h3_content.append(block)
    
    if current_h2:
        if current_h3:
            current_h2_h3s.append({'title': current_h3, 'content': current_h3_content})
        sections.append({'title': current_h2, 'subsections': current_h2_h3s})
    
    # 找到需要的章节
    core_framework_section = None  # 第二部 核心认知框架
    golden_quotes_section = None   # 第四部 金句集锦
    presales_section = None        # 第五部 IT售前工程师视角
    
    for sec in sections:
        if '核心认知框架' in sec['title']:
            core_framework_section = sec
        elif '金句集锦' in sec['title']:
            golden_quotes_section = sec
        elif 'IT售前工程师视角' in sec['title']:
            presales_section = sec
    
    return core_framework_section, golden_quotes_section, presales_section, sections

def block_to_html(block):
    """将单个块转为HTML"""
    if block['type'] == 'paragraph':
        return f'<p>{inline_markdown_to_html(block["text"])}</p>\n'
    elif block['type'] == 'quote':
        text = block['text'].replace('\n', '<br>\n')
        return f'<blockquote>{inline_markdown_to_html(text)}</blockquote>\n'
    elif block['type'] == 'list':
        items_html = ''
        for item in block['items']:
            items_html += f'  <li>{inline_markdown_to_html(item)}</li>\n'
        tag = block['list_type']
        return f'<{tag}>\n{items_html}</{tag}>\n'
    elif block['type'] == 'hr':
        return '<hr>\n'
    return ''

def generate_essence_page():
    """生成精华页"""
    blocks = parse_markdown_to_blocks(md_content)
    core_section, quotes_section, presales_section, all_sections = render_essence_content(blocks)
    
    # 一句话总结
    one_liner = ''
    for i, block in enumerate(blocks):
        if block['type'] == 'heading' and block['level'] == 2 and '一句话总结' in block['text']:
            if i+1 < len(blocks) and blocks[i+1]['type'] == 'paragraph':
                one_liner = blocks[i+1]['text']
            break
    
    # 核心观点HTML
    core_html = ''
    if core_section:
        for sub in core_section['subsections']:
            # 精华页只取前几段
            content_html = ''
            para_count = 0
            for b in sub['content']:
                if b['type'] == 'paragraph' and para_count >= 3:
                    continue
                if b['type'] == 'paragraph':
                    para_count += 1
                content_html += block_to_html(b)
                if para_count >= 3:
                    break
            
            core_html += f'''
      <div class="subsection">
        <h3 class="subsection-title">{sub['title']}</h3>
        {content_html}
      </div>
'''
    
    # 金句HTML（取10条）
    quotes_html = ''
    if quotes_section:
        all_quotes = []
        for sub in quotes_section['subsections']:
            for b in sub['content']:
                if b['type'] == 'quote':
                    all_quotes.append(b['text'])
        # 取前10条
        selected_quotes = all_quotes[:10]
        for i, q in enumerate(selected_quotes):
            q_text = inline_markdown_to_html(q.strip())
            quotes_html += f'''
      <div class="golden-quote-item">
        <span class="golden-quote-icon">☀️</span>
        <div class="golden-quote-text">{q_text}</div>
      </div>
'''
    
    # 售前精华HTML
    presales_html = ''
    presales_action_html = ''
    if presales_section:
        # 找到行动清单项
        action_items = []
        for sub in presales_section['subsections']:
            if '行动清单' in sub['title'] or 'TOP10' in sub['title']:
                for b in sub['content']:
                    if b['type'] == 'list':
                        for item in b['items']:
                            action_items.append(item)
                break
        
        # 售前核心观点（前几个subsection的摘要）
        for sub in presales_section['subsections'][:4]:
            if '行动清单' in sub['title'] or 'TOP10' in sub['title']:
                continue
            content_html = ''
            para_count = 0
            for b in sub['content']:
                if b['type'] == 'paragraph' and para_count >= 2:
                    continue
                if b['type'] == 'paragraph':
                    para_count += 1
                content_html += block_to_html(b)
                if para_count >= 2:
                    break
            
            presales_html += f'''
      <div class="subsection">
        <h3 class="subsection-title">{sub['title']}</h3>
        {content_html}
      </div>
'''
        
        # 行动清单
        if action_items:
            for i, item in enumerate(action_items[:10]):
                item_text = inline_markdown_to_html(item)
                presales_action_html += f'''
      <li class="action-item">
        <span class="action-num">{i+1}</span>
        <span class="action-text">{item_text}</span>
      </li>
'''
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>《我身上有个不可战胜的夏天》· 精华解读</title>
<link rel="stylesheet" href="../../annotation.css">
<style>
  :root {{
    --primary: {THEME['primary']};
    --primary-light: {THEME['primary_light']};
    --primary-dark: {THEME['primary_dark']};
    --accent: {THEME['accent']};
    --accent-light: {THEME['accent_light']};
    --bg: #f0f4f8;
    --bg-card: #ffffff;
    --text: #1e293b;
    --text-secondary: #475569;
    --text-light: #94a3b8;
    --border: #e2e8f0;
    --success: #10b981;
  }}

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.8;
    -webkit-font-smoothing: antialiased;
  }}

  .container {{ max-width: 900px; margin: 0 auto; padding: 0 24px; }}

  .top-nav {{
    background: rgba(255,255,255,0.92);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    z-index: 100;
  }}
  .top-nav-inner {{
    max-width: 900px;
    margin: 0 auto;
    padding: 12px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .back-link {{
    color: var(--primary);
    text-decoration: none;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all 0.2s;
    font-weight: 500;
  }}
  .back-link:hover {{ color: var(--primary-dark); transform: translateX(-2px); }}

  .like-btn {{
    background: none;
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 6px 14px;
    cursor: pointer;
    font-size: 14px;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 4px;
    transition: all 0.2s;
  }}
  .like-btn:hover {{ background: var(--accent-light); }}

  .hero {{
    background: {THEME['hero_grad_rich']};
    color: white;
    padding: 60px 0 80px;
    position: relative;
    overflow: hidden;
  }}
  .hero::before {{
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(232,168,56,0.2) 0%, transparent 70%);
    border-radius: 50%;
    animation: pulse 8s ease-in-out infinite;
  }}
  .hero::after {{
    content: '';
    position: absolute;
    bottom: -30%;
    left: -20%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
    border-radius: 50%;
    animation: pulse 10s ease-in-out infinite reverse;
  }}
  @keyframes pulse {{
    0%, 100% {{ transform: scale(1); opacity: 0.8; }}
    50% {{ transform: scale(1.1); opacity: 1; }}
  }}
  .hero .container {{ position: relative; z-index: 1; }}
  .book-tag {{
    display: inline-block;
    background: rgba(255,255,255,0.18);
    color: rgba(255,255,255,0.95);
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 500;
    margin-bottom: 18px;
    border: 1px solid rgba(255,255,255,0.3);
  }}
  .hero h1 {{
    font-size: 36px;
    font-weight: 700;
    line-height: 1.3;
    margin-bottom: 12px;
    letter-spacing: -0.5px;
  }}
  .hero .subtitle {{
    font-size: 18px;
    opacity: 0.92;
    margin-bottom: 28px;
    font-weight: 300;
  }}
  .hero-meta {{
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    font-size: 14px;
    opacity: 0.88;
  }}
  .hero-meta span {{ display: flex; align-items: center; gap: 6px; }}

  .summary-card {{
    background: white;
    border-radius: 16px;
    padding: 32px;
    margin-top: -40px;
    position: relative;
    z-index: 2;
    box-shadow: 0 10px 40px rgba(0,0,0,0.12);
    margin-bottom: 48px;
    border: 1px solid var(--border);
  }}
  .summary-card h2 {{
    font-size: 20px;
    color: var(--primary-dark);
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .summary-card p {{
    color: var(--text-secondary);
    line-height: 1.9;
    margin-bottom: 16px;
    font-size: 15px;
  }}
  .summary-card strong {{ color: var(--primary-dark); }}

  .report-link {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 24px;
    padding: 16px 20px;
    background: linear-gradient(135deg, var(--bg), var(--accent-light));
    border-radius: 12px;
    text-decoration: none;
    color: var(--primary-dark);
    font-weight: 500;
    font-size: 14px;
    transition: all 0.2s;
    border: 1px solid rgba(0,0,0,0.05);
  }}
  .report-link:hover {{ transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,0.1); }}
  .report-link .report-label {{ display: flex; align-items: center; gap: 10px; }}
  .report-link .report-icon {{ font-size: 20px; }}
  .report-link .report-title {{ font-weight: 600; }}
  .report-link .report-desc {{
    font-size: 12px;
    color: var(--text-secondary);
    font-weight: normal;
    margin-top: 2px;
  }}
  .report-link .report-arrow {{
    font-size: 16px;
    opacity: 0.6;
    transition: transform 0.2s;
  }}
  .report-link:hover .report-arrow {{ transform: translateX(4px); opacity: 1; }}

  .section {{ margin-bottom: 56px; }}
  .section-title {{
    font-size: 26px;
    font-weight: 700;
    color: var(--primary-dark);
    margin-bottom: 24px;
    padding-bottom: 12px;
    border-bottom: 3px solid var(--primary);
    display: inline-block;
  }}

  .subsection {{ margin-bottom: 36px; }}
  .subsection-title {{
    font-size: 20px;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 16px;
    padding-left: 14px;
    border-left: 4px solid var(--accent);
  }}
  .section p {{ margin-bottom: 14px; color: var(--text-secondary); }}

  blockquote {{
    background: linear-gradient(135deg, var(--bg), var(--accent-light));
    border-left: 4px solid var(--accent);
    padding: 16px 20px;
    border-radius: 0 12px 12px 0;
    margin: 20px 0;
    color: var(--text-secondary);
    font-style: italic;
    font-size: 14px;
  }}
  blockquote strong {{ font-style: normal; color: var(--primary-dark); }}

  .quote-card {{
    background: linear-gradient(135deg, var(--bg), var(--accent-light));
    border-radius: 12px;
    padding: 24px 28px;
    margin: 20px 0;
    position: relative;
  }}
  .quote-card::before {{
    content: '"';
    position: absolute;
    top: 8px;
    left: 20px;
    font-size: 60px;
    color: rgba(0,0,0,0.08);
    font-family: Georgia, serif;
    line-height: 1;
  }}
  .quote-card p {{
    position: relative;
    z-index: 1;
    color: var(--primary-dark);
    font-size: 15px;
    line-height: 1.8;
    margin: 0;
    padding-left: 20px;
  }}
  .quote-card .quote-source {{
    margin-top: 10px;
    font-size: 13px;
    color: var(--text-secondary);
    text-align: right;
    font-style: italic;
  }}

  .key-points {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 16px;
    margin-top: 24px;
  }}
  .key-point {{
    background: linear-gradient(135deg, var(--bg), var(--accent-light));
    padding: 18px 20px;
    border-radius: 12px;
    border-left: 4px solid var(--primary);
    transition: transform 0.2s;
  }}
  .key-point:hover {{ transform: translateY(-2px); }}
  .key-point h4 {{
    font-size: 14px;
    color: var(--primary-dark);
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .key-point p {{
    font-size: 13px;
    color: var(--text-secondary);
    margin: 0;
    line-height: 1.6;
  }}

  /* 金句板块 */
  .golden-quotes-section {{ margin-bottom: 40px; }}
  .golden-quotes-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
  }}
  .golden-quote-item {{
    background: linear-gradient(135deg, {THEME['golden_quote_bg1']}, {THEME['golden_quote_bg2']});
    border-left: 4px solid {THEME['golden_quote_border']};
    border-radius: 0 10px 10px 0;
    padding: 14px 16px 14px 18px;
    display: flex;
    gap: 12px;
    align-items: flex-start;
    transition: all 0.25s ease;
  }}
  .golden-quote-item:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 20px {THEME['primary']}22;
    background: linear-gradient(135deg, #1e609118, #e8a83830);
  }}
  .golden-quote-icon {{
    font-size: 18px;
    flex-shrink: 0;
    margin-top: 2px;
  }}
  .golden-quote-text {{
    font-size: 14px;
    color: var(--text-secondary);
    line-height: 1.7;
    font-style: italic;
  }}
  .golden-quote-text strong {{
    font-style: normal;
    color: var(--primary-dark);
  }}

  /* 行动清单 */
  .action-list {{
    list-style: none;
    padding: 0;
  }}
  .action-item {{
    background: white;
    border-radius: 10px;
    padding: 14px 20px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 14px;
    border: 1px solid var(--border);
    transition: all 0.2s;
  }}
  .action-item:hover {{
    transform: translateX(4px);
    border-color: var(--accent);
    box-shadow: 0 2px 12px rgba(232,168,56,0.15);
  }}
  .action-num {{
    flex-shrink: 0;
    width: 28px;
    height: 28px;
    background: linear-gradient(135deg, var(--accent), #c4871f);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 13px;
  }}
  .action-text {{
    font-size: 14px;
    color: var(--text-secondary);
    line-height: 1.6;
  }}

  /* 底部思考区 */
  .thought-section {{
    margin: 48px 0;
  }}
  .thought-box {{
    background: white;
    border-radius: 16px;
    padding: 28px;
    border: 1px solid var(--border);
  }}
  .thought-box h3 {{
    font-size: 18px;
    color: var(--primary-dark);
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .thought-box textarea {{
    width: 100%;
    min-height: 120px;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px;
    font-family: inherit;
    font-size: 14px;
    line-height: 1.7;
    resize: vertical;
    color: var(--text);
    background: var(--bg);
    transition: border-color 0.2s;
  }}
  .thought-box textarea:focus {{
    outline: none;
    border-color: var(--accent);
    background: white;
  }}
  .thought-actions {{
    margin-top: 12px;
    display: flex;
    justify-content: flex-end;
  }}
  .thought-save-btn {{
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    color: white;
    border: none;
    padding: 10px 24px;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;
  }}
  .thought-save-btn:hover {{ opacity: 0.9; transform: translateY(-1px); }}

  @media (max-width: 768px) {{
    .hero h1 {{ font-size: 26px; }}
    .hero {{ padding: 40px 0 60px; }}
    .summary-card {{ padding: 24px; margin-top: -30px; }}
    .section-title {{ font-size: 22px; }}
    .golden-quotes-grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

  <nav class="top-nav">
    <div class="top-nav-inner">
      <a href="../../index.html" class="back-link">← 返回书架</a>
      <button class="like-btn" id="likeBtn" onclick="toggleLike()">
        <span id="likeIcon">🤍</span> <span id="likeCount">0</span>
      </button>
    </div>
  </nav>

  <section class="hero">
    <div class="container">
      <span class="book-tag">第23本 · 历史与思维</span>
      <h1>《我身上有个不可战胜的夏天》<br>精华解读</h1>
      <p class="subtitle">加缪的荒诞反抗与售前工程师的盛夏之力</p>
      <div class="hero-meta">
        <span>✍️ 阿尔贝·加缪 (Albert Camus)</span>
        <span>📖 14篇散文</span>
        <span>🏆 诺贝尔文学奖</span>
      </div>
    </div>
  </section>

  <div class="container">
    <!-- 一句话总结 -->
    <div class="summary-card">
      <h2>🎯 一句话总结</h2>
      <p>{inline_markdown_to_html(one_liner)}</p>
      <a href="report.html" class="report-link">
        <div class="report-label">
          <span class="report-icon">📚</span>
          <div>
            <div class="report-title">查看完整深度研报</div>
            <div class="report-desc">14篇散文逐篇解读 + 售前视角深度融合</div>
          </div>
        </div>
        <span class="report-arrow">→</span>
      </a>
    </div>

    <!-- 核心观点 -->
    <div class="section">
      <h2 class="section-title">🌊 核心认知框架</h2>
      <p style="color: var(--text-secondary); margin-bottom: 24px; font-size: 14px;">
        加缪思想的三个核心维度——荒诞是地基，反抗是脊梁，热爱是血肉。
      </p>
      {core_html}
    </div>

    <!-- 金句集锦 -->
    <div class="section golden-quotes-section">
      <h2 class="section-title">☀️ 盛夏金句</h2>
      <p style="color: var(--text-secondary); margin-bottom: 24px; font-size: 14px;">
        十句穿越时光的盛夏之光，在隆冬深处唤醒你心中的阳光。
      </p>
      <div class="golden-quotes-grid">
        {quotes_html}
      </div>
    </div>

    <!-- 售前精华 -->
    <div class="section">
      <h2 class="section-title">💻 售前工程师视角</h2>
      <p style="color: var(--text-secondary); margin-bottom: 24px; font-size: 14px;">
        当加缪哲学遇上IT售前——市场寒冬中的精神原典，荒诞竞争里的专业尊严。
      </p>
      {presales_html}
    </div>

    <!-- 行动清单 -->
    <div class="section">
      <h2 class="section-title">⚡ TOP 10 行动清单</h2>
      <p style="color: var(--text-secondary); margin-bottom: 24px; font-size: 14px;">
        售前工程师可立即练习的"加缪式"工作与生活修炼方法
      </p>
      <ul class="action-list">
        {presales_action_html}
      </ul>
    </div>

    <!-- 我的思考 -->
    <div class="section thought-section">
      <div class="thought-box">
        <h3>💭 我的思考笔记</h3>
        <textarea id="thoughtContent" placeholder="读完这本书，你有什么思考和感悟？记录下来吧..."></textarea>
        <div class="thought-actions">
          <button class="thought-save-btn" onclick="saveThought()">保存笔记</button>
        </div>
      </div>
    </div>
  </div>

<script>

  function getBookKey() {{
    return location.pathname.split('/').pop();
  }}
  function initLike() {{
    const key = getBookKey();
    let data = JSON.parse(localStorage.getItem(key) || '{{"count":0,"liked":false}}');
    updateLikeUI(data.count, data.liked);
  }}
  function toggleLike() {{
    const key = getBookKey();
    let data = JSON.parse(localStorage.getItem(key) || '{{"count":0,"liked":false}}');
    if (data.liked) {{
      data.count = Math.max(0, data.count - 1);
      data.liked = false;
    }} else {{
      data.count += 1;
      data.liked = true;
    }}
    localStorage.setItem(key, JSON.stringify(data));
    updateLikeUI(data.count, data.liked);
  }}
  function updateLikeUI(count, liked) {{
    document.getElementById('likeIcon').textContent = liked ? '❤️' : '🤍';
    document.getElementById('likeCount').textContent = count;
    const btn = document.getElementById('likeBtn');
    if (liked) {{
      btn.style.background = 'rgba(239,68,68,0.1)';
    }} else {{
      btn.style.background = 'none';
    }}
  }}
  function loadThought() {{
    const key = location.pathname.split('/').pop() + '_thought';
    const content = localStorage.getItem(key);
    if (content) {{
      document.getElementById('thoughtContent').value = content;
    }}
  }}
  function saveThought() {{
    const key = location.pathname.split('/').pop() + '_thought';
    const content = document.getElementById('thoughtContent').value;
    localStorage.setItem(key, content);
    const btn = event.target;
    const originalText = btn.textContent;
    btn.textContent = '✓ 已保存';
    btn.style.background = '{THEME["primary_dark"]}';
    setTimeout(function() {{
      btn.textContent = originalText;
      btn.style.background = '';
    }}, 1500);
  }}
  initLike();
  loadThought();

</script>
<script src="../../annotation.js"></script>
<script src="../../toc.js"></script>

</body>
</html>'''
    
    with open(ESSENCE_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'精华页已生成: {ESSENCE_PATH}')
    print(f'  核心观点小节: {len(core_section["subsections"]) if core_section else 0}')
    print(f'  金句数量: 10')
    print(f'  行动清单项: {10 if presales_action_html else 0}')

def generate_report_page():
    """生成研报页（完整内容）"""
    blocks = parse_markdown_to_blocks(md_content)
    
    # 构建完整HTML内容
    content_html = ''
    h2_count = 0
    h3_count = 0
    
    for block in blocks:
        if block['type'] == 'heading':
            if block['level'] == 1:
                # 跳过主标题（页面已有hero）
                continue
            elif block['level'] == 2:
                h2_count += 1
                text = inline_markdown_to_html(block['text'])
                # 跳过"一句话总结"（已在summary中）
                if '一句话总结' in block['text']:
                    continue
                content_html += f'\n<h2 class="report-chapter-title">{text}</h2>\n'
            elif block['level'] == 3:
                h3_count += 1
                text = inline_markdown_to_html(block['text'])
                content_html += f'\n<h3 class="report-subsection-title">{text}</h3>\n'
            elif block['level'] == 4:
                text = inline_markdown_to_html(block['text'])
                content_html += f'\n<h4>{text}</h4>\n'
            else:
                text = inline_markdown_to_html(block['text'])
                content_html += f'<h{block["level"]}>{text}</h{block["level"]}>\n'
        else:
            content_html += block_to_html(block)
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>《我身上有个不可战胜的夏天》· 深度研报</title>
<link rel="stylesheet" href="../../annotation.css">
<style>
  :root {{
    --primary: {THEME['primary']};
    --primary-light: {THEME['primary_light']};
    --primary-dark: {THEME['primary_dark']};
    --accent: {THEME['accent']};
    --accent-light: {THEME['accent_light']};
    --bg: #f0f4f8;
    --bg-card: #ffffff;
    --text: #1e293b;
    --text-secondary: #475569;
    --text-light: #94a3b8;
    --border: #e2e8f0;
    --success: #10b981;
  }}

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.8;
    -webkit-font-smoothing: antialiased;
  }}

  .container {{ max-width: 900px; margin: 0 auto; padding: 0 24px; }}

  .top-nav {{
    background: rgba(255,255,255,0.92);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    z-index: 100;
  }}
  .top-nav-inner {{
    max-width: 900px;
    margin: 0 auto;
    padding: 12px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .back-link {{
    color: var(--primary);
    text-decoration: none;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all 0.2s;
    font-weight: 500;
  }}
  .back-link:hover {{ color: var(--primary-dark); transform: translateX(-2px); }}

  .like-btn {{
    background: none;
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 6px 14px;
    cursor: pointer;
    font-size: 14px;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 4px;
    transition: all 0.2s;
  }}
  .like-btn:hover {{ background: var(--accent-light); }}

  .hero {{
    background: {THEME['hero_grad_rich']};
    color: white;
    padding: 60px 0 80px;
    position: relative;
    overflow: hidden;
  }}
  .hero::before {{
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(232,168,56,0.2) 0%, transparent 70%);
    border-radius: 50%;
    animation: pulse 8s ease-in-out infinite;
  }}
  .hero::after {{
    content: '';
    position: absolute;
    bottom: -30%;
    left: -20%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
    border-radius: 50%;
    animation: pulse 10s ease-in-out infinite reverse;
  }}
  @keyframes pulse {{
    0%, 100% {{ transform: scale(1); opacity: 0.8; }}
    50% {{ transform: scale(1.1); opacity: 1; }}
  }}
  .hero .container {{ position: relative; z-index: 1; }}
  .book-tag {{
    display: inline-block;
    background: rgba(255,255,255,0.18);
    color: rgba(255,255,255,0.95);
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 500;
    margin-bottom: 18px;
    border: 1px solid rgba(255,255,255,0.3);
  }}
  .hero h1 {{
    font-size: 36px;
    font-weight: 700;
    line-height: 1.3;
    margin-bottom: 12px;
    letter-spacing: -0.5px;
  }}
  .hero .subtitle {{
    font-size: 18px;
    opacity: 0.92;
    margin-bottom: 28px;
    font-weight: 300;
  }}
  .hero-meta {{
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    font-size: 14px;
    opacity: 0.88;
  }}
  .hero-meta span {{ display: flex; align-items: center; gap: 6px; }}

  .report-content {{
    background: white;
    border-radius: 16px;
    padding: 48px 56px;
    margin-top: -40px;
    position: relative;
    z-index: 2;
    box-shadow: 0 10px 40px rgba(0,0,0,0.12);
    margin-bottom: 48px;
    border: 1px solid var(--border);
  }}

  .report-chapter-title {{
    font-size: 26px;
    font-weight: 700;
    color: var(--primary-dark);
    margin: 40px 0 20px;
    padding-bottom: 12px;
    border-bottom: 3px solid var(--primary);
    display: inline-block;
  }}
  .report-chapter-title:first-child {{ margin-top: 0; }}

  .report-subsection-title {{
    font-size: 20px;
    font-weight: 600;
    color: var(--text);
    margin: 28px 0 14px;
    padding-left: 14px;
    border-left: 4px solid var(--accent);
  }}

  .report-content h4 {{
    font-size: 17px;
    font-weight: 600;
    color: var(--text);
    margin: 22px 0 12px;
  }}

  .report-content p {{
    color: var(--text-secondary);
    line-height: 1.9;
    margin-bottom: 14px;
    font-size: 15px;
  }}
  .report-content strong {{ color: var(--primary-dark); }}

  .report-content ul {{
    list-style: none;
    padding: 0;
    margin: 16px 0;
  }}
  .report-content li {{
    padding: 8px 0;
    padding-left: 28px;
    position: relative;
    color: var(--text-secondary);
    font-size: 14px;
    line-height: 1.7;
  }}
  .report-content li::before {{
    content: '◆';
    position: absolute;
    left: 0;
    color: var(--accent);
    font-size: 12px;
    top: 11px;
  }}

  .report-content blockquote {{
    background: linear-gradient(135deg, var(--bg), var(--accent-light));
    border-left: 4px solid var(--accent);
    padding: 16px 20px;
    border-radius: 0 12px 12px 0;
    margin: 20px 0;
    color: var(--text-secondary);
    font-style: italic;
    font-size: 14px;
  }}
  .report-content blockquote strong {{ font-style: normal; color: var(--primary-dark); }}
  .report-content blockquote br {{ display: none; }}
  .report-content blockquote {{ line-height: 1.8; }}

  .report-content hr {{
    border: none;
    border-top: 1px solid var(--border);
    margin: 32px 0;
  }}

  .report-content a {{
    color: var(--accent);
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: border-color 0.2s;
  }}
  .report-content a:hover {{
    border-bottom-color: var(--accent);
  }}

  .essence-link {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
    padding: 16px 20px;
    background: linear-gradient(135deg, var(--bg), var(--accent-light));
    border-radius: 12px;
    text-decoration: none;
    color: var(--primary-dark);
    font-weight: 500;
    font-size: 14px;
    transition: all 0.2s;
    border: 1px solid rgba(0,0,0,0.05);
  }}
  .essence-link:hover {{ transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,0.1); }}
  .essence-link .essence-label {{ display: flex; align-items: center; gap: 10px; }}
  .essence-link .essence-icon {{ font-size: 20px; }}
  .essence-link .essence-title {{ font-weight: 600; }}
  .essence-link .essence-desc {{
    font-size: 12px;
    color: var(--text-secondary);
    font-weight: normal;
    margin-top: 2px;
  }}
  .essence-link .essence-arrow {{
    font-size: 16px;
    opacity: 0.6;
    transition: transform 0.2s;
  }}
  .essence-link:hover .essence-arrow {{ transform: translateX(-4px); opacity: 1; }}

  .thought-section {{
    margin: 32px 0;
  }}
  .thought-box {{
    background: var(--bg);
    border-radius: 12px;
    padding: 24px;
    border: 1px solid var(--border);
  }}
  .thought-box h3 {{
    font-size: 17px;
    color: var(--primary-dark);
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .thought-box textarea {{
    width: 100%;
    min-height: 100px;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px;
    font-family: inherit;
    font-size: 14px;
    line-height: 1.7;
    resize: vertical;
    color: var(--text);
    background: white;
    transition: border-color 0.2s;
  }}
  .thought-box textarea:focus {{
    outline: none;
    border-color: var(--accent);
  }}
  .thought-actions {{
    margin-top: 12px;
    display: flex;
    justify-content: flex-end;
  }}
  .thought-save-btn {{
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    color: white;
    border: none;
    padding: 10px 24px;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;
  }}
  .thought-save-btn:hover {{ opacity: 0.9; }}

  @media (max-width: 768px) {{
    .hero h1 {{ font-size: 26px; }}
    .hero {{ padding: 40px 0 60px; }}
    .report-content {{ padding: 28px 20px; margin-top: -30px; }}
    .report-chapter-title {{ font-size: 22px; }}
  }}
</style>
</head>
<body>

  <nav class="top-nav">
    <div class="top-nav-inner">
      <a href="../../index.html" class="back-link">← 返回书架</a>
      <button class="like-btn" id="likeBtn" onclick="toggleLike()">
        <span id="likeIcon">🤍</span> <span id="likeCount">0</span>
      </button>
    </div>
  </nav>

  <section class="hero">
    <div class="container">
      <span class="book-tag">第23本 · 历史与思维 · 深度研报</span>
      <h1>《我身上有个不可战胜的夏天》</h1>
      <p class="subtitle">加缪的荒诞反抗与售前工程师的盛夏之力</p>
      <div class="hero-meta">
        <span>✍️ 阿尔贝·加缪 (Albert Camus)</span>
        <span>📖 14篇散文深度解读</span>
        <span>🏆 诺贝尔文学奖得主</span>
      </div>
    </div>
  </section>

  <div class="container">
    <div class="report-content">
      <a href="index.html" class="essence-link">
        <div class="essence-label">
          <span class="essence-icon">✨</span>
          <div>
            <div class="essence-title">查看精华版解读</div>
            <div class="essence-desc">核心观点 + 金句集锦 + 行动清单</div>
          </div>
        </div>
        <span class="essence-arrow">←</span>
      </a>
      
      {content_html}

      <!-- 我的思考 -->
      <div class="thought-section">
        <div class="thought-box">
          <h3>💭 我的思考笔记</h3>
          <textarea id="thoughtContent" placeholder="读完这篇研报，你有什么思考和感悟？记录下来吧..."></textarea>
          <div class="thought-actions">
            <button class="thought-save-btn" onclick="saveThought()">保存笔记</button>
          </div>
        </div>
      </div>
    </div>
  </div>

<script>

  function getBookKey() {{
    return location.pathname.split('/').pop();
  }}
  function initLike() {{
    const key = getBookKey();
    let data = JSON.parse(localStorage.getItem(key) || '{{"count":0,"liked":false}}');
    updateLikeUI(data.count, data.liked);
  }}
  function toggleLike() {{
    const key = getBookKey();
    let data = JSON.parse(localStorage.getItem(key) || '{{"count":0,"liked":false}}');
    if (data.liked) {{
      data.count = Math.max(0, data.count - 1);
      data.liked = false;
    }} else {{
      data.count += 1;
      data.liked = true;
    }}
    localStorage.setItem(key, JSON.stringify(data));
    updateLikeUI(data.count, data.liked);
  }}
  function updateLikeUI(count, liked) {{
    document.getElementById('likeIcon').textContent = liked ? '❤️' : '🤍';
    document.getElementById('likeCount').textContent = count;
    const btn = document.getElementById('likeBtn');
    if (liked) {{
      btn.style.background = 'rgba(239,68,68,0.1)';
    }} else {{
      btn.style.background = 'none';
    }}
  }}
  function loadThought() {{
    const key = location.pathname.split('/').pop() + '_thought';
    const content = localStorage.getItem(key);
    if (content) {{
      document.getElementById('thoughtContent').value = content;
    }}
  }}
  function saveThought() {{
    const key = location.pathname.split('/').pop() + '_thought';
    const content = document.getElementById('thoughtContent').value;
    localStorage.setItem(key, content);
    const btn = event.target;
    const originalText = btn.textContent;
    btn.textContent = '✓ 已保存';
    btn.style.background = '{THEME["primary_dark"]}';
    setTimeout(function() {{
      btn.textContent = originalText;
      btn.style.background = '';
    }}, 1500);
  }}
  initLike();
  loadThought();

</script>
<script src="../../annotation.js"></script>
<script src="../../toc.js"></script>

</body>
</html>'''
    
    with open(REPORT_HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'研报页已生成: {REPORT_HTML_PATH}')
    print(f'  二级标题数: {h2_count}')
    print(f'  三级标题数: {h3_count}')

if __name__ == '__main__':
    generate_essence_page()
    generate_report_page()
    print('\n✅ 两页生成完成！')
