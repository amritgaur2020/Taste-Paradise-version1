import React, { useState } from 'react';
import './OpenItemModal.css';

const OpenItemModal = ({ isOpen, onClose, onAddItem, categories = [] }) => {
  const [itemData, setItemData] = useState({
    name: '',
    food_type: 'other',
    price: '',
    quantity: 1,
    category: '',
    description: '',
    taxable: true
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    
    const customItem = {
      menu_item_id: `CUSTOM-${Date.now()}`,
      menu_item_name: itemData.name,
      price: parseFloat(itemData.price),
      quantity: itemData.quantity,
      food_type: itemData.food_type,
      is_custom_item: true,
      category: itemData.category || 'Other Charges',
      description: itemData.description,
      taxable: itemData.taxable,
      special_instructions: '',
      added_at: new Date().toISOString()
    };

    onAddItem(customItem);
    
    // Reset form
    setItemData({
      name: '',
      food_type: 'other',
      price: '',
      quantity: 1,
      category: '',
      description: '',
      taxable: true
    });
    
    onClose();
  };

  const calculateTotal = () => {
    const price = parseFloat(itemData.price) || 0;
    const quantity = itemData.quantity || 1;
    return (price * quantity).toFixed(2);
  };

  if (!isOpen) return null;

  return (
    <div className="open-item-modal-overlay" onClick={onClose}>
      <div className="open-item-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="open-item-modal-header">
          <h2>Add Custom Item</h2>
          <button className="open-item-modal-close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="open-item-modal-body">
          <form onSubmit={handleSubmit} className="open-item-form">
            <div className="open-item-form-group">
              <label>Item Name *</label>
              <input
                type="text"
                required
                value={itemData.name}
                onChange={(e) => setItemData({...itemData, name: e.target.value})}
                placeholder='Example: "Half Portion Dal Makhani"'
              />
            </div>

            <div className="open-item-form-group">
              <label>Item Type</label>
              <div className="open-item-radio-group">
                <label className="open-item-radio-option">
                  <input
                    type="radio"
                    value="veg"
                    checked={itemData.food_type === 'veg'}
                    onChange={(e) => setItemData({...itemData, food_type: e.target.value})}
                  />
                  <span>🟢 Veg</span>
                </label>
                <label className="open-item-radio-option">
                  <input
                    type="radio"
                    value="non-veg"
                    checked={itemData.food_type === 'non-veg'}
                    onChange={(e) => setItemData({...itemData, food_type: e.target.value})}
                  />
                  <span>🔴 Non-Veg</span>
                </label>
                <label className="open-item-radio-option">
                  <input
                    type="radio"
                    value="other"
                    checked={itemData.food_type === 'other'}
                    onChange={(e) => setItemData({...itemData, food_type: e.target.value})}
                  />
                  <span>⚪ Other</span>
                </label>
              </div>
            </div>

            <div className="open-item-form-group">
              <label>Price (₹) *</label>
              <input
                type="number"
                required
                min="0"
                step="0.01"
                value={itemData.price}
                onChange={(e) => setItemData({...itemData, price: e.target.value})}
                placeholder="0.00"
              />
            </div>

            <div className="open-item-form-group">
              <label>Quantity</label>
              <div className="open-item-quantity-control">
                <button
                  type="button"
                  className="open-item-qty-btn"
                  onClick={() => setItemData({...itemData, quantity: Math.max(1, itemData.quantity - 1)})}
                >
                  −
                </button>
                <input
                  type="number"
                  min="1"
                  value={itemData.quantity}
                  onChange={(e) => setItemData({...itemData, quantity: parseInt(e.target.value) || 1})}
                  className="open-item-qty-input"
                />
                <button
                  type="button"
                  className="open-item-qty-btn"
                  onClick={() => setItemData({...itemData, quantity: itemData.quantity + 1})}
                >
                  +
                </button>
              </div>
            </div>

            <div className="open-item-form-group">
              <label>Category (optional)</label>
              <select
                value={itemData.category}
                onChange={(e) => setItemData({...itemData, category: e.target.value})}
              >
                <option value="">Select category</option>
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
                <option value="Other Charges">Other Charges</option>
              </select>
            </div>

            <div className="open-item-form-group">
              <label>Description (optional)</label>
              <textarea
                value={itemData.description}
                onChange={(e) => setItemData({...itemData, description: e.target.value})}
                placeholder="Internal notes for kitchen/billing"
                rows="2"
              />
            </div>

            <div className="open-item-form-group open-item-checkbox-group">
              <label className="open-item-checkbox-label">
                <input
                  type="checkbox"
                  checked={itemData.taxable}
                  onChange={(e) => setItemData({...itemData, taxable: e.target.checked})}
                />
                <span>Apply standard tax (5%)</span>
              </label>
            </div>

            <div className="open-item-total">
              <strong>Total:</strong>
              <span className="open-item-total-amount">₹ {calculateTotal()}</span>
            </div>

            <div className="open-item-form-actions">
              <button type="button" className="open-item-btn-secondary" onClick={onClose}>
                Cancel
              </button>
              <button type="submit" className="open-item-btn-primary">
                Add to Cart
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default OpenItemModal;
