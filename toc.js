
// 通用自动目录导航 - 精华页 & 研报页通用
(function() {
  document.addEventListener('DOMContentLoaded', function() {
    // 收集所有标题（h2和h3）
    let headings = [];
    const allH2 = document.querySelectorAll('h2');
    const allH3 = document.querySelectorAll('h3');
    
    // 过滤：只取正文区域的标题，跳过nav/hero/footer里的
    allH2.forEach(function(h) {
      if (isInContentArea(h)) headings.push({el: h, level: 2});
    });
    allH3.forEach(function(h) {
      if (isInContentArea(h)) headings.push({el: h, level: 3});
    });
    
    // 按在页面中的位置排序
    headings.sort(function(a, b) {
      return a.el.offsetTop - b.el.offsetTop;
    });
    
    if (headings.length < 4) return; // 标题太少不显示
    
    function isInContentArea(el) {
      let parent = el;
      while (parent) {
        if (parent.className && typeof parent.className === 'string') {
          const cls = parent.className.toLowerCase();
          if (cls.includes('hero') || cls.includes('top-nav') || 
              cls.includes('footer') || cls.includes('nav-actions') ||
              cls.includes('toc-sidebar') || cls.includes('annotation')) {
            return false;
          }
        }
        if (parent.tagName === 'NAV' || parent.tagName === 'HEADER' || parent.tagName === 'FOOTER') {
          return false;
        }
        parent = parent.parentElement;
      }
      return true;
    }
    
    // 给标题加id
    let idCounter = 0;
    headings.forEach(function(item) {
      if (!item.el.id) {
        item.el.id = 'auto-toc-' + idCounter++;
      }
    });
    
    // 创建侧边栏
    const sidebar = document.createElement('div');
    sidebar.className = 'auto-toc-sidebar';
    sidebar.innerHTML = '<div class="auto-toc-inner"><h4 class="auto-toc-title">📑 目录导航</h4><ul class="auto-toc-list"></ul></div>';
    
    const list = sidebar.querySelector('.auto-toc-list');
    headings.forEach(function(item) {
      const li = document.createElement('li');
      li.className = 'auto-toc-item auto-toc-level-' + item.level;
      const a = document.createElement('a');
      a.href = '#' + item.el.id;
      a.className = 'auto-toc-link';
      a.textContent = item.el.textContent.trim().replace(/^\S+\s+/, function(m) {
        return m; // 保留emoji前缀
      });
      li.appendChild(a);
      list.appendChild(li);
    });
    
    document.body.appendChild(sidebar);
    
    // 样式
    const style = document.createElement('style');
    style.textContent = `
      .auto-toc-sidebar {
        position: fixed;
        right: calc(50% - 480px - 200px - 40px);
        top: 100px;
        width: 200px;
        max-height: calc(100vh - 130px);
        overflow-y: auto;
        z-index: 80;
        opacity: 0;
        transition: opacity 0.3s ease;
      }
      .auto-toc-sidebar.show { opacity: 1; }
      
      .auto-toc-inner {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 12px;
        padding: 16px 12px;
        border: 1px solid rgba(0,0,0,0.06);
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
      }
      
      .auto-toc-title {
        font-size: 13px;
        font-weight: 600;
        color: var(--primary, #3b82f6);
        margin: 0 0 12px 4px;
        padding-bottom: 8px;
        border-bottom: 2px solid var(--primary, #3b82f6);
      }
      
      .auto-toc-list {
        list-style: none;
        padding: 0;
        margin: 0;
      }
      
      .auto-toc-item { margin-bottom: 2px; }
      
      .auto-toc-link {
        display: block;
        padding: 6px 10px;
        font-size: 12.5px;
        color: #64748b;
        text-decoration: none;
        border-radius: 6px;
        line-height: 1.5;
        transition: all 0.2s ease;
        border-left: 2px solid transparent;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      
      .auto-toc-link:hover {
        background: rgba(0,0,0,0.04);
        color: #334155;
      }
      
      .auto-toc-link.active {
        color: var(--primary, #3b82f6);
        background: color-mix(in srgb, var(--primary, #3b82f6) 10%, transparent);
        border-left-color: var(--primary, #3b82f6);
        font-weight: 500;
      }
      
      .auto-toc-level-3 .auto-toc-link {
        padding-left: 24px;
        font-size: 12px;
        color: #94a3b8;
      }
      
      .auto-toc-level-3 .auto-toc-link.active {
        color: var(--primary, #3b82f6);
      }
      
      /* 滚动条 */
      .auto-toc-sidebar::-webkit-scrollbar { width: 4px; }
      .auto-toc-sidebar::-webkit-scrollbar-track { background: transparent; }
      .auto-toc-sidebar::-webkit-scrollbar-thumb {
        background: rgba(0,0,0,0.15);
        border-radius: 2px;
      }
      
      /* 小屏隐藏 */
      @media (max-width: 1400px) {
        .auto-toc-sidebar { display: none; }
      }
      
      /* 打印隐藏 */
      @media print {
        .auto-toc-sidebar { display: none !important; }
      }
    `;
    document.head.appendChild(style);
    
    // 滚动高亮
    const tocLinks = sidebar.querySelectorAll('.auto-toc-link');
    
    function updateActive() {
      let currentIdx = 0;
      const scrollPos = window.scrollY + 120;
      
      for (let i = 0; i < headings.length; i++) {
        if (headings[i].el.offsetTop <= scrollPos) {
          currentIdx = i;
        } else {
          break;
        }
      }
      
      tocLinks.forEach(function(link, idx) {
        if (idx === currentIdx) {
          link.classList.add('active');
          // 滚动到可视区域
          if (link.offsetTop < sidebar.scrollTop || 
              link.offsetTop + link.offsetHeight > sidebar.scrollTop + sidebar.clientHeight) {
            link.scrollIntoView({ block: 'nearest' });
          }
        } else {
          link.classList.remove('active');
        }
      });
    }
    
    setTimeout(function() {
      sidebar.classList.add('show');
      updateActive();
    }, 200);
    
    window.addEventListener('scroll', updateActive, { passive: true });
    
    // 点击平滑滚动
    tocLinks.forEach(function(link) {
      link.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
          window.scrollTo({
            top: target.offsetTop - 80,
            behavior: 'smooth'
          });
        }
      });
    });
  });
})();
