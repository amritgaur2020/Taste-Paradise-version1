import React, { useState } from 'react';
import './DiscountSection.css';

const DiscountSection = ({ subtotal, discount, onDiscountChange, onDiscountRemove }) => {
  const [isExpanded, setIsExpanded] = useState(!!discount);
  const [discountType, setDiscountType] = useState(discount?.type || 'percentage');
  const [discountValue, setDiscountValue] = useState(discount?.value || '');
  const [discountReason, setDiscountReason] = useState(discount?.reason || '');

  const reasons = [
    'Happy Hour',
    'Festival Offer',
    'Loyalty Discount',
    'Manager Override',
    'Staff Discount',
    'Custom'
  ];

  const calculateDiscountAmount = () => {
    const value = parseFloat(discountValue) || 0;
    if (discountType === 'percentage') {
      return Math.min((subtotal * value) / 100, subtotal);
    }
    return Math.min(value, subtotal);
  };

  const handleApplyDiscount = () => {
    const discountAmount = calculateDiscountAmount();
    onDiscountChange({
      type: discountType,
      value: parseFloat(discountValue) || 0,
      reason: discountReason,
      amount: discountAmount
    });
  };

  const handleRemoveDiscount = () => {
    setDiscountValue('');
    setDiscountReason('');
    onDiscountRemove();
    setIsExpanded(false);
  };

  if (!isExpanded && !discount) {
    return (
      <div className="discount-section-collapsed">
        <span className="discount-label">Discount</span>
        <button 
          className="discount-add-btn"
          onClick={() => setIsExpanded(true)}
        >
          + Add
        </button>
      </div>
    );
  }

  return (
    <div className="discount-section-expanded">
      <div className="discount-header">
        <span className="discount-label">Discount</span>
        {discount && (
          <button 
            className="discount-remove-btn"
            onClick={handleRemoveDiscount}
          >
            🗑️ Remove
          </button>
        )}
      </div>

      {!discount ? (
        <div className="discount-input-area">
          <div className="discount-type-selector">
            <label className="discount-type-option">
              <input
                type="radio"
                value="percentage"
                checked={discountType === 'percentage'}
                onChange={(e) => setDiscountType(e.target.value)}
              />
              <span>Percentage (%)</span>
            </label>
            <label className="discount-type-option">
              <input
                type="radio"
                value="fixed"
                checked={discountType === 'fixed'}
                onChange={(e) => setDiscountType(e.target.value)}
              />
              <span>Fixed Amount (₹)</span>
            </label>
          </div>

          <div className="discount-value-input">
            <input
              type="number"
              min="0"
              max={discountType === 'percentage' ? 100 : subtotal}
              step={discountType === 'percentage' ? 1 : 0.01}
              value={discountValue}
              onChange={(e) => setDiscountValue(e.target.value)}
              placeholder={discountType === 'percentage' ? 'Enter %' : 'Enter ₹'}
            />
            <span className="discount-input-suffix">
              {discountType === 'percentage' ? '%' : '₹'}
            </span>
          </div>

          <select
            value={discountReason}
            onChange={(e) => setDiscountReason(e.target.value)}
            className="discount-reason-select"
          >
            <option value="">Select reason (optional)</option>
            {reasons.map(reason => (
              <option key={reason} value={reason}>{reason}</option>
            ))}
          </select>

          <div className="discount-preview">
            <span>Discount Amount:</span>
            <span className="discount-preview-amount">
              - ₹{calculateDiscountAmount().toFixed(2)}
            </span>
          </div>

          <div className="discount-actions">
            <button
              className="discount-cancel-btn"
              onClick={() => {
                setIsExpanded(false);
                setDiscountValue('');
                setDiscountReason('');
              }}
            >
              Cancel
            </button>
            <button
              className="discount-apply-btn"
              onClick={handleApplyDiscount}
              disabled={!discountValue || parseFloat(discountValue) <= 0}
            >
              Apply Discount
            </button>
          </div>
        </div>
      ) : (
        <div className="discount-applied">
          <div className="discount-applied-details">
            <span className="discount-applied-type">
              {discount.type === 'percentage' 
                ? `${discount.value}% OFF` 
                : `₹${discount.value} OFF`}
            </span>
            {discount.reason && (
              <span className="discount-applied-reason">({discount.reason})</span>
            )}
          </div>
          <span className="discount-applied-amount">- ₹{discount.amount.toFixed(2)}</span>
        </div>
      )}
    </div>
  );
};

export default DiscountSection;
