let currentScanData = null;
let selectedCategoryId = 'ALL';
let defaultDirs = {};
let loadedRules = null;

// DOM Elements
const folderInput = document.getElementById('folderPathInput');
const browseBtn = document.getElementById('browseFolderBtn');
const scanBtn = document.getElementById('scanBtn');
const organizeBtn = document.getElementById('organizeBtn');
const undoBtn = document.getElementById('undoBtn');
const undoLabel = document.getElementById('undoLabel');
const daemonToggleBtn = document.getElementById('daemonToggleBtn');
const daemonDot = document.getElementById('daemonDot');
const daemonText = document.getElementById('daemonText');
const searchInput = document.getElementById('searchInput');
const selectAllCheckbox = document.getElementById('selectAllCheckbox');

const statTotalFiles = document.getElementById('statTotalFiles');
const statTotalSize = document.getElementById('statTotalSize');
const statCategories = document.getElementById('statCategories');
const statSelectedCount = document.getElementById('statSelectedCount');
const btnOrganizeCount = document.getElementById('btnOrganizeCount');

const categoryStrip = document.getElementById('categoryStrip');
const fileTableBody = document.getElementById('fileTableBody');

// Rules Modal
const rulesModal = document.getElementById('rulesModal');
const openRulesBtn = document.getElementById('openRulesBtn');
const closeRulesBtn = document.getElementById('closeRulesBtn');
const saveRulesBtn = document.getElementById('saveRulesBtn');
const rulesListContainer = document.getElementById('rulesListContainer');
const newRuleCategory = document.getElementById('newRuleCategory');
const newRuleKeyword = document.getElementById('newRuleKeyword');
const addRuleBtn = document.getElementById('addRuleBtn');

// Toast Notification
function showToast(message, type = 'info') {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.className = `toast show ${type}`;
  setTimeout(() => {
    toast.className = 'toast';
  }, 4000);
}

// Fetch Initial Status
async function initApp() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    defaultDirs = data.default_dirs || {};

    if (defaultDirs.downloads) {
      folderInput.value = defaultDirs.downloads;
    }

    updateDaemonUI(data.daemon_active, data.daemon_folder);
    updateUndoUI(data.last_undo);

    // Initial Scan on load
    if (folderInput.value) {
      triggerScan();
    }
  } catch (err) {
    console.error('Error connecting to backend:', err);
    showToast('Gagal terhubung ke engine lokal.', 'error');
  }
}

function updateDaemonUI(isActive, folder) {
  if (isActive) {
    daemonDot.className = 'status-dot active';
    daemonText.textContent = `Daemon Aktif (${folder ? folder.split(/[\\/]/).pop() : 'Monitoring'})`;
    daemonToggleBtn.style.borderColor = 'rgba(16, 185, 129, 0.4)';
  } else {
    daemonDot.className = 'status-dot';
    daemonText.textContent = 'Daemon Standby';
    daemonToggleBtn.style.borderColor = '';
  }
}

function updateUndoUI(lastUndo) {
  if (lastUndo && lastUndo.moved_count > 0) {
    undoBtn.disabled = false;
    undoLabel.textContent = `Undo (${lastUndo.moved_count} file)`;
    undoBtn.title = `Kembalikan ${lastUndo.moved_count} file yang dirapikan pada ${lastUndo.timestamp}`;
  } else {
    undoBtn.disabled = true;
    undoLabel.textContent = 'Undo Terakhir';
    undoBtn.title = 'Tidak ada pemindahan yang bisa dibatalkan';
  }
}

// Preset Buttons
document.querySelectorAll('.preset-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    document.querySelectorAll('.preset-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    const preset = chip.dataset.preset;
    if (preset === 'downloads' && defaultDirs.downloads) {
      folderInput.value = defaultDirs.downloads;
    } else if (preset === 'desktop' && defaultDirs.desktop) {
      folderInput.value = defaultDirs.desktop;
    } else if (preset === 'current' && defaultDirs.current) {
      folderInput.value = defaultDirs.current;
    }
    triggerScan();
  });
});

// Browse Folder
browseBtn.addEventListener('click', async () => {
  browseBtn.disabled = true;
  browseBtn.textContent = 'Membuka folder...';
  try {
    const res = await fetch('/api/browse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ initial_dir: folderInput.value })
    });
    const data = await res.json();
    if (data.folder) {
      folderInput.value = data.folder;
      document.querySelectorAll('.preset-chip').forEach(c => c.classList.remove('active'));
      triggerScan();
    }
  } catch (err) {
    console.error('Error picking folder:', err);
  } finally {
    browseBtn.disabled = false;
    browseBtn.innerHTML = `
      <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
      Cari Folder...
    `;
  }
});

// Scan & Preview
async function triggerScan() {
  const folder = folderInput.value.trim();
  if (!folder) {
    showToast('Pilih folder terlebih dahulu.', 'error');
    return;
  }

  const targetMode = document.querySelector('input[name="targetMode"]:checked').value;

  scanBtn.disabled = true;
  scanBtn.innerHTML = 'Memindai...';

  try {
    const res = await fetch('/api/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folder, target_mode: targetMode })
    });
    const data = await res.json();

    if (data.error) {
      showToast(data.error, 'error');
      return;
    }

    currentScanData = data;
    renderScanResults(data);
  } catch (err) {
    console.error('Scan error:', err);
    showToast('Gagal memindai folder.', 'error');
  } finally {
    scanBtn.disabled = false;
    scanBtn.innerHTML = `
      <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
      Pindai & Pratinjau
    `;
  }
}

scanBtn.addEventListener('click', triggerScan);

// Render Results
function renderScanResults(data) {
  statTotalFiles.textContent = data.total_files;
  statTotalSize.textContent = data.total_size_formatted;
  statCategories.textContent = Object.keys(data.category_counts).length;

  renderCategoryPills(data);
  renderTable();
  updateSelectedCount();
}

function renderCategoryPills(data) {
  categoryStrip.innerHTML = '';

  // "Semua" pill
  const allPill = document.createElement('button');
  allPill.className = `cat-pill ${selectedCategoryId === 'ALL' ? 'active' : ''}`;
  allPill.innerHTML = `
    <span>Semua File</span>
    <span class="cat-pill-count">${data.total_files}</span>
  `;
  allPill.addEventListener('click', () => {
    selectedCategoryId = 'ALL';
    updateCategoryPillsActive();
    renderTable();
  });
  categoryStrip.appendChild(allPill);

  // Individual category pills
  for (const [catName, count] of Object.entries(data.category_counts)) {
    const pill = document.createElement('button');
    pill.className = `cat-pill ${selectedCategoryId === catName ? 'active' : ''}`;
    pill.dataset.category = catName;

    let dotColor = '#94a3b8';
    if (data.items.length > 0) {
      const match = data.items.find(i => i.category === catName);
      if (match) dotColor = match.color;
    }

    pill.innerHTML = `
      <span class="cat-badge-dot" style="background-color: ${dotColor}"></span>
      <span>${catName}</span>
      <span class="cat-pill-count">${count}</span>
    `;
    pill.addEventListener('click', () => {
      selectedCategoryId = catName;
      updateCategoryPillsActive();
      renderTable();
    });
    categoryStrip.appendChild(pill);
  }
}

function updateCategoryPillsActive() {
  document.querySelectorAll('.cat-pill').forEach(p => {
    if (selectedCategoryId === 'ALL' && !p.dataset.category) {
      p.classList.add('active');
    } else if (p.dataset.category === selectedCategoryId) {
      p.classList.add('active');
    } else {
      p.classList.remove('active');
    }
  });
}

function renderTable() {
  if (!currentScanData || currentScanData.items.length === 0) {
    fileTableBody.innerHTML = `
      <tr>
        <td colspan="6" class="empty-state">
          <div class="empty-illustration">✨</div>
          <p class="empty-title">Folder sudah rapi!</p>
          <p class="empty-desc">Tidak ada file yang perlu dirapikan di folder ini.</p>
        </td>
      </tr>
    `;
    organizeBtn.disabled = true;
    return;
  }

  const query = searchInput.value.toLowerCase().trim();
  const filtered = currentScanData.items.filter(item => {
    const matchesCat = selectedCategoryId === 'ALL' || item.category === selectedCategoryId;
    const matchesQuery = !query || item.name.toLowerCase().includes(query) || item.extension.toLowerCase().includes(query);
    return matchesCat && matchesQuery;
  });

  if (filtered.length === 0) {
    fileTableBody.innerHTML = `
      <tr>
        <td colspan="6" class="empty-state">
          <p class="empty-title">Tidak ada file yang cocok dengan filter</p>
        </td>
      </tr>
    `;
    return;
  }

  fileTableBody.innerHTML = '';
  filtered.forEach(item => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>
        <label class="checkbox-container">
          <input type="checkbox" class="file-checkbox" data-id="${item.id}" ${item.selected ? 'checked' : ''}>
          <span class="checkmark"></span>
        </label>
      </td>
      <td>
        <div class="file-name-cell">
          <span class="ext-badge">${item.is_dir ? 'DIR' : (item.extension.replace('.', '') || 'FILE')}</span>
          <span title="${item.name}">${escapeHtml(item.name)}</span>
        </div>
      </td>
      <td>
        <span class="category-tag" style="background: ${item.color}20; color: ${item.color}; border-color: ${item.color}40;">
          ${item.category}
        </span>
      </td>
      <td>
        <span class="dest-path" title="${item.target_path}">${escapeHtml(item.target_dir.split(/[\\/]/).pop())}/${escapeHtml(item.name)}</span>
      </td>
      <td style="color: var(--text-muted);">${item.size_formatted}</td>
      <td style="color: var(--text-sub);">${item.modified_time}</td>
    `;
    fileTableBody.appendChild(tr);
  });

  // Attach checkbox listeners
  document.querySelectorAll('.file-checkbox').forEach(cb => {
    cb.addEventListener('change', e => {
      const id = e.target.dataset.id;
      const targetItem = currentScanData.items.find(i => i.id === id);
      if (targetItem) {
        targetItem.selected = e.target.checked;
      }
      updateSelectedCount();
    });
  });
}

function updateSelectedCount() {
  if (!currentScanData) return;
  const count = currentScanData.items.filter(i => i.selected).length;
  statSelectedCount.textContent = count;
  btnOrganizeCount.textContent = count;
  organizeBtn.disabled = count === 0;

  const allSelected = currentScanData.items.length > 0 && count === currentScanData.items.length;
  selectAllCheckbox.checked = allSelected;
}

selectAllCheckbox.addEventListener('change', e => {
  const isChecked = e.target.checked;
  if (!currentScanData) return;
  currentScanData.items.forEach(item => {
    item.selected = isChecked;
  });
  renderTable();
  updateSelectedCount();
});

searchInput.addEventListener('input', () => {
  renderTable();
});

// Organize Action
organizeBtn.addEventListener('click', async () => {
  if (!currentScanData) return;
  const itemsToMove = currentScanData.items.filter(i => i.selected);
  if (itemsToMove.length === 0) return;

  organizeBtn.disabled = true;
  organizeBtn.innerHTML = 'Memindahkan File...';

  try {
    const res = await fetch('/api/organize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items: itemsToMove })
    });
    const data = await res.json();

    if (data.success) {
      showToast(`✨ Berhasil merapikan ${data.moved_count} file!`, 'success');
      updateUndoUI({ moved_count: data.moved_count, timestamp: 'Baru saja' });
      triggerScan();
    } else {
      showToast(`Sebagian file gagal dipindahkan (${data.errors.length} error).`, 'error');
    }
  } catch (err) {
    console.error('Error organizing files:', err);
    showToast('Terjadi kesalahan saat memindahkan file.', 'error');
  } finally {
    organizeBtn.disabled = false;
    organizeBtn.innerHTML = `
      <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 13l4 4L19 7"/></svg>
      Rapikan Sekarang (<span id="btnOrganizeCount">0</span>)
    `;
  }
});

// One-Click Undo Action
undoBtn.addEventListener('click', async () => {
  undoBtn.disabled = true;
  undoBtn.textContent = 'Mengembalikan...';

  try {
    const res = await fetch('/api/undo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });
    const data = await res.json();

    if (data.success) {
      showToast(`↩️ Berhasil mengembalikan ${data.reverted_count} file ke posisi semula!`, 'success');
      updateUndoUI(null);
      triggerScan();
    } else {
      showToast(data.message || 'Gagal melakukan undo.', 'error');
    }
  } catch (err) {
    console.error('Error undoing batch:', err);
    showToast('Gagal membatalkan pemindahan file.', 'error');
  } finally {
    undoBtn.disabled = false;
    undoLabel.textContent = 'Undo Terakhir';
  }
});

// Daemon Toggle
daemonToggleBtn.addEventListener('click', async () => {
  const folder = folderInput.value.trim();
  try {
    const res = await fetch('/api/daemon/toggle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folder })
    });
    const data = await res.json();
    if (data.error) {
      showToast(data.error, 'error');
      return;
    }
    updateDaemonUI(data.daemon_active, data.daemon_folder);
    if (data.daemon_active) {
      showToast('🛡️ Background Daemon aktif. File baru akan dirapikan otomatis!', 'success');
    } else {
      showToast('Daemon dinonaktifkan.', 'info');
    }
  } catch (err) {
    console.error('Daemon toggle error:', err);
  }
});

// Rules Modal
openRulesBtn.addEventListener('click', async () => {
  try {
    const res = await fetch('/api/rules');
    loadedRules = await res.json();
    renderRulesEditor(loadedRules);
    rulesModal.classList.add('open');
  } catch (err) {
    showToast('Gagal memuat aturan.', 'error');
  }
});

closeRulesBtn.addEventListener('click', () => {
  rulesModal.classList.remove('open');
});

function renderRulesEditor(rules) {
  rulesListContainer.innerHTML = '';
  for (const [catName, catInfo] of Object.entries(rules.categories || {})) {
    const card = document.createElement('div');
    card.className = 'rule-item-card';

    const kws = (catInfo.keywords || []).map(k => `
      <span class="rule-chip">${escapeHtml(k)} <span style="cursor:pointer;margin-left:4px;" onclick="removeKeyword('${catName}', '${k}')">&times;</span></span>
    `).join('');

    const exts = (catInfo.extensions || []).slice(0, 8).map(e => `
      <span class="rule-chip" style="color: ${catInfo.color}">${escapeHtml(e)}</span>
    `).join('');

    card.innerHTML = `
      <div class="rule-item-header">
        <span class="rule-category-title" style="color: ${catInfo.color}">
          ● ${catName}
        </span>
        <span style="font-size: 11px; color: var(--text-muted);">Folder: /${catInfo.folder_name}</span>
      </div>
      <div style="font-size: 11px; color: var(--text-sub); margin-bottom: 6px;">Ekstensi didukung:</div>
      <div class="rule-tags-container" style="margin-bottom: 8px;">${exts || '<span style="color:var(--text-sub);font-size:11px;">(Semua format yang cocok dengan keyword)</span>'}</div>
      <div style="font-size: 11px; color: var(--text-sub); margin-bottom: 6px;">Kata kunci (keywords):</div>
      <div class="rule-tags-container">${kws || '<span style="color:var(--text-sub);font-size:11px;">-</span>'}</div>
    `;
    rulesListContainer.appendChild(card);
  }
}

window.removeKeyword = (catName, keyword) => {
  if (!loadedRules || !loadedRules.categories[catName]) return;
  loadedRules.categories[catName].keywords = loadedRules.categories[catName].keywords.filter(k => k !== keyword);
  renderRulesEditor(loadedRules);
};

addRuleBtn.addEventListener('click', () => {
  const cat = newRuleCategory.value;
  const kw = newRuleKeyword.value.trim().toLowerCase();
  if (!kw) return;
  if (!loadedRules.categories[cat].keywords) {
    loadedRules.categories[cat].keywords = [];
  }
  if (!loadedRules.categories[cat].keywords.includes(kw)) {
    loadedRules.categories[cat].keywords.push(kw);
    newRuleKeyword.value = '';
    renderRulesEditor(loadedRules);
  }
});

saveRulesBtn.addEventListener('click', async () => {
  try {
    const res = await fetch('/api/rules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(loadedRules)
    });
    const data = await res.json();
    if (data.success) {
      showToast('Aturan berhasil disimpan!', 'success');
      rulesModal.classList.remove('open');
      triggerScan();
    }
  } catch (err) {
    showToast('Gagal menyimpan aturan.', 'error');
  }
});

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

// Start
initApp();
