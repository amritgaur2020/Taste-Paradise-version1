import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import { Save, X, ArrowLeft } from 'lucide-react';
import './inventory.css';

const API = window.API || 'http://127.0.0.1:8002/api';

const AddInventoryItem = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEditMode = !!id;

  const [formData, setFormData] = useState({
    name: '',
    category: '',
    unit: 'kg',
    current_stock: '',
    reorder_level: '',
    unit_cost: '',
    supplier: '',
    supplier_contact: ''
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (isEditMode) {
      fetchItem();
    }
  }, [id]);

  const fetchItem = async () => {
    try {
      const response = await axios.get(`${API}/inventory/items/${id}`);
      setFormData(response.data);
    } catch (error) {
      console.error('Error fetching item:', error);
      alert('Failed to load item');
      navigate('/inventory/items');
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validate = () => {
    const newErrors = {};

    if (!formData.name.trim()) newErrors.name = 'Name is required';
    if (!formData.category.trim()) newErrors.category = 'Category is required';
    if (!formData.current_stock || formData.current_stock < 0) {
      newErrors.current_stock = 'Valid current stock is required';
    }
    if (!formData.reorder_level || formData.reorder_level < 0) {
      newErrors.reorder_level = 'Valid reorder level is required';
    }
    if (!formData.unit_cost || formData.unit_cost < 0) {
      newErrors.unit_cost = 'Valid unit cost is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validate()) return;

    try {
      setLoading(true);

      const payload = {
        ...formData,
        current_stock: parseFloat(formData.current_stock),
        reorder_level: parseFloat(formData.reorder_level),
        unit_cost: parseFloat(formData.unit_cost)
      };

      if (isEditMode) {
        await axios.put(`${API}/inventory/items/${id}`, payload);
      } else {
        await axios.post(`${API}/inventory/items`, payload);
      }

      navigate('/inventory/items');
    } catch (error) {
      console.error('Error saving item:', error);
      alert('Failed to save item');
      setLoading(false);
    }
  };

  return (
    <div className="add-inventory-page">
      {/* Header */}
      <div className="page-header">
        <button className="btn-back" onClick={() => navigate('/inventory/items')}>
          <ArrowLeft size={20} />
        </button>
        <div>
          <h1>{isEditMode ? 'Edit' : 'Add'} Inventory Item</h1>
          <p>Enter item details below</p>
        </div>
      </div>

      {/* Form */}
      <div className="form-container">
        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            {/* Item Name */}
            <div className="form-group">
              <label>
                Item Name <span className="required">*</span>
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="e.g., Paneer, Oil, Onion"
                className={errors.name ? 'error' : ''}
              />
              {errors.name && <span className="error-message">{errors.name}</span>}
            </div>

            {/* Category */}
            <div className="form-group">
              <label>
                Category <span className="required">*</span>
              </label>
              <input
                type="text"
                name="category"
                value={formData.category}
                onChange={handleChange}
                placeholder="e.g., Dairy, Vegetables, Spices"
                className={errors.category ? 'error' : ''}
              />
              {errors.category && <span className="error-message">{errors.category}</span>}
            </div>

            {/* Unit */}
            <div className="form-group">
              <label>
                Unit <span className="required">*</span>
              </label>
              <select
                name="unit"
                value={formData.unit}
                onChange={handleChange}
              >
                <option value="kg">Kilogram (kg)</option>
                <option value="gm">Gram (gm)</option>
                <option value="ltr">Liter (ltr)</option>
                <option value="ml">Milliliter (ml)</option>
                <option value="pieces">Pieces</option>
              </select>
            </div>

            {/* Current Stock */}
            <div className="form-group">
              <label>
                Current Stock <span className="required">*</span>
              </label>
              <input
                type="number"
                name="current_stock"
                value={formData.current_stock}
                onChange={handleChange}
                placeholder="0"
                step="0.01"
                min="0"
                className={errors.current_stock ? 'error' : ''}
              />
              {errors.current_stock && (
                <span className="error-message">{errors.current_stock}</span>
              )}
            </div>

            {/* Reorder Level */}
            <div className="form-group">
              <label>
                Reorder Level <span className="required">*</span>
              </label>
              <input
                type="number"
                name="reorder_level"
                value={formData.reorder_level}
                onChange={handleChange}
                placeholder="0"
                step="0.01"
                min="0"
                className={errors.reorder_level ? 'error' : ''}
              />
              {errors.reorder_level && (
                <span className="error-message">{errors.reorder_level}</span>
              )}
              <small className="form-hint">
                You'll be alerted when stock falls below this level
              </small>
            </div>

            {/* Unit Cost */}
            <div className="form-group">
              <label>
                Unit Cost (₹) <span className="required">*</span>
              </label>
              <input
                type="number"
                name="unit_cost"
                value={formData.unit_cost}
                onChange={handleChange}
                placeholder="0.00"
                step="0.01"
                min="0"
                className={errors.unit_cost ? 'error' : ''}
              />
              {errors.unit_cost && (
                <span className="error-message">{errors.unit_cost}</span>
              )}
            </div>

            {/* Supplier */}
            <div className="form-group">
              <label>Supplier Name</label>
              <input
                type="text"
                name="supplier"
                value={formData.supplier}
                onChange={handleChange}
                placeholder="e.g., ABC Suppliers"
              />
            </div>

            {/* Supplier Contact */}
            <div className="form-group">
              <label>Supplier Contact</label>
              <input
                type="text"
                name="supplier_contact"
                value={formData.supplier_contact}
                onChange={handleChange}
                placeholder="e.g., +91-9876543210"
              />
            </div>
          </div>

          {/* Summary Card */}
          {formData.current_stock && formData.unit_cost && (
            <div className="summary-card">
              <h3>Inventory Value</h3>
              <div className="summary-value">
                ₹{(formData.current_stock * formData.unit_cost).toLocaleString('en-IN', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
                })}
              </div>
              <p className="summary-details">
                {formData.current_stock} {formData.unit} × ₹{formData.unit_cost} per {formData.unit}
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="form-actions">
            <button
              type="button"
              className="btn-secondary"
              onClick={() => navigate('/inventory/items')}
              disabled={loading}
            >
              <X size={18} />
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={loading}
            >
              <Save size={18} />
              {loading ? 'Saving...' : (isEditMode ? 'Update' : 'Save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddInventoryItem;