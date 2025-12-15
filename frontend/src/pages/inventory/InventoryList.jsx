import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Search, 
  Plus, 
  Edit, 
  Trash2, 
  AlertCircle,
  Upload,
  Package
} from 'lucide-react';
import './inventory.css';

const API = window.API || 'http://127.0.0.1:8002/api';

const InventoryList = () => {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [filteredItems, setFilteredItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [showLowStockOnly, setShowLowStockOnly] = useState(false);
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    fetchItems();
  }, [showLowStockOnly]);

  useEffect(() => {
    filterItems();
  }, [items, searchTerm, categoryFilter]);

  const fetchItems = async () => {
    try {
      setLoading(true);
      const url = showLowStockOnly 
        ? `${API}/inventory/items?low_stock_only=true`
        : `${API}/inventory/items`;

      const response = await axios.get(url);
      setItems(response.data);

      // Extract unique categories
      const cats = [...new Set(response.data.map(item => item.category))];
      setCategories(cats);

      setLoading(false);
    } catch (error) {
      console.error('Error fetching items:', error);
      setLoading(false);
    }
  };

  const filterItems = () => {
    let filtered = items;

    if (searchTerm) {
      filtered = filtered.filter(item =>
        item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.category.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (categoryFilter !== 'all') {
      filtered = filtered.filter(item => item.category === categoryFilter);
    }

    setFilteredItems(filtered);
  };

  const deleteItem = async (id) => {
    if (window.confirm('Are you sure you want to delete this item?')) {
      try {
        await axios.delete(`${API}/inventory/items/${id}`);
        fetchItems();
      } catch (error) {
        console.error('Error deleting item:', error);
        alert('Failed to delete item');
      }
    }
  };

  const getStockStatus = (item) => {
    const percentage = (item.current_stock / item.reorder_level) * 100;
    if (percentage <= 50) return 'critical';
    if (percentage <= 100) return 'warning';
    return 'good';
  };

  return (
    <div className="inventory-list-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1>Inventory Items</h1>
          <p>{filteredItems.length} items</p>
        </div>
        <div className="header-actions">
          <button 
            className="btn-secondary"
            onClick={() => navigate('/inventory/import')}
          >
            <Upload size={18} />
            Import
          </button>
          <button 
            className="btn-primary"
            onClick={() => navigate('/inventory/add')}
          >
            <Plus size={18} />
            Add Item
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-section">
        <div className="search-box">
          <Search size={20} />
          <input
            type="text"
            placeholder="Search items..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <select 
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Categories</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={showLowStockOnly}
              onChange={(e) => setShowLowStockOnly(e.target.checked)}
            />
            Low Stock Only
          </label>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="loading-state">Loading...</div>
      ) : (
        <div className="table-container">
          <table className="inventory-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Category</th>
                <th>Current Stock</th>
                <th>Reorder Level</th>
                <th>Unit</th>
                <th>Unit Cost</th>
                <th>Total Value</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map(item => (
                <tr key={item.id}>
                  <td className="font-medium">{item.name}</td>
                  <td>
                    <span className="category-badge">{item.category}</span>
                  </td>
                  <td>
                    <span className="stock-display">
                      {item.current_stock_display || `${item.current_stock} ${item.unit}`}
                    </span>
                  </td>
                  <td>{item.reorder_level} {item.unit}</td>
                  <td>{item.unit}</td>
                  <td>₹{item.unit_cost}</td>
                  <td>₹{item.inventory_value.toLocaleString('en-IN')}</td>
                  <td>
                    <span className={`status-badge status-${getStockStatus(item)}`}>
                      {getStockStatus(item) === 'critical' && <AlertCircle size={14} />}
                      {getStockStatus(item)}
                    </span>
                  </td>
                  <td>
                    <div className="action-buttons">
                      <button 
                        className="btn-icon btn-icon-edit"
                        onClick={() => navigate(`/inventory/edit/${item.id}`)}
                        title="Edit"
                      >
                        <Edit size={16} />
                      </button>
                      <button 
                        className="btn-icon btn-icon-delete"
                        onClick={() => deleteItem(item.id)}
                        title="Delete"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredItems.length === 0 && (
            <div className="empty-state">
              <Package size={48} />
              <h3>No items found</h3>
              <p>Try adjusting your filters or add a new item</p>
              <button 
                className="btn-primary"
                onClick={() => navigate('/inventory/add')}
              >
                <Plus size={18} />
                Add Item
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default InventoryList;
