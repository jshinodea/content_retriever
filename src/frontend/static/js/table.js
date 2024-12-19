/**
 * Table Handler Module
 * 
 * Manages the content table display and interactions.
 */

class TableHandler {
    constructor() {
        this.container = document.getElementById('content-table');
        this.table = this.container.querySelector('table');
        this.thead = this.table.querySelector('thead');
        this.tbody = this.table.querySelector('tbody');
        
        this.content = {
            columns: [],
            rows: []
        };
        
        this.selectedCells = new Set();
        this.isEditing = false;
        
        this._bindEvents();
    }
    
    /**
     * Bind table event handlers
     */
    _bindEvents() {
        // Cell selection
        this.tbody.addEventListener('click', (event) => {
            const cell = event.target.closest('td');
            if (!cell || this.isEditing) return;
            
            if (event.shiftKey) {
                this._handleShiftClick(cell);
            } else {
                this._handleClick(cell);
            }
        });
        
        // Double click to edit
        this.tbody.addEventListener('dblclick', (event) => {
            const cell = event.target.closest('td');
            if (!cell || this.isEditing) return;
            
            this._startEditing(cell);
        });
        
        // Handle document clicks to end editing
        document.addEventListener('click', (event) => {
            if (this.isEditing && !event.target.closest('.table-cell-editing')) {
                this._endEditing();
            }
        });
    }
    
    /**
     * Update table content
     */
    updateContent(content) {
        this.content = content;
        this._renderTable();
        this.container.classList.remove('hidden');
    }
    
    /**
     * Render the table
     */
    _renderTable() {
        // Render headers
        this.thead.innerHTML = `
            <tr>
                ${this.content.columns.map(column => `
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        ${this._escapeHtml(column)}
                    </th>
                `).join('')}
            </tr>
        `;
        
        // Render rows
        this.tbody.innerHTML = this.content.rows.map((row, rowIndex) => `
            <tr>
                ${this.content.columns.map(column => `
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 table-cell-editable"
                        data-row="${rowIndex}"
                        data-column="${column}">
                        ${this._escapeHtml(row[column] || '')}
                    </td>
                `).join('')}
            </tr>
        `).join('');
    }
    
    /**
     * Handle regular cell click
     */
    _handleClick(cell) {
        const wasSelected = cell.classList.contains('table-cell-selected');
        
        // Clear all selections if not holding Ctrl/Cmd
        if (!event.ctrlKey && !event.metaKey) {
            this._clearSelection();
        }
        
        if (wasSelected) {
            this._deselectCell(cell);
        } else {
            this._selectCell(cell);
        }
    }
    
    /**
     * Handle shift-click for range selection
     */
    _handleShiftClick(cell) {
        const lastSelected = this.tbody.querySelector('.table-cell-selected');
        if (!lastSelected) {
            this._selectCell(cell);
            return;
        }
        
        const range = this._getCellRange(lastSelected, cell);
        this._selectRange(range);
    }
    
    /**
     * Start editing a cell
     */
    _startEditing(cell) {
        this.isEditing = true;
        cell.classList.add('table-cell-editing');
        
        const value = cell.textContent;
        const input = document.createElement('textarea');
        input.value = value;
        input.rows = 1;
        
        // Auto-resize textarea
        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = input.scrollHeight + 'px';
        });
        
        // Handle keyboard events
        input.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                this._endEditing(true);
            } else if (event.key === 'Escape') {
                this._endEditing(false);
            }
        });
        
        cell.textContent = '';
        cell.appendChild(input);
        input.focus();
    }
    
    /**
     * End cell editing
     */
    _endEditing(save = true) {
        if (!this.isEditing) return;
        
        const cell = this.tbody.querySelector('.table-cell-editing');
        if (!cell) return;
        
        const input = cell.querySelector('textarea');
        if (!input) return;
        
        if (save) {
            const newValue = input.value;
            const row = parseInt(cell.dataset.row);
            const column = cell.dataset.column;
            
            // Update content
            this.content.rows[row][column] = newValue;
            cell.textContent = newValue;
            
            // Notify of change
            this._notifyContentChange(row, column, newValue);
        } else {
            cell.textContent = this.content.rows[row][column];
        }
        
        cell.classList.remove('table-cell-editing');
        this.isEditing = false;
    }
    
    /**
     * Select a cell
     */
    _selectCell(cell) {
        cell.classList.add('table-cell-selected');
        this.selectedCells.add(this._getCellIdentifier(cell));
        this._updateSelectionState();
    }
    
    /**
     * Deselect a cell
     */
    _deselectCell(cell) {
        cell.classList.remove('table-cell-selected');
        this.selectedCells.delete(this._getCellIdentifier(cell));
        this._updateSelectionState();
    }
    
    /**
     * Clear all cell selections
     */
    _clearSelection() {
        this.tbody.querySelectorAll('.table-cell-selected').forEach(cell => {
            cell.classList.remove('table-cell-selected');
        });
        this.selectedCells.clear();
        this._updateSelectionState();
    }
    
    /**
     * Get cell range between two cells
     */
    _getCellRange(cell1, cell2) {
        const row1 = parseInt(cell1.dataset.row);
        const row2 = parseInt(cell2.dataset.row);
        const col1 = this.content.columns.indexOf(cell1.dataset.column);
        const col2 = this.content.columns.indexOf(cell2.dataset.column);
        
        return {
            startRow: Math.min(row1, row2),
            endRow: Math.max(row1, row2),
            startCol: Math.min(col1, col2),
            endCol: Math.max(col1, col2)
        };
    }
    
    /**
     * Select a range of cells
     */
    _selectRange(range) {
        this._clearSelection();
        
        for (let row = range.startRow; row <= range.endRow; row++) {
            for (let col = range.startCol; col <= range.endCol; col++) {
                const cell = this.tbody.querySelector(
                    `td[data-row="${row}"][data-column="${this.content.columns[col]}"]`
                );
                if (cell) {
                    this._selectCell(cell);
                }
            }
        }
    }
    
    /**
     * Get unique identifier for a cell
     */
    _getCellIdentifier(cell) {
        return `${cell.dataset.row}:${cell.dataset.column}`;
    }
    
    /**
     * Update UI based on selection state
     */
    _updateSelectionState() {
        if (window.uiHandler) {
            window.uiHandler.state.selectedCells = this.selectedCells;
        }
    }
    
    /**
     * Notify of content changes
     */
    _notifyContentChange(row, column, value) {
        wsHandler.sendMessage('content_change', {
            row,
            column,
            value
        });
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    _escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// Create global table handler instance
window.tableHandler = new TableHandler(); 