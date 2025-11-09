import React from 'react';
import './OrderTypeSelector.css';

const OrderTypeSelector = ({ selectedType, onTypeChange }) => {
  const orderTypes = [
    { value: 'takeaway', label: 'TakeAway', icon: '🛍️' },
    { value: 'delivery', label: 'Delivery', icon: '🚚' },
    { value: 'dine-in', label: 'Dine-in', icon: '🍽️' }
  ];

  return (
    <div className="order-type-selector">
      <span className="order-type-label">Order Type:</span>
      <div className="order-type-buttons">
        {orderTypes.map(type => (
          <button
            key={type.value}
            className={`order-type-btn ${selectedType === type.value ? 'active' : ''}`}
            onClick={() => onTypeChange(type.value)}
            type="button"
          >
            <span className="order-type-icon">{type.icon}</span>
            <span className="order-type-text">{type.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default OrderTypeSelector;
