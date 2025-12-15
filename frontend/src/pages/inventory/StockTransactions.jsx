import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Search, Activity } from 'lucide-react';
import './inventory.css';

const API = window.API || 'http://127.0.0.1:8002/api';

const StockTransactions = () => {
  const navigate = useNavigate();
  const [transactions, setTransactions] = useState([]);
  const [filteredTransactions, setFilteredTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchTransactions();
  }, []);

  useEffect(() => {
    filterTransactions();
  }, [transactions, searchTerm]);

  const fetchTransactions = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/inventory/transactions`);
      setTransactions(response.data.transactions || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching transactions:', error);
      setLoading(false);
    }
  };

  const filterTransactions = () => {
    if (!searchTerm) {
      setFilteredTransactions(transactions);
      return;
    }

    const filtered = transactions.filter(txn =>
      txn.item_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (txn.order_id && txn.order_id.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (txn.menu_item && txn.menu_item.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    setFilteredTransactions(filtered);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getTransactionTypeColor = (type) => {
    switch (type) {
      case 'order_deduction':
        return 'red';
      case 'purchase':
        return 'green';
      case 'adjustment':
        return 'blue';
      default:
        return 'gray';
    }
  };

  return (
    <div className="transactions-page">
      {/* Header */}
      <div className="page-header">
        <button className="btn-back" onClick={() => navigate('/inventory')}>
          <ArrowLeft size={20} />
        </button>
        <div>
          <h1>Stock Transactions</h1>
          <p>{filteredTransactions.length} transactions</p>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-section">
        <div className="search-box">
          <Search size={20} />
          <input
            type="text"
            placeholder="Search by item name, order ID, or menu item..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Transactions List */}
      {loading ? (
        <div className="loading-state">Loading transactions...</div>
      ) : (
        <div className="transactions-list">
          {filteredTransactions.map(txn => (
            <div key={txn.id} className="transaction-card">
              <div className="transaction-header">
                <div className="transaction-item-info">
                  <h3>{txn.item_name}</h3>
                  {txn.menu_item && (
                    <span className="menu-item-tag">
                      For: {txn.menu_item}
                    </span>
                  )}
                </div>
                <span className={`transaction-type type-${getTransactionTypeColor(txn.transaction_type)}`}>
                  {txn.transaction_type.replace('_', ' ')}
                </span>
              </div>

              <div className="transaction-details">
                <div className="transaction-detail">
                  <span className="detail-label">Quantity</span>
                  <span className="detail-value quantity-deducted">
                    -{txn.quantity_deducted} {txn.unit}
                  </span>
                </div>

                <div className="transaction-detail">
                  <span className="detail-label">Previous Stock</span>
                  <span className="detail-value">
                    {txn.previous_stock} {txn.storage_unit}
                  </span>
                </div>

                <div className="transaction-detail">
                  <span className="detail-label">New Stock</span>
                  <span className="detail-value">
                    {txn.new_stock} {txn.storage_unit}
                  </span>
                </div>

                {txn.recipe_quantity && txn.recipe_unit && (
                  <div className="transaction-detail">
                    <span className="detail-label">Recipe Used</span>
                    <span className="detail-value">
                      {txn.recipe_quantity} {txn.recipe_unit}
                    </span>
                  </div>
                )}
              </div>

              <div className="transaction-footer">
                {txn.order_id && (
                  <span className="order-id-badge">
                    Order: {txn.order_id}
                  </span>
                )}
                <span className="transaction-date">
                  {formatDate(txn.transaction_date)}
                </span>
                <span className="transaction-author">
                  by {txn.created_by || 'System'}
                </span>
              </div>
            </div>
          ))}

          {filteredTransactions.length === 0 && (
            <div className="empty-state">
              <Activity size={48} />
              <h3>No transactions found</h3>
              <p>Transaction history will appear here</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default StockTransactions;