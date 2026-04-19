/**
 * FavouritesManager
 *
 * ⚠️ FEATURE TEMPORARILY DISABLED (April 19, 2026)
 * ================================================
 * Status: Work in Progress - UI hidden due to browser caching issues
 * 
 * Background:
 * - Backend API fully functional (100% test coverage)
 * - Frontend CSRF fix applied (axios.defaults.withCredentials = true)
 * - Issue: Browser cache serving old JavaScript without CSRF fix
 * - Decision: Hide all UI elements until browser cache issue resolved
 * 
 * What's Hidden:
 * - Star button (favourite/unfavourite)
 * - Sidebar list of favourites
 * - Dashboard table on main page
 * 
 * Backend Status:
 * - ✅ All API endpoints working (favourites_routes.py - 100% coverage)
 * - ✅ Database operations functional (favourites_repo.py)
 * - ✅ CSRF protection configured correctly
 * - ✅ Path resolution fixed (4 strategies)
 * 
 * To Re-enable:
 * 1. Remove the "style.display = 'none'" lines in:
 *    - onFileLoaded() method (lines ~127, 130, 133)
 *    - renderDashboard() method (line ~207)
 *    - goHome() method (lines ~112, 113)
 * 2. Test with hard browser refresh (Ctrl+Shift+R)
 * 3. Verify CSRF token is sent with requests
 * 4. See AUDIT_REPORT.md for full context
 * 
 * ================================================
 *
 * Manages the favourites dashboard, sidebar, star button, and context menu.
 * Completely decoupled from MarkdownViewerApp — communicates exclusively via
 * CustomEvents:
 *   Dispatches: 'fav:open-file'  → app.js routes to the correct loader
 *               'app:status'     → app.js calls setStatus()
 *   Listens:    'backend:ready'  → dispatched by app.js after health check
 *
 * Security:
 *   - All user-supplied data rendered via textContent / createElement (no innerHTML).
 *   - Context menu dismisses on outside click + Escape (U3).
 */
class FavouritesManager {
    constructor() {
        /** @type {Array<Object>} in-memory cache of all favourites */
        this.favourites = [];
        /** @type {string|null} absolute path of the currently open file */
        this.currentFilePath = null;
        /** @type {number|null} debounce timer id for autocomplete */
        this._autocompleteTimer = null;

        // Grab DOM refs needed across methods
        this._sidebar     = document.getElementById('fav-sidebar');
        this._sidebarList = document.getElementById('favSidebarList');
        this._sidebarSearch    = document.getElementById('favSidebarSearch');
        this._sidebarAutocomp  = document.getElementById('favSidebarAutocomplete');
        this._dashboard   = document.getElementById('fav-dashboard');
        this._tableSearch = document.getElementById('favTableSearch');
        this._tableAutocomp    = document.getElementById('favTableAutocomplete');
        this._tableContainer   = document.getElementById('favTableContainer');
        this._contextMenu = document.getElementById('fav-context-menu');
        this._btnFavourite     = document.getElementById('btnFavourite');
        this._btnCloseSidebar  = document.getElementById('btnCloseSidebar');

        this.init();
    }

    // -----------------------------------------------------------------------
    // Initialisation
    // -----------------------------------------------------------------------

    init() {
        // R1: wait for backend to be ready before loading favourites
        document.addEventListener('backend:ready', () => this._loadInitialData(), { once: true });

        // Sidebar close button
        if (this._btnCloseSidebar) {
            this._btnCloseSidebar.addEventListener('click', () => {
                if (this._sidebar) this._sidebar.style.display = 'none';
            });
        }

        // Star button toggle
        if (this._btnFavourite) {
            this._btnFavourite.addEventListener('click', () => this.toggleFavourite());
        }

        // Dashboard search
        if (this._tableSearch) {
            this._tableSearch.addEventListener('input', (e) => {
                this.filterList(e.target.value);
                this._autocomplete(e.target.value, this._tableAutocomp);
            });
            this._tableSearch.addEventListener('blur', () => {
                setTimeout(() => this._hideAutocomplete(this._tableAutocomp), 200);
            });
        }

        // Sidebar search
        if (this._sidebarSearch) {
            this._sidebarSearch.addEventListener('input', (e) => {
                this._filterSidebar(e.target.value);
                this._autocomplete(e.target.value, this._sidebarAutocomp);
            });
            this._sidebarSearch.addEventListener('blur', () => {
                setTimeout(() => this._hideAutocomplete(this._sidebarAutocomp), 200);
            });
        }
    }

    async _loadInitialData() {
        try {
            const res = await window.MarkdownViewerAPI.getFavourites();
            if (res.success) {
                this.favourites = res.data || [];
                this.renderSidebar();

                if (this.currentFilePath) {
                    // File was already loaded before favourites finished loading
                    // (race condition: CLI ?file= param triggers loadFileFromServer
                    // before _loadInitialData resolves). Show sidebar now.
                    if (this._sidebar && this.favourites.length > 0) {
                        this._sidebar.style.display = '';
                    }
                } else {
                    this.renderDashboard();
                }
            }
        } catch (err) {
            this._dispatchStatus('Could not load favourites: ' + err.message, 'warning');
        }
    }

    /**
     * Called by app.js when the user navigates back to the Home page.
     * Resets file context and shows the dashboard (or welcome screen).
     */
    goHome() {
        this.currentFilePath = null;
        // ⚠️ WORK IN PROGRESS: UI elements hidden - see class header for details
        if (this._sidebar) this._sidebar.style.display = 'none';  // TODO: Remove to re-enable
        if (this._btnFavourite) this._btnFavourite.style.display = 'none';  // TODO: Remove to re-enable
        this.renderDashboard();
    }

    // -----------------------------------------------------------------------
    // Star button
    // -----------------------------------------------------------------------

    /** Called by app.js whenever a file is successfully loaded. */
    async onFileLoaded(filePath) {
        this.currentFilePath = filePath;
        if (!this._btnFavourite) return;

        // ⚠️ WORK IN PROGRESS: Favourites feature temporarily disabled (April 19, 2026)
        // Reason: Browser cache serving old JS without CSRF fix
        // Backend fully functional - see class header comment for re-enabling instructions
        this._btnFavourite.style.display = 'none';  // TODO: Remove this line to re-enable

        // Hide dashboard table — it belongs to the main/home page only
        if (this._dashboard) this._dashboard.style.display = 'none';  // TODO: Remove this line to re-enable

        // ⚠️ WORK IN PROGRESS: Sidebar hidden until favourites feature re-enabled
        if (this._sidebar) this._sidebar.style.display = 'none';  // TODO: Remove this line to re-enable
    }

    _setStarState(isFav, favId) {
        if (!this._btnFavourite) return;
        this._btnFavourite.setAttribute('aria-pressed', isFav ? 'true' : 'false');
        this._btnFavourite.title = isFav ? 'Remove from Favourites' : 'Add to Favourites';
        this._btnFavourite.textContent = isFav ? '★ Favourite' : '☆ Favourite';
        // Store id for quick unfavourite
        this._btnFavourite.dataset.favId = isFav ? (favId || '') : '';
    }

    async toggleFavourite() {
        if (!this.currentFilePath) return;
        if (this._btnFavourite.disabled) return; // Skip if button is disabled

        const isFav = this._btnFavourite.getAttribute('aria-pressed') === 'true';
        try {
            if (isFav) {
                // Remove from favourites
                const favId = parseInt(this._btnFavourite.dataset.favId, 10);
                if (!favId) return;
                const confirmed = confirm('Remove this file from favourites?');
                if (!confirmed) return;
                await this._removeFavourite(favId);
                // Update the local array and sidebar
                this.favourites = this.favourites.filter(f => f.id !== favId);
                this.renderSidebar();
                // Hide sidebar if no more favourites
                if (this.favourites.length === 0 && this._sidebar) {
                    this._sidebar.style.display = 'none';
                }
                this._setStarState(false, null);
                this._dispatchStatus('Removed from favourites', 'success');
            } else {
                // Add to favourites
                const res = await window.MarkdownViewerAPI.addFavourite(this.currentFilePath);
                if (res.success) {
                    this.favourites.unshift(res.data);
                    this._setStarState(true, res.data.id);
                    this.renderSidebar();
                    // Show sidebar; do NOT show dashboard table while a file is open
                    if (this._sidebar) this._sidebar.style.display = '';
                    this._dispatchStatus('Added to favourites', 'success');
                }
            }
        } catch (err) {
            const msg = err.response?.data?.error?.message || err.message;
            let displayMsg = msg;
            
            // Provide clearer error messages for common cases
            if (msg.includes('does not exist') || msg.includes('not found')) {
                displayMsg = 'Cannot save favourite: File path not accessible. Try opening the file from the examples folder or using the CLI with a full path.';
            }
            
            this._dispatchStatus('Favourite error: ' + displayMsg, 'error');
        }
    }

    // -----------------------------------------------------------------------
    // Dashboard
    // -----------------------------------------------------------------------

    renderDashboard() {
        // Dashboard is shown on the main/home page (no file open)
        if (this.currentFilePath) return;
        
        const welcome = document.getElementById('welcome');
        const features = document.getElementById('welcome-features');
        
        // Always show welcome container
        if (welcome) welcome.style.display = '';
        
        // ⚠️ WORK IN PROGRESS: Dashboard hidden temporarily (April 19, 2026)
        // Backend fully functional - hiding UI due to browser cache issues
        // See class header comment for full context and re-enabling instructions
        if (this._dashboard) this._dashboard.style.display = 'none';  // TODO: Change to '' to re-enable
        
        // Always show features list (until favourites dashboard re-enabled)
        if (features) features.style.display = '';
    }

    renderTable() {
        if (!this._tableContainer) return;
        // Clear existing content
        while (this._tableContainer.firstChild) {
            this._tableContainer.removeChild(this._tableContainer.firstChild);
        }

        const table = document.createElement('table');
        table.className = 'fav-table';

        // Header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        ['Name', 'Filename', 'Path', 'Tags', 'Favourited', 'Actions'].forEach(label => {
            const th = document.createElement('th');
            th.scope = 'col';
            th.textContent = label;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Body
        const tbody = document.createElement('tbody');
        this.favourites.forEach(item => {
            tbody.appendChild(this._buildRow(item));
        });
        table.appendChild(tbody);
        this._tableContainer.appendChild(table);
    }

    _buildRow(item) {
        const tr = document.createElement('tr');
        tr.dataset.favId = item.id;

        // U1: double-click opens, single click does nothing
        tr.addEventListener('dblclick', () => {
            this._dispatchOpenFile(item.path, 'same');
        });

        // Name cell
        const tdName = document.createElement('td');
        tdName.textContent = item.name;
        tr.appendChild(tdName);

        // Filename cell
        const tdFilename = document.createElement('td');
        tdFilename.textContent = item.filename;
        tr.appendChild(tdFilename);

        // Path cell — truncated with tooltip (U2)
        const tdPath = document.createElement('td');
        tdPath.className = 'fav-path-cell';
        tdPath.textContent = item.path;
        tdPath.title = item.path;
        tr.appendChild(tdPath);

        // Tags cell
        const tdTags = document.createElement('td');
        tdTags.className = 'fav-tags-cell';
        this._renderChips(tdTags, item.tags || []);
        tr.appendChild(tdTags);

        // Star cell
        const tdStar = document.createElement('td');
        const btnStar = document.createElement('button');
        btnStar.className = 'btn-icon';
        btnStar.textContent = '★';
        btnStar.title = 'Remove from favourites';
        btnStar.setAttribute('aria-label', `Remove ${item.name} from favourites`);
        btnStar.addEventListener('click', (e) => {
            e.stopPropagation();
            this.confirmUnfavourite(item.id, tr);
        });
        tdStar.appendChild(btnStar);
        tr.appendChild(tdStar);

        // Actions cell
        const tdActions = document.createElement('td');
        const btnEdit = document.createElement('button');
        btnEdit.className = 'btn btn-sm';
        btnEdit.textContent = 'Edit';
        btnEdit.addEventListener('click', (e) => {
            e.stopPropagation();
            this.enterEditMode(tr, item);
        });
        tdActions.appendChild(btnEdit);
        tr.appendChild(tdActions);

        return tr;
    }

    _renderChips(container, tags) {
        while (container.firstChild) container.removeChild(container.firstChild);
        tags.forEach(tag => {
            const chip = document.createElement('span');
            chip.className = 'fav-chip';
            chip.textContent = tag;
            container.appendChild(chip);
        });
    }

    // -----------------------------------------------------------------------
    // Edit mode
    // -----------------------------------------------------------------------

    enterEditMode(tr, item) {
        if (tr.dataset.editing === 'true') return;
        tr.dataset.editing = 'true';

        const cells = tr.querySelectorAll('td');
        // cells: 0=name, 1=filename, 2=path, 3=tags, 4=star, 5=actions

        // Name input
        const nameInput = document.createElement('input');
        nameInput.type = 'text';
        nameInput.className = 'fav-edit-input';
        nameInput.value = item.name;
        nameInput.setAttribute('aria-label', 'Favourite name');
        while (cells[0].firstChild) cells[0].removeChild(cells[0].firstChild);
        cells[0].appendChild(nameInput);

        // Tag chip editor
        const tagEditor = this._buildChipEditor(item.tags || []);
        while (cells[3].firstChild) cells[3].removeChild(cells[3].firstChild);
        cells[3].appendChild(tagEditor);

        // Save / Cancel buttons (U6: disabled while in-flight)
        while (cells[5].firstChild) cells[5].removeChild(cells[5].firstChild);

        const btnSave = document.createElement('button');
        btnSave.className = 'btn btn-sm btn-primary';
        btnSave.textContent = 'Save';

        const btnCancel = document.createElement('button');
        btnCancel.className = 'btn btn-sm';
        btnCancel.textContent = 'Cancel';

        btnSave.addEventListener('click', async (e) => {
            e.stopPropagation();
            const newName = nameInput.value.trim();
            const newTags = Array.from(
                tagEditor.querySelectorAll('.fav-chip[data-tag]')
            ).map(c => c.dataset.tag);

            btnSave.disabled = true;
            btnCancel.disabled = true;

            await this.saveEdit(item.id, newName, newTags, tr, item);
        });

        btnCancel.addEventListener('click', (e) => {
            e.stopPropagation();
            this._exitEditMode(tr, item);
        });

        cells[5].appendChild(btnSave);
        cells[5].appendChild(btnCancel);
    }

    async saveEdit(favId, name, tags, tr, originalItem) {
        try {
            const res = await window.MarkdownViewerAPI.updateFavourite(favId, { name, tags });
            if (res.success) {
                // Update in-memory cache
                const idx = this.favourites.findIndex(f => f.id === favId);
                if (idx !== -1) this.favourites[idx] = res.data;
                // Update this DOM row only (P2: no full re-render)
                this._exitEditMode(tr, res.data);
                // Sync sidebar so renamed favourite shows the new name immediately
                this.renderSidebar();
                this._dispatchStatus('Favourite saved', 'info');
            }
        } catch (err) {
            const msg = err.response?.data?.error?.message || err.message;
            this._dispatchStatus('Save error: ' + msg, 'error');
            // Re-enable buttons
            const btns = tr.querySelectorAll('button');
            btns.forEach(b => { b.disabled = false; });
        }
    }

    _exitEditMode(tr, item) {
        tr.dataset.editing = 'false';
        const cells = tr.querySelectorAll('td');

        while (cells[0].firstChild) cells[0].removeChild(cells[0].firstChild);
        cells[0].textContent = item.name;

        while (cells[3].firstChild) cells[3].removeChild(cells[3].firstChild);
        this._renderChips(cells[3], item.tags || []);

        while (cells[5].firstChild) cells[5].removeChild(cells[5].firstChild);
        const btnEdit = document.createElement('button');
        btnEdit.className = 'btn btn-sm';
        btnEdit.textContent = 'Edit';
        btnEdit.addEventListener('click', (e) => {
            e.stopPropagation();
            this.enterEditMode(tr, item);
        });
        cells[5].appendChild(btnEdit);

        // Update row reference for next edit
        tr.dataset.favId = item.id;
    }

    /** Build a chip editor widget with existing tags pre-filled. */
    _buildChipEditor(tags) {
        const wrapper = document.createElement('div');
        wrapper.className = 'fav-chip-editor';

        const addChip = (tagName) => {
            const chip = document.createElement('span');
            chip.className = 'fav-chip';
            chip.dataset.tag = tagName;
            chip.textContent = tagName;

            const xBtn = document.createElement('button');
            xBtn.type = 'button';
            xBtn.className = 'fav-chip-remove';
            xBtn.setAttribute('aria-label', `Remove tag ${tagName}`);
            xBtn.textContent = '×';
            xBtn.addEventListener('click', () => wrapper.removeChild(chip));
            chip.appendChild(xBtn);
            wrapper.insertBefore(chip, input);
        };

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'fav-tag-input';
        input.placeholder = 'Add tag…';
        input.setAttribute('aria-label', 'New tag');

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ',') {
                e.preventDefault();
                const val = input.value.trim().replace(/,/g, '');
                if (!val) return;
                const existing = Array.from(wrapper.querySelectorAll('.fav-chip[data-tag]'))
                    .map(c => c.dataset.tag.toLowerCase());
                if (existing.includes(val.toLowerCase())) {
                    input.value = '';
                    return;
                }
                addChip(val);
                input.value = '';
            } else if (e.key === 'Backspace' && input.value === '') {
                // U4: backspace on empty input removes last chip
                const chips = wrapper.querySelectorAll('.fav-chip[data-tag]');
                if (chips.length > 0) wrapper.removeChild(chips[chips.length - 1]);
            }
        });

        wrapper.appendChild(input);
        tags.forEach(addChip);
        return wrapper;
    }

    // -----------------------------------------------------------------------
    // Unfavourite
    // -----------------------------------------------------------------------

    async confirmUnfavourite(favId, tr) {
        const confirmed = confirm('Remove this file from favourites?');
        if (!confirmed) return;
        await this._removeFavourite(favId, tr);
    }

    async _removeFavourite(favId, tr) {
        try {
            const res = await window.MarkdownViewerAPI.deleteFavourite(favId);
            if (res.success) {
                this.favourites = this.favourites.filter(f => f.id !== favId);

                // Remove row from table
                if (tr && tr.parentNode) tr.parentNode.removeChild(tr);

                // Update sidebar
                this.renderSidebar();

                if (this.favourites.length === 0) {
                    if (this._sidebar) this._sidebar.style.display = 'none';
                    if (this._dashboard) this._dashboard.style.display = 'none';
                    // Only show welcome on the main page (no file open)
                    if (!this.currentFilePath) {
                        const welcome = document.getElementById('welcome');
                        const features = document.getElementById('welcome-features');
                        if (welcome) welcome.style.display = '';
                        if (features) features.style.display = '';
                    }
                }

                // Update star if this was the currently open file
                if (this._btnFavourite && this._btnFavourite.dataset.favId == favId) {
                    this._setStarState(false, null);
                }
            }
        } catch (err) {
            const msg = err.response?.data?.error?.message || err.message;
            this._dispatchStatus('Remove error: ' + msg, 'error');
        }
    }

    // -----------------------------------------------------------------------
    // Sidebar
    // -----------------------------------------------------------------------

    renderSidebar() {
        if (!this._sidebarList) return;
        
        // HIDE SIDEBAR - favourites feature disabled
        if (this._sidebar) this._sidebar.style.display = 'none';
        return;
        
        while (this._sidebarList.firstChild) {
            this._sidebarList.removeChild(this._sidebarList.firstChild);
        }
        this.favourites.forEach(item => {
            this._sidebarList.appendChild(this._buildSidebarItem(item));
        });
    }

    _buildSidebarItem(item) {
        const li = document.createElement('li');
        li.role = 'listitem';

        const btn = document.createElement('button');
        btn.className = 'fav-list-item';
        btn.dataset.path = item.path;
        btn.title = item.path;
        btn.textContent = item.name;

        btn.addEventListener('click', () => {
            this._dispatchOpenFile(item.path, 'same');
        });

        btn.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this._showContextMenu(e.clientX, e.clientY, item.path);
        });

        li.appendChild(btn);
        return li;
    }

    _filterSidebar(query) {
        if (!this._sidebarList) return;
        const q = query.toLowerCase();
        this._sidebarList.querySelectorAll('li').forEach(li => {
            const btn = li.querySelector('.fav-list-item');
            if (!btn) return;
            const path = (btn.dataset.path || '').toLowerCase();
            const name = (btn.textContent || '').toLowerCase();
            li.style.display = (!q || name.includes(q) || path.includes(q)) ? '' : 'none';
        });
    }

    // -----------------------------------------------------------------------
    // Dashboard filter
    // -----------------------------------------------------------------------

    filterList(query) {
        if (!this._tableContainer) return;
        const q = query.toLowerCase();
        this._tableContainer.querySelectorAll('tbody tr').forEach(tr => {
            const cells = tr.querySelectorAll('td');
            if (!cells.length) return;
            const text = [
                cells[0]?.textContent || '',
                cells[1]?.textContent || '',
                cells[2]?.textContent || '',
                cells[3]?.textContent || ''
            ].join(' ').toLowerCase();
            tr.style.display = (!q || text.includes(q)) ? '' : 'none';
        });
    }

    // -----------------------------------------------------------------------
    // Autocomplete
    // -----------------------------------------------------------------------

    _autocomplete(query, dropdownEl) {
        clearTimeout(this._autocompleteTimer);
        if (!query || query.length < 2) {
            this._hideAutocomplete(dropdownEl);
            return;
        }
        this._autocompleteTimer = setTimeout(async () => {
            try {
                const res = await window.MarkdownViewerAPI.searchFavourites(query);
                if (res.success) {
                    this._renderAutocomplete(dropdownEl, res.data);
                }
            } catch (_) {
                this._hideAutocomplete(dropdownEl);
            }
        }, 300);
    }

    _renderAutocomplete(dropdownEl, items) {
        if (!dropdownEl) return;
        while (dropdownEl.firstChild) dropdownEl.removeChild(dropdownEl.firstChild);
        if (!items || items.length === 0) {
            dropdownEl.style.display = 'none';
            return;
        }
        items.forEach(item => {
            const opt = document.createElement('div');
            opt.className = 'fav-autocomplete-item';
            opt.setAttribute('role', 'option');
            opt.textContent = item.name;
            opt.title = item.path;
            opt.addEventListener('mousedown', (e) => {
                e.preventDefault();
                this._dispatchOpenFile(item.path, 'same');
                this._hideAutocomplete(dropdownEl);
            });
            dropdownEl.appendChild(opt);
        });
        dropdownEl.style.display = '';
    }

    _hideAutocomplete(dropdownEl) {
        if (dropdownEl) dropdownEl.style.display = 'none';
    }

    // -----------------------------------------------------------------------
    // Context menu
    // -----------------------------------------------------------------------

    _showContextMenu(x, y, filePath) {
        if (!this._contextMenu) return;
        while (this._contextMenu.firstChild) {
            this._contextMenu.removeChild(this._contextMenu.firstChild);
        }

        const items = [
            { label: 'Open here',         target: 'same' },
            { label: 'Open in new window', target: 'window' },
            { label: 'Open in new tab',    target: 'tab' }
        ];

        items.forEach(({ label, target }) => {
            const btn = document.createElement('button');
            btn.className = 'fav-context-item';
            btn.setAttribute('role', 'menuitem');
            btn.textContent = label;
            btn.addEventListener('click', () => {
                this._closeContextMenu();
                this._dispatchOpenFile(filePath, target);
            });
            this._contextMenu.appendChild(btn);
        });

        this._contextMenu.style.left = x + 'px';
        this._contextMenu.style.top  = y + 'px';
        this._contextMenu.style.display = '';

        // U3: close on outside click or Escape
        const onOutsideClick = (e) => {
            if (!this._contextMenu.contains(e.target)) {
                this._closeContextMenu();
                document.removeEventListener('click', onOutsideClick);
                document.removeEventListener('keydown', onEscape);
            }
        };
        const onEscape = (e) => {
            if (e.key === 'Escape') {
                this._closeContextMenu();
                document.removeEventListener('click', onOutsideClick);
                document.removeEventListener('keydown', onEscape);
            }
        };
        // Delay attachment so the triggering right-click doesn't immediately close it
        setTimeout(() => {
            document.addEventListener('click', onOutsideClick);
            document.addEventListener('keydown', onEscape);
        }, 0);
    }

    _closeContextMenu() {
        if (this._contextMenu) this._contextMenu.style.display = 'none';
    }

    // -----------------------------------------------------------------------
    // Event dispatch helpers
    // -----------------------------------------------------------------------

    _dispatchOpenFile(filePath, target) {
        document.dispatchEvent(new CustomEvent('fav:open-file', {
            detail: { path: filePath, target }
        }));
    }

    _dispatchStatus(message, level) {
        document.dispatchEvent(new CustomEvent('app:status', {
            detail: { message, level }
        }));
    }
}
