/**
 * SomaStack UI - Data Table Component
 * Version: 1.0.0
 */

document.addEventListener('alpine:init', () => {
  Alpine.data('dataTable', (config = {}) => ({
    columns: config.columns || [],
    data: config.data || [],
    pageSize: config.pageSize || 10,
    currentPage: 1,
    sortColumn: null,
    sortDirection: 'asc',
    searchQuery: '',
    selectedRows: new Set(),
    isLoading: config.isLoading || false,
    
    init() {
      // Initialize
    },
    
    get filteredData() {
      if (!this.searchQuery.trim()) {
        return this.data;
      }
      
      const query = this.searchQuery.toLowerCase();
      
      return this.data.filter(row => {
        return this.columns.some(col => {
          const value = row[col.key];
          if (value === null || value === undefined) return false;
          return String(value).toLowerCase().includes(query);
        });
      });
    },
    
    get sortedData() {
      if (!this.sortColumn) {
        return this.filteredData;
      }
      
      const col = this.columns.find(c => c.key === this.sortColumn);
      const sortType = col?.sortType || 'string';
      
      return [...this.filteredData].sort((a, b) => {
        let aVal = a[this.sortColumn];
        let bVal = b[this.sortColumn];
        
        // Handle null/undefined
        if (aVal === null || aVal === undefined) aVal = '';
        if (bVal === null || bVal === undefined) bVal = '';
        
        let comparison = 0;
        
        if (sortType === 'number') {
          comparison = Number(aVal) - Number(bVal);
        } else if (sortType === 'date') {
          comparison = new Date(aVal) - new Date(bVal);
        } else {
          comparison = String(aVal).localeCompare(String(bVal));
        }
        
        return this.sortDirection === 'asc' ? comparison : -comparison;
      });
    },
    
    get paginatedData() {
      const start = (this.currentPage - 1) * this.pageSize;
      const end = start + this.pageSize;
      return this.sortedData.slice(start, end);
    },
    
    get totalItems() {
      return this.filteredData.length;
    },
    
    get totalPages() {
      return Math.ceil(this.totalItems / this.pageSize);
    },
    
    get startIndex() {
      if (this.totalItems === 0) return 0;
      return (this.currentPage - 1) * this.pageSize + 1;
    },
    
    get endIndex() {
      return Math.min(this.currentPage * this.pageSize, this.totalItems);
    },
    
    get showPagination() {
      return this.totalItems > this.pageSize;
    },
    
    get isEmpty() {
      return this.data.length === 0;
    },
    
    get isFiltered() {
      return this.searchQuery.trim() !== '';
    },
    
    get noResults() {
      return this.isFiltered && this.filteredData.length === 0;
    },
    
    sortBy(columnKey) {
      if (this.sortColumn === columnKey) {
        this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
      } else {
        this.sortColumn = columnKey;
        this.sortDirection = 'asc';
      }
      this.currentPage = 1;
    },
    
    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++;
      }
    },
    
    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--;
      }
    },
    
    goToPage(page) {
      if (page >= 1 && page <= this.totalPages) {
        this.currentPage = page;
      }
    },
    
    setPageSize(size) {
      this.pageSize = size;
      this.currentPage = 1;
    },
    
    isSelected(rowId) {
      return this.selectedRows.has(rowId);
    },
    
    toggleSelect(rowId) {
      if (this.selectedRows.has(rowId)) {
        this.selectedRows.delete(rowId);
      } else {
        this.selectedRows.add(rowId);
      }
      this.selectedRows = new Set(this.selectedRows);
    },
    
    toggleSelectAll() {
      if (this.allSelected) {
        this.selectedRows.clear();
      } else {
        this.paginatedData.forEach(row => {
          if (row.id) this.selectedRows.add(row.id);
        });
      }
      this.selectedRows = new Set(this.selectedRows);
    },
    
    get allSelected() {
      if (this.paginatedData.length === 0) return false;
      return this.paginatedData.every(row => row.id && this.selectedRows.has(row.id));
    },
    
    get someSelected() {
      return this.selectedRows.size > 0 && !this.allSelected;
    },
    
    get selectedCount() {
      return this.selectedRows.size;
    },
    
    clearSelection() {
      this.selectedRows.clear();
      this.selectedRows = new Set();
    },
    
    getSelectedRows() {
      return this.data.filter(row => row.id && this.selectedRows.has(row.id));
    },
    
    setData(newData) {
      this.data = newData;
      this.currentPage = 1;
      this.clearSelection();
    },
    
    refresh() {
      // Trigger reactivity
      this.data = [...this.data];
    }
  }));
});
