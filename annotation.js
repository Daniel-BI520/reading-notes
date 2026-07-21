/**
 * Annotation System - Text Highlight & Comment with Gist Sync
 * Pure vanilla JS, no dependencies
 * 
 * Data structures:
 * 
 * localStorage (per-book, for local cache/fallback):
 * key: book_annotations_{filename}
 * value: [{ id, text, context_before, context_after, comment, type, author, created_at, startOffset, endOffset }]
 * 
 * GitHub Gist (all books in one file):
 * file: annotations.json
 * {
 *   books: {
 *     "book_001_tech_product_marketing": [{...}, ...]
 *   },
 *   version: timestamp
 * }
 */

(function() {
  'use strict';

  // ============= Configuration =============
  const CONFIG = {
    contextLength: 20,
    storagePrefix: 'book_annotations_',
    highlightClass: 'annot-highlight',
    highlightTagName: 'mark',
    gistDescription: 'reading-notes-annotations',
    gistFilename: 'annotations.json',
    tokenKey: 'github_token',
    readerKey: 'reader_id',
    gistIdKey: 'gist_id'
  };

  // ============= State =============
  let annotations = [];
  let currentSelection = null;
  let currentRange = null;
  let bookKey = '';
  let fullTextCache = '';
  let textNodesCache = [];
  let syncState = 'offline'; // offline | syncing | synced | error
  let gistId = null;
  let syncTimer = null;

  // ============= DOM Elements =============
  let toolbar = null;
  let popup = null;
  let tooltip = null;
  let sidebar = null;
  let sidebarToggle = null;
  let sidebarList = null;
  let sidebarCount = null;
  let loginModal = null;

  // ============= Initialization =============
  function init() {
    bookKey = getBookKey();
    if (!bookKey) return;

    // Ensure reader ID
    ensureReaderId();

    // Build UI elements
    buildToolbar();
    buildPopup();
    buildTooltip();
    buildSidebar();
    buildLoginModal();
    injectSyncButton();

    // Load from local first
    loadFromLocal();

    // Rebuild text cache
    rebuildTextCache();

    // Render initial highlights
    renderAllAnnotations();

    // Bind events
    bindEvents();

    // Update UI
    updateSidebarCount();
    updateSyncStatus('offline');

    // Try Gist sync if token exists
    const token = getToken();
    if (token) {
      syncFromGist();
    }
  }

  function getBookKey() {
    const path = window.location.pathname;
    const parts = path.split('/');
    const file = parts[parts.length - 1];
    if (!file) return null;
    return file.replace(/\.html?$/, '');
  }

  // ============= Reader ID =============
  function ensureReaderId() {
    let readerId = localStorage.getItem(CONFIG.readerKey);
    if (!readerId) {
      const hex = Math.floor(Math.random() * 0x10000).toString(16).toUpperCase().padStart(4, '0');
      readerId = '读者#' + hex;
      localStorage.setItem(CONFIG.readerKey, readerId);
    }
    return readerId;
  }

  function getReaderId() {
    return localStorage.getItem(CONFIG.readerKey) || ensureReaderId();
  }

  function setReaderId(name) {
    localStorage.setItem(CONFIG.readerKey, name);
  }

  // ============= Token Management =============
  function getToken() {
    return localStorage.getItem(CONFIG.tokenKey) || '';
  }

  function setToken(token) {
    if (token) {
      localStorage.setItem(CONFIG.tokenKey, token);
    } else {
      localStorage.removeItem(CONFIG.tokenKey);
    }
    gistId = null;
    localStorage.removeItem(CONFIG.gistIdKey);
  }

  // ============= Storage Layer =============
  
  // --- Local Storage ---
  function loadFromLocal() {
    try {
      const key = CONFIG.storagePrefix + bookKey;
      const data = localStorage.getItem(key);
      annotations = data ? JSON.parse(data) : [];
    } catch (e) {
      console.warn('Failed to load local annotations:', e);
      annotations = [];
    }
  }

  function saveToLocal() {
    try {
      const key = CONFIG.storagePrefix + bookKey;
      localStorage.setItem(key, JSON.stringify(annotations));
    } catch (e) {
      console.warn('Failed to save local annotations:', e);
    }
  }

  // --- Gist API ---
  async function findOrCreateGist() {
    const token = getToken();
    if (!token) return null;

    // Check cached gist ID
    if (!gistId) {
      gistId = localStorage.getItem(CONFIG.gistIdKey);
    }

    if (gistId) {
      // Verify it still exists
      try {
        const gist = await gistApi('GET', `gists/${gistId}`);
        if (gist && gist.description === CONFIG.gistDescription) {
          return gist;
        }
      } catch (e) {
        // Not found or invalid, recreate
        gistId = null;
      }
    }

    // Search for existing gist by description
    try {
      const gists = await gistApi('GET', 'gists?per_page=100');
      const found = gists.find(g => g.description === CONFIG.gistDescription);
      if (found) {
        gistId = found.id;
        localStorage.setItem(CONFIG.gistIdKey, gistId);
        return found;
      }
    } catch (e) {
      console.warn('Failed to list gists:', e);
    }

    // Create new gist
    try {
      const newGist = await gistApi('POST', 'gists', {
        description: CONFIG.gistDescription,
        public: false,
        files: {
          [CONFIG.gistFilename]: {
            content: JSON.stringify({ books: {}, version: Date.now() }, null, 2)
          }
        }
      });
      gistId = newGist.id;
      localStorage.setItem(CONFIG.gistIdKey, gistId);
      return newGist;
    } catch (e) {
      console.error('Failed to create gist:', e);
      throw e;
    }
  }

  async function gistApi(method, path, body) {
    const token = getToken();
    const url = `https://api.github.com/${path}`;
    
    const options = {
      method: method,
      headers: {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': `token ${token}`,
        'Content-Type': 'application/json'
      }
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);
    
    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`GitHub API ${response.status}: ${errText}`);
    }

    return response.json();
  }

  async function syncFromGist() {
    updateSyncStatus('syncing');
    
    try {
      const gist = await findOrCreateGist();
      if (!gist) throw new Error('无法获取 Gist');

      const file = gist.files[CONFIG.gistFilename];
      if (!file) throw new Error('Gist 文件不存在');

      let remoteData;
      try {
        // files content is already inline for GET /gists/{id}, but may be truncated
        if (file.truncated && file.raw_url) {
          const rawResp = await fetch(file.raw_url);
          remoteData = await rawResp.json();
        } else {
          remoteData = JSON.parse(file.content);
        }
      } catch (e) {
        remoteData = { books: {}, version: 0 };
      }

      // Merge: combine local and remote for this book
      const remoteBookAnns = (remoteData.books && remoteData.books[bookKey]) || [];
      
      if (remoteBookAnns.length > 0) {
        annotations = mergeAnnotations(annotations, remoteBookAnns);
        saveToLocal();
        rebuildTextCache();
        renderAllAnnotations();
        updateSidebarCount();
        renderSidebarList();
      }

      updateSyncStatus('synced');
      
      // Clear error state after 3s
      setTimeout(() => {
        if (syncState === 'synced') {
          updateSyncStatus('offline');
        }
      }, 3000);
      
    } catch (e) {
      console.error('Sync failed:', e);
      updateSyncStatus('error');
    }
  }

  async function syncToGist() {
    const token = getToken();
    if (!token) return;

    // Debounce
    if (syncTimer) clearTimeout(syncTimer);
    syncTimer = setTimeout(doSyncToGist, 800);
  }

  async function doSyncToGist() {
    const token = getToken();
    if (!token) return;

    updateSyncStatus('syncing');

    try {
      const gist = await findOrCreateGist();
      if (!gist) throw new Error('无法获取 Gist');

      // Get current content
      let remoteData;
      const file = gist.files[CONFIG.gistFilename];
      try {
        if (file.truncated && file.raw_url) {
          const rawResp = await fetch(file.raw_url);
          remoteData = await rawResp.json();
        } else {
          remoteData = JSON.parse(file.content);
        }
      } catch (e) {
        remoteData = { books: {}, version: 0 };
      }

      if (!remoteData.books) remoteData.books = {};

      // Update this book's annotations (merge with remote for all books)
      const remoteBookAnns = remoteData.books[bookKey] || [];
      const merged = mergeAnnotations(annotations, remoteBookAnns);
      remoteData.books[bookKey] = merged;
      remoteData.version = Date.now();

      // Update local annotations with merged result
      annotations = merged;
      saveToLocal();

      // Update gist
      await gistApi('PATCH', `gists/${gistId}`, {
        files: {
          [CONFIG.gistFilename]: {
            content: JSON.stringify(remoteData, null, 2)
          }
        }
      });

      updateSyncStatus('synced');
      setTimeout(() => {
        if (syncState === 'synced') {
          updateSyncStatus('offline');
        }
      }, 3000);

    } catch (e) {
      console.error('Push to gist failed:', e);
      updateSyncStatus('error');
    }
  }

  // Merge two annotation arrays by ID (latest wins)
  function mergeAnnotations(local, remote) {
    const map = new Map();
    
    for (const ann of local) {
      map.set(ann.id, { ...ann, _local: true });
    }
    
    for (const ann of remote) {
      const existing = map.get(ann.id);
      if (!existing) {
        map.set(ann.id, { ...ann });
      } else {
        // Newer timestamp wins
        const existingTime = existing.created_at || 0;
        const remoteTime = ann.created_at || 0;
        if (remoteTime >= existingTime) {
          map.set(ann.id, { ...ann });
        }
      }
    }

    return Array.from(map.values()).sort((a, b) => (a.startOffset || 0) - (b.startOffset || 0));
  }

  // ============= Sync Status =============
  function updateSyncStatus(state) {
    syncState = state;
    const icons = document.querySelectorAll('.annot-sync-icon');
    icons.forEach(icon => {
      icon.classList.remove('syncing', 'synced', 'error');
      switch (state) {
        case 'syncing':
          icon.classList.add('syncing');
          icon.textContent = '☁️';
          icon.title = '同步中...';
          break;
        case 'synced':
          icon.classList.add('synced');
          icon.textContent = '✓';
          icon.title = '已同步';
          break;
        case 'error':
          icon.classList.add('error');
          icon.textContent = '⚠️';
          icon.title = '同步失败';
          break;
        default:
          const token = getToken();
          icon.textContent = token ? '☁️' : '🔒';
          icon.title = token ? '云同步已开启' : '未登录 (本地模式)';
      }
    });

    // Update sync button text in sidebar/nav
    const btnTexts = document.querySelectorAll('.annot-sync-text');
    btnTexts.forEach(el => {
      switch (state) {
        case 'syncing': el.textContent = '同步中'; break;
        case 'synced': el.textContent = '已同步'; break;
        case 'error': el.textContent = '同步失败'; break;
        default:
          const token = getToken();
          el.textContent = token ? '云同步' : '登录同步';
      }
    });
  }

  // ============= Inject Sync Button =============
  function injectSyncButton() {
    // Try to find nav-actions (精华页 style)
    const navActions = document.querySelector('.nav-actions');
    
    if (navActions) {
      const btn = document.createElement('button');
      btn.className = 'nav-btn annot-sync-btn';
      btn.id = 'annotSyncBtn';
      btn.innerHTML = `
        <span class="annot-sync-icon">🔒</span>
        <span class="annot-sync-text">登录同步</span>
      `;
      btn.addEventListener('click', openLoginModal);
      navActions.insertBefore(btn, navActions.firstChild);
      return;
    }

    // Try to find top-nav-inner (研报页 style)
    const topNavInner = document.querySelector('.top-nav-inner');
    if (topNavInner) {
      const wrap = document.createElement('div');
      wrap.style.cssText = 'display:inline-flex;align-items:center;gap:10px;';
      
      // Find existing right-aligned links
      const rightLinks = topNavInner.querySelector('.nav-link.right');
      
      const btn = document.createElement('a');
      btn.href = 'javascript:void(0)';
      btn.className = 'nav-link annot-sync-btn';
      btn.id = 'annotSyncBtn';
      btn.style.cssText = 'display:inline-flex;align-items:center;gap:4px;';
      btn.innerHTML = `
        <span class="annot-sync-icon">🔒</span>
        <span class="annot-sync-text">登录同步</span>
      `;
      btn.addEventListener('click', openLoginModal);

      if (rightLinks) {
        wrap.appendChild(btn);
        wrap.appendChild(rightLinks.cloneNode(true));
        rightLinks.replaceWith(wrap);
      } else {
        topNavInner.appendChild(btn);
      }
      return;
    }

    // Fallback: just a floating button
    const btn = document.createElement('button');
    btn.id = 'annotSyncBtn';
    btn.className = 'annot-sync-btn';
    btn.style.cssText = `
      position: fixed; top: 10px; right: 10px; z-index: 100;
      background: rgba(15, 23, 42, 0.9); color: white;
      border: none; padding: 8px 14px; border-radius: 6px; cursor: pointer;
      font-size: 13px;
    `;
    btn.innerHTML = `<span class="annot-sync-icon">🔒</span> <span class="annot-sync-text">登录同步</span>`;
    btn.addEventListener('click', openLoginModal);
    document.body.appendChild(btn);
  }

  // ============= Login Modal =============
  function buildLoginModal() {
    loginModal = document.createElement('div');
    loginModal.className = 'annot-login-modal';
    loginModal.innerHTML = `
      <div class="annot-login-box" onclick="event.stopPropagation()">
        <div class="annot-login-title">
          <span>🔑</span>
          <span>云同步设置</span>
        </div>
        <div class="annot-login-subtitle">
          使用 GitHub Gist 保存批注，多设备同步
        </div>
        
        <div class="annot-login-status" id="annotLoginStatus"></div>
        
        <div id="annotLoggedSection" style="display:none;">
          <div class="annot-login-logged">
            <span>✓ 已登录</span>
            <button type="button" id="annotLogoutBtn">退出登录</button>
          </div>
        </div>
        
        <div id="annotTokenSection">
          <div class="annot-login-label">GitHub Personal Access Token</div>
          <input type="password" class="annot-login-input" id="annotTokenInput" placeholder="ghp_xxxxxxxxxxxx" autocomplete="off">
          <div class="annot-login-hint">
            仅勾选 <code>gist</code> 权限即可<br>
            创建路径：GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
          </div>
        </div>

        <div class="annot-reader-section">
          <div class="annot-login-label">
            <span>你的昵称</span>
            <span id="annotRandomReader">随机生成</span>
          </div>
          <input type="text" class="annot-login-input" id="annotReaderInput" placeholder="读者#A7F2" maxlength="20">
          <div class="annot-login-hint">
            批注时会显示你的昵称，方便多人协作时区分
          </div>
        </div>
        
        <div class="annot-login-actions">
          <button class="annot-btn-outline" id="annotLoginCancel">取消</button>
          <button class="annot-btn-primary" id="annotLoginSave">保存并同步</button>
        </div>
      </div>
    `;
    document.body.appendChild(loginModal);

    // Events
    loginModal.addEventListener('click', closeLoginModal);
    
    loginModal.querySelector('#annotLoginCancel').addEventListener('click', closeLoginModal);
    loginModal.querySelector('#annotLoginSave').addEventListener('click', handleLoginSave);
    loginModal.querySelector('#annotLogoutBtn').addEventListener('click', handleLogout);
    loginModal.querySelector('#annotRandomReader').addEventListener('click', randomizeReader);
    
    // Enter key to save
    loginModal.querySelector('#annotTokenInput').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleLoginSave();
    });
    loginModal.querySelector('#annotReaderInput').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleLoginSave();
    });
  }

  function openLoginModal() {
    // Populate current values
    const tokenInput = loginModal.querySelector('#annotTokenInput');
    const readerInput = loginModal.querySelector('#annotReaderInput');
    const loggedSection = loginModal.querySelector('#annotLoggedSection');
    const tokenSection = loginModal.querySelector('#annotTokenSection');
    const status = loginModal.querySelector('#annotLoginStatus');
    
    const token = getToken();
    tokenInput.value = token || '';
    readerInput.value = getReaderId();
    status.classList.remove('show', 'error', 'success');
    status.textContent = '';

    if (token) {
      loggedSection.style.display = 'block';
      tokenSection.style.display = 'none';
    } else {
      loggedSection.style.display = 'none';
      tokenSection.style.display = 'block';
    }

    loginModal.classList.add('show');
    
    if (!token) {
      setTimeout(() => tokenInput.focus(), 100);
    }
  }

  function closeLoginModal() {
    loginModal.classList.remove('show');
  }

  async function handleLoginSave() {
    const token = loginModal.querySelector('#annotTokenInput').value.trim();
    const readerName = loginModal.querySelector('#annotReaderInput').value.trim();
    const status = loginModal.querySelector('#annotLoginStatus');
    
    // Save reader name
    if (readerName) {
      setReaderId(readerName);
    }

    // Save token and test
    if (token) {
      setToken(token);
      status.classList.add('show');
      status.classList.remove('error');
      status.classList.add('success');
      status.textContent = '正在验证并同步...';
      
      try {
        await syncFromGist();
        status.textContent = '✓ 同步成功！';
        updateSyncStatus('synced');
        setTimeout(() => {
          closeLoginModal();
          updateSyncStatus('offline');
        }, 1000);
      } catch (e) {
        status.classList.remove('success');
        status.classList.add('error');
        status.textContent = '同步失败：' + (e.message || '请检查 Token 是否正确');
        updateSyncStatus('error');
      }
    } else {
      // Just saved reader name
      closeLoginModal();
    }
  }

  function handleLogout() {
    if (confirm('确定退出登录？退出后批注仍保留在本地。')) {
      setToken('');
      updateSyncStatus('offline');
      closeLoginModal();
    }
  }

  function randomizeReader() {
    const hex = Math.floor(Math.random() * 0x10000).toString(16).toUpperCase().padStart(4, '0');
    const newId = '读者#' + hex;
    loginModal.querySelector('#annotReaderInput').value = newId;
  }

  // ============= Text Cache =============
  function rebuildTextCache() {
    textNodesCache = [];
    fullTextCache = '';
    
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: function(node) {
          const parent = node.parentElement;
          if (!parent) return NodeFilter.FILTER_REJECT;
          if (parent.closest('script, style, .annot-toolbar, .annot-popup, .annot-tooltip, .annot-sidebar, .annot-sidebar-toggle, .annot-login-modal, #annotSyncBtn, .annot-sync-btn')) {
            return NodeFilter.FILTER_REJECT;
          }
          if (!node.nodeValue || node.nodeValue.trim() === '') {
            return NodeFilter.FILTER_REJECT;
          }
          return NodeFilter.FILTER_ACCEPT;
        }
      }
    );

    let node;
    let offset = 0;
    while (node = walker.nextNode()) {
      const text = node.nodeValue;
      textNodesCache.push({
        node: node,
        start: offset,
        end: offset + text.length,
        length: text.length
      });
      fullTextCache += text;
      offset += text.length;
    }
  }

  function rangeToOffset(range) {
    let startOffset = 0;
    let endOffset = 0;
    let foundStart = false;
    let foundEnd = false;

    for (const tn of textNodesCache) {
      if (!foundStart && tn.node === range.startContainer) {
        startOffset = tn.start + range.startOffset;
        foundStart = true;
      }
      if (!foundEnd && tn.node === range.endContainer) {
        endOffset = tn.start + range.endOffset;
        foundEnd = true;
        break;
      }
    }

    return { start: startOffset, end: endOffset };
  }

  function offsetToRange(startOffset, endOffset) {
    let startNode = null;
    let startNodeOffset = 0;
    let endNode = null;
    let endNodeOffset = 0;

    for (const tn of textNodesCache) {
      if (!startNode && startOffset >= tn.start && startOffset <= tn.end) {
        startNode = tn.node;
        startNodeOffset = startOffset - tn.start;
      }
      if (!endNode && endOffset >= tn.start && endOffset <= tn.end) {
        endNode = tn.node;
        endNodeOffset = endOffset - tn.start;
        break;
      }
    }

    if (!startNode || !endNode) return null;

    const range = document.createRange();
    try {
      range.setStart(startNode, startNodeOffset);
      range.setEnd(endNode, endNodeOffset);
      return range;
    } catch (e) {
      return null;
    }
  }

  // ============= Selection =============
  function handleSelection() {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) {
      hideToolbar();
      currentSelection = null;
      currentRange = null;
      return;
    }

    const text = selection.toString().trim();
    if (!text || text.length < 1) {
      hideToolbar();
      return;
    }

    const range = selection.getRangeAt(0);
    const container = range.commonAncestorContainer;
    const el = container.nodeType === 1 ? container : container.parentElement;
    if (el.closest('.annot-toolbar, .annot-popup, .annot-tooltip, .annot-sidebar, .annot-sidebar-toggle, .annot-login-modal, .annot-sync-btn')) {
      return;
    }

    currentSelection = text;
    currentRange = range.cloneRange();
    showToolbar(range);
  }

  function showToolbar(range) {
    if (!toolbar) return;

    const rect = range.getBoundingClientRect();
    const toolbarRect = toolbar.getBoundingClientRect();
    
    let top = rect.top + window.scrollY - toolbarRect.height - 8;
    let left = rect.left + window.scrollX + (rect.width / 2) - (toolbarRect.width / 2);

    if (left < 10) left = 10;
    if (left + toolbarRect.width > window.innerWidth - 10) {
      left = window.innerWidth - toolbarRect.width - 10;
    }
    
    if (top < window.scrollY + 10) {
      top = rect.bottom + window.scrollY + 8;
    }

    toolbar.style.top = top + 'px';
    toolbar.style.left = left + 'px';
    toolbar.classList.add('show');
  }

  function showToolbarAt(x, y) {
    if (!toolbar) return;
    
    const toolbarRect = toolbar.getBoundingClientRect();
    let top = y + window.scrollY - toolbarRect.height - 8;
    let left = x + window.scrollX - toolbarRect.width / 2;
    
    if (left < 10) left = 10;
    if (top < window.scrollY + 10) {
      top = y + window.scrollY + 8;
    }
    
    toolbar.style.top = top + 'px';
    toolbar.style.left = left + 'px';
    toolbar.classList.add('show');
  }

  function hideToolbar() {
    if (toolbar) toolbar.classList.remove('show');
  }

  // ============= Create Highlight =============
  function createHighlight() {
    if (!currentRange) return;

    const offsets = rangeToOffset(currentRange);
    const text = currentSelection;
    
    const prefix = fullTextCache.substring(
      Math.max(0, offsets.start - CONFIG.contextLength),
      offsets.start
    );
    const suffix = fullTextCache.substring(
      offsets.end,
      Math.min(fullTextCache.length, offsets.end + CONFIG.contextLength)
    );

    const annotation = {
      id: generateId(),
      text: text,
      context_before: prefix,
      context_after: suffix,
      startOffset: offsets.start,
      endOffset: offsets.end,
      comment: '',
      type: 'highlight',
      author: getReaderId(),
      created_at: Date.now()
    };

    annotations.push(annotation);
    saveToLocal();
    syncToGist();
    
    renderAnnotation(annotation);
    
    window.getSelection().removeAllRanges();
    hideToolbar();
    
    rebuildTextCache();
    updateSidebarCount();
    renderSidebarList();
  }

  // ============= Render =============
  function renderAllAnnotations() {
    clearAllHighlights();
    
    const sorted = [...annotations].sort((a, b) => b.startOffset - a.startOffset);
    
    for (const ann of sorted) {
      renderAnnotation(ann);
    }
  }

  function renderAnnotation(annotation) {
    let range = offsetToRange(annotation.startOffset, annotation.endOffset);
    
    if (!range || range.toString() !== annotation.text) {
      const foundOffset = findByContext(annotation);
      if (foundOffset !== null) {
        annotation.startOffset = foundOffset.start;
        annotation.endOffset = foundOffset.end;
        range = offsetToRange(foundOffset.start, foundOffset.end);
      }
    }
    
    if (!range) return;
    
    try {
      const mark = document.createElement(CONFIG.highlightTagName);
      mark.className = CONFIG.highlightClass;
      mark.dataset.id = annotation.id;
      if (annotation.comment) {
        mark.classList.add('has-comment');
      }
      
      const contents = range.extractContents();
      mark.appendChild(contents);
      range.insertNode(mark);
    } catch (e) {
      console.warn('Failed to render annotation:', e);
    }
  }

  function clearAllHighlights() {
    const marks = document.querySelectorAll('mark.annot-highlight');
    marks.forEach(mark => {
      const parent = mark.parentNode;
      while (mark.firstChild) {
        parent.insertBefore(mark.firstChild, mark);
      }
      parent.removeChild(mark);
      parent.normalize();
    });
  }

  function findByContext(annotation) {
    const { text, context_before: prefix, context_after: suffix } = annotation;
    if (!text) return null;

    const pattern = prefix + text + suffix;
    const index = fullTextCache.indexOf(pattern);
    
    if (index !== -1) {
      return {
        start: index + prefix.length,
        end: index + prefix.length + text.length
      };
    }

    let lastIndex = 0;
    let bestMatch = null;
    let bestScore = -1;

    while (true) {
      const idx = fullTextCache.indexOf(text, lastIndex);
      if (idx === -1) break;
      
      const pre = fullTextCache.substring(
        Math.max(0, idx - CONFIG.contextLength),
        idx
      );
      const suf = fullTextCache.substring(
        idx + text.length,
        Math.min(fullTextCache.length, idx + text.length + CONFIG.contextLength)
      );
      
      let score = 0;
      for (let i = 1; i <= Math.min(pre.length, prefix.length); i++) {
        if (pre[pre.length - i] === prefix[prefix.length - i]) score++;
        else break;
      }
      for (let i = 0; i < Math.min(suf.length, suffix.length); i++) {
        if (suf[i] === suffix[i]) score++;
        else break;
      }
      
      if (score > bestScore) {
        bestScore = score;
        bestMatch = { start: idx, end: idx + text.length };
      }
      
      lastIndex = idx + 1;
    }

    return bestMatch;
  }

  // ============= Comment/Popup =============
  function openCommentPopup() {
    if (!currentRange) return;
    
    const offsets = rangeToOffset(currentRange);
    const text = currentSelection;
    
    const prefix = fullTextCache.substring(
      Math.max(0, offsets.start - CONFIG.contextLength),
      offsets.start
    );
    const suffix = fullTextCache.substring(
      offsets.end,
      Math.min(fullTextCache.length, offsets.end + CONFIG.contextLength)
    );

    const rect = currentRange.getBoundingClientRect();
    showPopup(rect, {
      id: null,
      text: text,
      context_before: prefix,
      context_after: suffix,
      startOffset: offsets.start,
      endOffset: offsets.end,
      comment: '',
      isNew: true
    });
    
    hideToolbar();
  }

  function editAnnotation(id) {
    const ann = annotations.find(a => a.id === id);
    if (!ann) return;

    const mark = document.querySelector(`mark.annot-highlight[data-id="${id}"]`);
    if (!mark) return;

    const rect = mark.getBoundingClientRect();
    showPopup(rect, {
      id: id,
      text: ann.text,
      comment: ann.comment,
      author: ann.author,
      isNew: false
    });
  }

  function showPopup(rect, data) {
    if (!popup) return;

    const textarea = popup.querySelector('textarea');
    const header = popup.querySelector('.annot-popup-header span');
    const deleteBtn = popup.querySelector('.annot-btn-delete');
    const authorEl = popup.querySelector('.annot-popup-author');
    
    header.textContent = data.isNew ? '添加批注' : '编辑批注';
    textarea.value = data.comment || '';
    deleteBtn.style.display = data.isNew ? 'none' : 'inline-block';
    
    if (data.isNew) {
      authorEl.innerHTML = `👤 ${getReaderId()}`;
    } else {
      authorEl.innerHTML = `👤 ${data.author || '未知'}`;
    }
    
    popup.dataset.annotationId = data.id || '';
    popup.dataset.isNew = data.isNew ? 'true' : 'false';
    
    if (data.isNew) {
      popup.dataset.newText = data.text;
      popup.dataset.newPrefix = data.context_before;
      popup.dataset.newSuffix = data.context_after;
      popup.dataset.newStart = data.startOffset;
      popup.dataset.newEnd = data.endOffset;
    }

    const popupRect = popup.getBoundingClientRect();
    let top = rect.top + window.scrollY - popupRect.height - 10;
    let left = rect.left + window.scrollX + (rect.width / 2) - (popupRect.width / 2);

    if (left < 10) left = 10;
    if (left + popupRect.width > window.innerWidth - 10) {
      left = window.innerWidth - popupRect.width - 10;
    }
    if (top < window.scrollY + 10) {
      top = rect.bottom + window.scrollY + 10;
    }

    popup.style.top = top + 'px';
    popup.style.left = left + 'px';
    popup.classList.add('show');
    
    setTimeout(() => textarea.focus(), 50);
  }

  function hidePopup() {
    if (popup) popup.classList.remove('show');
  }

  function saveComment() {
    if (!popup) return;
    
    const textarea = popup.querySelector('textarea');
    const comment = textarea.value.trim();
    const isNew = popup.dataset.isNew === 'true';
    const id = popup.dataset.annotationId;

    if (isNew) {
      const text = popup.dataset.newText;
      const prefix = popup.dataset.newPrefix;
      const suffix = popup.dataset.newSuffix;
      const startOffset = parseInt(popup.dataset.newStart);
      const endOffset = parseInt(popup.dataset.newEnd);

      const annotation = {
        id: generateId(),
        text: text,
        context_before: prefix,
        context_after: suffix,
        startOffset: startOffset,
        endOffset: endOffset,
        comment: comment,
        type: comment ? 'comment' : 'highlight',
        author: getReaderId(),
        created_at: Date.now()
      };

      annotations.push(annotation);
      saveToLocal();
      syncToGist();
      
      window.getSelection().removeAllRanges();
      
      rebuildTextCache();
      renderAllAnnotations();
      
    } else {
      const ann = annotations.find(a => a.id === id);
      if (ann) {
        ann.comment = comment;
        ann.type = comment ? 'comment' : 'highlight';
        ann.created_at = Date.now();
        saveToLocal();
        syncToGist();
        
        const mark = document.querySelector(`mark.annot-highlight[data-id="${id}"]`);
        if (mark) {
          if (comment) mark.classList.add('has-comment');
          else mark.classList.remove('has-comment');
        }
      }
    }

    hidePopup();
    updateSidebarCount();
    renderSidebarList();
  }

  function deleteAnnotation(id) {
    const idx = annotations.findIndex(a => a.id === id);
    if (idx === -1) return;

    annotations.splice(idx, 1);
    saveToLocal();
    syncToGist();
    
    rebuildTextCache();
    renderAllAnnotations();
    updateSidebarCount();
    renderSidebarList();
    hidePopup();
  }

  function deleteFromPopup() {
    const id = popup.dataset.annotationId;
    if (id) deleteAnnotation(id);
  }

  // ============= Tooltip =============
  function showTooltip(mark, event) {
    const id = mark.dataset.id;
    const ann = annotations.find(a => a.id === id);
    if (!ann || !ann.comment) return;

    if (!tooltip) return;
    
    tooltip.innerHTML = `
      ${escapeHtml(ann.comment)}
      <div class="annot-tooltip-author">— ${escapeHtml(ann.author || '未知')}</div>
    `;
    
    const rect = mark.getBoundingClientRect();
    let top = rect.top + window.scrollY - tooltip.offsetHeight - 8;
    let left = rect.left + window.scrollX;
    
    if (left + tooltip.offsetWidth > window.innerWidth - 10) {
      left = window.innerWidth - tooltip.offsetWidth - 10;
    }
    
    tooltip.style.top = top + 'px';
    tooltip.style.left = left + 'px';
    tooltip.classList.add('show');
  }

  function hideTooltip() {
    if (tooltip) tooltip.classList.remove('show');
  }

  // ============= Sidebar =============
  function buildSidebar() {
    sidebar = document.createElement('div');
    sidebar.className = 'annot-sidebar';
    sidebar.innerHTML = `
      <div class="annot-sidebar-header">
        <div class="annot-sidebar-title">
          <span>📝</span>
          <span>我的批注</span>
          <span class="annot-sidebar-count">0</span>
        </div>
        <button class="annot-sidebar-close" title="关闭">✕</button>
      </div>
      <div class="annot-sidebar-list"></div>
    `;
    document.body.appendChild(sidebar);

    sidebarList = sidebar.querySelector('.annot-sidebar-list');
    sidebarCount = sidebar.querySelector('.annot-sidebar-count');

    sidebarToggle = document.createElement('button');
    sidebarToggle.className = 'annot-sidebar-toggle';
    sidebarToggle.textContent = '📝 批注';
    sidebarToggle.title = '打开批注面板';
    document.body.appendChild(sidebarToggle);

    sidebarToggle.addEventListener('click', toggleSidebar);
    sidebar.querySelector('.annot-sidebar-close').addEventListener('click', toggleSidebar);
  }

  function toggleSidebar() {
    sidebar.classList.toggle('open');
    if (sidebar.classList.contains('open')) {
      renderSidebarList();
    }
  }

  function updateSidebarCount() {
    if (sidebarCount) {
      sidebarCount.textContent = annotations.length;
    }
  }

  function renderSidebarList() {
    if (!sidebarList) return;

    if (annotations.length === 0) {
      sidebarList.innerHTML = `
        <div class="annot-sidebar-empty">
          <div style="font-size: 32px; margin-bottom: 12px;">📖</div>
          <div>还没有批注</div>
          <div style="font-size: 12px; margin-top: 6px;">选中文字即可添加高亮和批注</div>
        </div>
      `;
      return;
    }

    const sorted = [...annotations].sort((a, b) => a.startOffset - b.startOffset);
    
    sidebarList.innerHTML = sorted.map(ann => {
      const time = new Date(ann.created_at).toLocaleString('zh-CN', {
        month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit'
      });
      const hasComment = ann.comment && ann.comment.length > 0;
      
      return `
        <div class="annot-item ${hasComment ? '' : 'no-comment'}" data-id="${ann.id}">
          <div class="annot-item-text">${escapeHtml(ann.text)}</div>
          <div class="annot-item-comment">${hasComment ? escapeHtml(ann.comment) : '（仅高亮）'}</div>
          <div class="annot-item-meta">
            <span class="annot-item-author">👤 ${escapeHtml(ann.author || '未知')}</span>
            <span class="annot-item-actions">
              <button class="annot-item-edit" title="编辑">✏️</button>
              <button class="annot-item-delete" title="删除">🗑️</button>
            </span>
          </div>
          <div style="font-size:10px;color:#ccc;margin-top:4px;">${time}</div>
        </div>
      `;
    }).join('');

    sidebarList.querySelectorAll('.annot-item').forEach(item => {
      const id = item.dataset.id;
      
      item.addEventListener('click', (e) => {
        if (e.target.closest('.annot-item-actions')) return;
        scrollToAnnotation(id);
      });
      
      item.querySelector('.annot-item-edit').addEventListener('click', (e) => {
        e.stopPropagation();
        scrollToAnnotation(id);
        setTimeout(() => editAnnotation(id), 300);
      });
      
      item.querySelector('.annot-item-delete').addEventListener('click', (e) => {
        e.stopPropagation();
        if (confirm('确定要删除这个批注吗？')) {
          deleteAnnotation(id);
        }
      });
    });
  }

  function scrollToAnnotation(id) {
    const mark = document.querySelector(`mark.annot-highlight[data-id="${id}"]`);
    if (!mark) return;

    mark.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    mark.classList.add('flash');
    setTimeout(() => mark.classList.remove('flash'), 1500);
  }

  // ============= UI Builders =============
  function buildToolbar() {
    toolbar = document.createElement('div');
    toolbar.className = 'annot-toolbar';
    toolbar.innerHTML = `
      <button class="annot-btn-highlight" title="高亮">
        <span>🟡</span><span>高亮</span>
      </button>
      <span class="annot-divider"></span>
      <button class="annot-btn-comment" title="批注">
        <span>📝</span><span>批注</span>
      </button>
      <span class="annot-divider"></span>
      <button class="annot-btn-close" title="关闭">✖</button>
    `;
    document.body.appendChild(toolbar);
  }

  function buildPopup() {
    popup = document.createElement('div');
    popup.className = 'annot-popup';
    popup.innerHTML = `
      <div class="annot-popup-header">
        <span>添加批注</span>
        <button class="annot-popup-close" title="关闭">✕</button>
      </div>
      <textarea placeholder="写下你的想法..."></textarea>
      <div class="annot-popup-author">👤 读者</div>
      <div class="annot-popup-actions">
        <button class="annot-btn-delete" style="display:none;">删除</button>
        <button class="annot-btn-cancel">取消</button>
        <button class="annot-btn-save">保存</button>
      </div>
    `;
    document.body.appendChild(popup);
  }

  function buildTooltip() {
    tooltip = document.createElement('div');
    tooltip.className = 'annot-tooltip';
    document.body.appendChild(tooltip);
  }

  // ============= Event Binding =============
  function bindEvents() {
    // Text selection
    document.addEventListener('mouseup', function(e) {
      setTimeout(() => {
        if (e.target.closest('.annot-toolbar, .annot-popup, .annot-sidebar, .annot-sidebar-toggle, .annot-login-modal')) {
          return;
        }
        handleSelection();
      }, 10);
    });

    // Keyboard
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        hideToolbar();
        hidePopup();
        hideTooltip();
        if (loginModal && loginModal.classList.contains('show')) {
          closeLoginModal();
        }
      }
    });

    // Toolbar buttons
    toolbar.querySelector('.annot-btn-highlight').addEventListener('mousedown', function(e) {
      e.preventDefault();
      e.stopPropagation();
      createHighlight();
    });

    toolbar.querySelector('.annot-btn-comment').addEventListener('mousedown', function(e) {
      e.preventDefault();
      e.stopPropagation();
      openCommentPopup();
    });

    toolbar.querySelector('.annot-btn-close').addEventListener('mousedown', function(e) {
      e.preventDefault();
      e.stopPropagation();
      window.getSelection().removeAllRanges();
      hideToolbar();
    });

    // Popup buttons
    popup.querySelector('.annot-popup-close').addEventListener('click', function(e) {
      e.stopPropagation();
      hidePopup();
    });

    popup.querySelector('.annot-btn-cancel').addEventListener('click', function(e) {
      e.stopPropagation();
      hidePopup();
    });

    popup.querySelector('.annot-btn-save').addEventListener('click', function(e) {
      e.stopPropagation();
      saveComment();
    });

    popup.querySelector('.annot-btn-delete').addEventListener('click', function(e) {
      e.stopPropagation();
      if (confirm('确定要删除这个批注吗？')) {
        deleteFromPopup();
      }
    });

    // Click on highlights
    document.addEventListener('click', function(e) {
      const mark = e.target.closest('mark.annot-highlight');
      if (mark) {
        const id = mark.dataset.id;
        const ann = annotations.find(a => a.id === id);
        if (ann && ann.comment) {
          editAnnotation(id);
        }
      } else if (popup && !popup.contains(e.target)) {
        hidePopup();
      }
    });

    // Hover tooltip
    document.addEventListener('mouseover', function(e) {
      const mark = e.target.closest('mark.annot-highlight');
      if (mark) {
        showTooltip(mark, e);
      }
    });

    document.addEventListener('mouseout', function(e) {
      const mark = e.target.closest('mark.annot-highlight');
      if (mark) {
        hideTooltip();
      }
    });

    // Context menu
    document.addEventListener('contextmenu', function(e) {
      const selection = window.getSelection();
      if (selection && !selection.isCollapsed && selection.toString().trim()) {
        e.preventDefault();
        const range = selection.getRangeAt(0);
        currentRange = range.cloneRange();
        currentSelection = selection.toString().trim();
        showToolbarAt(e.clientX, e.clientY);
      }
    });
  }

  // ============= Utilities =============
  function generateId() {
    return 'ann_' + Date.now().toString(36) + '_' + Math.random().toString(36).substr(2, 9);
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  // ============= Bootstrap =============
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Debug API
  window.__annotation = {
    getAnnotations: () => annotations,
    clearAll: () => { 
      annotations = []; 
      saveToLocal(); 
      syncToGist();
      rebuildTextCache(); 
      renderAllAnnotations(); 
      updateSidebarCount(); 
      renderSidebarList(); 
    },
    rebuild: () => { rebuildTextCache(); renderAllAnnotations(); },
    sync: () => syncFromGist(),
    push: () => syncToGist(),
    getBookKey: () => bookKey,
    getReaderId: getReaderId
  };

})();
