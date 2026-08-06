// 通用自动目录导航 - 精华页 & 研报页通用
// 研报页：左侧折叠式目录（可收起/展开）
// 精华页：右侧悬浮目录（保持原有样式）
(function() {
  document.addEventListener('DOMContentLoaded', function() {
    // 判断当前页面类型
    const isReportPage = document.querySelector('.report-content') !== null;
    const hasHero = document.querySelector('.hero') !== null;

    // 收集所有标题（h2和h3）
    let headings = [];
    const allH2 = document.querySelectorAll('h2');
    const allH3 = document.querySelectorAll('h3');

    // 过滤：只取正文区域的标题，跳过nav/hero/footer里的
    allH2.forEach(function(h) {
      if (isInContentArea(h)) headings.push({ el: h, level: 2 });
    });
    allH3.forEach(function(h) {
      if (isInContentArea(h)) headings.push({ el: h, level: 3 });
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
              cls.includes('toc-sidebar') || cls.includes('annotation') ||
              cls.includes('auto-toc')) {
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

    // 给标题加id（确保不重复且稳定）
    let idCounter = 0;
    headings.forEach(function(item) {
      if (!item.el.id) {
        const text = item.el.textContent.trim();
        const slug = text.replace(/[^\w\u4e00-\u9fa5]/g, '').substring(0, 20);
        item.el.id = 'toc-' + (slug || 'sec') + '-' + idCounter++;
      }
    });

    // 创建侧边栏
    const sidebar = document.createElement('div');
    if (isReportPage) {
      sidebar.className = 'auto-toc-sidebar toc-left toc-collapsible';
      sidebar.innerHTML =
        '<button class="toc-toggle-btn" aria-label="收起目录" title="收起/展开目录">📑</button>' +
        '<div class="auto-toc-inner">' +
        '<h4 class="auto-toc-title">目录导航</h4>' +
        '<ul class="auto-toc-list"></ul>' +
        '</div>';
    } else {
      sidebar.className = 'auto-toc-sidebar toc-right';
      sidebar.innerHTML =
        '<div class="auto-toc-inner">' +
        '<h4 class="auto-toc-title">📑 目录导航</h4>' +
        '<ul class="auto-toc-list"></ul>' +
        '</div>';
    }

    const list = sidebar.querySelector('.auto-toc-list');
    headings.forEach(function(item, idx) {
      const li = document.createElement('li');
      li.className = 'auto-toc-item auto-toc-level-' + item.level;
      const a = document.createElement('a');
      a.href = '#' + item.el.id;
      a.className = 'auto-toc-link';
      a.dataset.index = idx;
      a.textContent = item.el.textContent.trim();
      li.appendChild(a);
      list.appendChild(li);
    });

    document.body.appendChild(sidebar);

    // 样式
    const style = document.createElement('style');
    // 基础样式 + 右侧（精华页）样式 + 左侧（研报页）折叠样式
    style.textContent = `
      /* ===== 基础样式 ===== */
      .auto-toc-link {
        text-decoration: none;
        display: block;
        line-height: 1.5;
        transition: all 0.2s ease;
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
      .auto-toc-list {
        list-style: none;
        padding: 0;
        margin: 0;
      }
      .auto-toc-item { margin-bottom: 2px; }

      /* ===== 右侧目录（精华页） ===== */
      .auto-toc-sidebar.toc-right {
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
      .auto-toc-sidebar.toc-right.show { opacity: 1; }
      .toc-right .auto-toc-inner {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 12px;
        padding: 16px 12px;
        border: 1px solid rgba(0,0,0,0.06);
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
      }
      .toc-right .auto-toc-title {
        font-size: 13px;
        font-weight: 600;
        color: var(--primary, #3b82f6);
        margin: 0 0 12px 4px;
        padding-bottom: 8px;
        border-bottom: 2px solid var(--primary, #3b82f6);
      }
      .toc-right .auto-toc-link {
        padding: 6px 10px;
        font-size: 12.5px;
        color: #64748b;
        border-radius: 6px;
        border-left: 2px solid transparent;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .toc-right .auto-toc-level-3 .auto-toc-link {
        padding-left: 24px;
        font-size: 12px;
        color: #94a3b8;
      }
      .toc-right .auto-toc-level-3 .auto-toc-link.active {
        color: var(--primary, #3b82f6);
      }
      .toc-right::-webkit-scrollbar { width: 4px; }
      .toc-right::-webkit-scrollbar-track { background: transparent; }
      .toc-right::-webkit-scrollbar-thumb {
        background: rgba(0,0,0,0.15);
        border-radius: 2px;
      }

      /* ===== 左侧折叠目录（研报页） ===== */
      .auto-toc-sidebar.toc-left {
        position: fixed;
        left: calc(50% - 480px - 220px - 40px);
        top: 120px;
        width: 220px;
        max-height: calc(100vh - 150px);
        overflow-y: auto;
        overflow-x: hidden;
        z-index: 90;
        transition: transform 0.3s ease, opacity 0.3s ease;
      }
      .toc-left .auto-toc-inner {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 12px;
        padding: 14px 10px;
        border: 1px solid rgba(0,0,0,0.08);
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
      }
      .toc-left .auto-toc-title {
        font-size: 13px;
        font-weight: 600;
        color: var(--primary, #3b82f6);
        margin: 0 0 10px 6px;
        padding-bottom: 8px;
        border-bottom: 2px solid var(--primary, #3b82f6);
        display: flex;
        align-items: center;
        gap: 6px;
      }
      .toc-left .auto-toc-title::before {
        content: '📑';
        font-size: 14px;
      }
      .toc-left .auto-toc-link {
        padding: 6px 10px;
        font-size: 13px;
        color: #64748b;
        border-radius: 6px;
        border-left: 2px solid transparent;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .toc-left .auto-toc-level-3 .auto-toc-link {
        padding-left: 26px;
        font-size: 12px;
        color: #94a3b8;
      }
      .toc-left .auto-toc-level-3 .auto-toc-link.active {
        color: var(--primary, #3b82f6);
      }

      /* 折叠/展开按钮 */
      .toc-toggle-btn {
        position: absolute;
        top: 10px;
        right: -40px;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: var(--primary, #3b82f6);
        color: white;
        border: none;
        cursor: pointer;
        font-size: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.15);
        z-index: 91;
        transition: transform 0.3s ease;
      }
      .toc-toggle-btn:hover {
        transform: scale(1.1);
      }

      /* 收起状态 */
      .auto-toc-sidebar.toc-left.toc-collapsed {
        transform: translateX(calc(-100% - 20px));
      }
      .auto-toc-sidebar.toc-left.toc-collapsed .toc-toggle-btn {
        right: -56px;
        transform: rotate(180deg);
      }

      /* 滚动条 */
      .toc-left::-webkit-scrollbar { width: 4px; }
      .toc-left::-webkit-scrollbar-track { background: transparent; }
      .toc-left::-webkit-scrollbar-thumb {
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
        // 使用 getBoundingClientRect 更准确
        const rect = headings[i].el.getBoundingClientRect();
        const headingTop = rect.top + window.scrollY;
        if (headingTop <= scrollPos) {
          currentIdx = i;
        } else {
          break;
        }
      }

      tocLinks.forEach(function(link, idx) {
        if (idx === currentIdx) {
          link.classList.add('active');
          // 滚动到可视区域（侧边栏内）
          const sidebarEl = sidebar;
          if (link.offsetTop < sidebarEl.scrollTop ||
              link.offsetTop + link.offsetHeight > sidebarEl.scrollTop + sidebarEl.clientHeight) {
            link.scrollIntoView({ block: 'nearest' });
          }
        } else {
          link.classList.remove('active');
        }
      });
    }

    // 点击平滑滚动
    function handleTocClick(e) {
      e.preventDefault();
      e.stopPropagation();
      const href = this.getAttribute('href');
      if (!href || !href.startsWith('#')) return;
      const target = document.querySelector(href);
      if (!target) return;

      // 计算目标位置（考虑顶部导航等偏移）
      const offset = 80;
      const targetTop = target.getBoundingClientRect().top + window.scrollY - offset;

      window.scrollTo({
        top: targetTop,
        behavior: 'smooth'
      });

      // 研报页：点击后自动收起目录
      if (isReportPage && sidebar.classList.contains('toc-collapsible')) {
        // 稍微延迟一下，让用户看到跳转后再收起
        setTimeout(function() {
          sidebar.classList.add('toc-collapsed');
        }, 400);
      }
    }

    tocLinks.forEach(function(link) {
      link.addEventListener('click', handleTocClick);
    });

    // 折叠/展开按钮（仅研报页）
    if (isReportPage) {
      const toggleBtn = sidebar.querySelector('.toc-toggle-btn');
      if (toggleBtn) {
        toggleBtn.addEventListener('click', function(e) {
          e.stopPropagation();
          sidebar.classList.toggle('toc-collapsed');
          const isCollapsed = sidebar.classList.contains('toc-collapsed');
          toggleBtn.setAttribute('aria-label', isCollapsed ? '展开目录' : '收起目录');
          toggleBtn.setAttribute('title', isCollapsed ? '展开目录' : '收起目录');
        });
      }
    }

    // 显示 & 初始化高亮
    setTimeout(function() {
      sidebar.classList.add('show');
      updateActive();
    }, 200);

    // 滚动监听（防抖优化）
    let scrollTimer = null;
    window.addEventListener('scroll', function() {
      if (scrollTimer) return;
      scrollTimer = setTimeout(function() {
        scrollTimer = null;
        updateActive();
      }, 80);
    }, { passive: true });

    // 响应 hash 直接跳转
    if (window.location.hash) {
      const target = document.querySelector(window.location.hash);
      if (target) {
        setTimeout(function() {
          const targetTop = target.getBoundingClientRect().top + window.scrollY - 80;
          window.scrollTo({ top: targetTop, behavior: 'smooth' });
        }, 300);
      }
    }
  });
})();
