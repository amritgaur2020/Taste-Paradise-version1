import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './AddCustomerModal.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8002';
const API = `${BACKEND_URL}/api`;


const AddCustomerModal = ({ isOpen, onClose, onCustomerSelect, onViewCustomer }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isCreatingNew, setIsCreatingNew] = useState(false);
  const [newCustomer, setNewCustomer] = useState({
    name: '',
    phone: '',
    email: '',
    addresses: [{ type: 'home', line1: '', line2: '', landmark: '', city: '', pincode: '', isdefault: true }]
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Search customers as user types
  useEffect(() => {
    const searchCustomers = async () => {
      if (searchQuery.length < 2) {
        setSearchResults([]);
        return;
      }
      try {
        const response = await axios.get(`${API}/customers/search`, {
          params: { query: searchQuery }
        });
        setSearchResults(response.data);
      } catch (err) {
        console.error('Search error:', err);
      }
    };

    const debounce = setTimeout(searchCustomers, 300);
    return () => clearTimeout(debounce);
  }, [searchQuery]);

  const handleSelectCustomer = (customer) => {
    onCustomerSelect(customer);
    resetAndClose();
  };

  // ✅ NEW: Handle View Customer
  const handleViewCustomer = (customer) => {
    if (onViewCustomer) {
      onViewCustomer(customer);
      resetAndClose();
    }
  };

  const handleCreateCustomer = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await axios.post(`${API}/customers`, newCustomer);
      onCustomerSelect(response.data);
      resetAndClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create customer');
    } finally {
      setLoading(false);
    }
  };

  const resetAndClose = () => {
    setSearchQuery('');
    setSearchResults([]);
    setIsCreatingNew(false);
    setNewCustomer({
      name: '',
      phone: '',
      email: '',
      addresses: [{ type: 'home', line1: '', line2: '', landmark: '', city: '', pincode: '', isdefault: true }]
    });
    setError('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="customer-modal-overlay" onClick={resetAndClose}>
      <div className="customer-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="customer-modal-header">
          <h2>Customer Management</h2>
          <button className="customer-modal-close-btn" onClick={resetAndClose}>×</button>
        </div>

        <div className="customer-modal-body">
          {!isCreatingNew ? (
            <>
              {/* Search Section */}
              <div className="customer-search-section">
                <label>🔍 Search Existing Customer</label>
                <input
                  type="text"
                  placeholder="Type name or phone number..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="customer-search-input"
                />

                {/* Search Results */}
                {searchResults.length > 0 && (
                  <div className="customer-search-results">
                    {searchResults.map((customer) => (
                      <div
                        key={customer.customer_id}
                        className="customer-result-item"
                      >
                        <div className="customer-result-info">
                          <span className="customer-result-name">{customer.name}</span>
                          <span className="customer-result-phone">{customer.phone}</span>
                          {customer.orderhistory?.totalorders > 0 && (
                            <span className="customer-result-orders">
                              {customer.orderhistory.totalorders} previous orders
                            </span>
                          )}
                        </div>

                        {/* ✅ Button Container - Select and View */}
                        <div className="customer-result-actions">
                          <button
                            className="customer-btn-select"
                            onClick={() => handleSelectCustomer(customer)}
                          >
                            Select
                          </button>
                          {/* ✅ NEW View BUTTON */}
                          <button
                            className="customer-btn-view"
                            onClick={() => handleViewCustomer(customer)}
                          >
                            View
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="customer-divider">
                <span>OR</span>
              </div>

              <button
                className="customer-add-new-btn"
                onClick={() => setIsCreatingNew(true)}
              >
                ➕ Add New Customer
              </button>
            </>
          ) : (
            <>
              {/* Create New Customer Form */}
              <form onSubmit={handleCreateCustomer} className="customer-create-form">
                <div className="customer-form-group">
                  <label>Customer Name *</label>
                  <input
                    type="text"
                    required
                    value={newCustomer.name}
                    onChange={(e) => setNewCustomer({ ...newCustomer, name: e.target.value })}
                    placeholder="Enter full name"
                  />
                </div>

                <div className="customer-form-group">
                  <label>Phone Number *</label>
                  <input
                    type="tel"
                    required
                    value={newCustomer.phone}
                    onChange={(e) => setNewCustomer({ ...newCustomer, phone: e.target.value })}
                    placeholder="91-9876543210"
                  />
                </div>

                <div className="customer-form-group">
                  <label>Email (optional)</label>
                  <input
                    type="email"
                    value={newCustomer.email}
                    onChange={(e) => setNewCustomer({ ...newCustomer, email: e.target.value })}
                    placeholder="customer@example.com"
                  />
                </div>

                <div className="customer-form-group">
                  <label>Address for delivery orders</label>
                  <input
                    type="text"
                    value={newCustomer.addresses[0].line1}
                    onChange={(e) => {
                      const addresses = [...newCustomer.addresses];
                      addresses[0].line1 = e.target.value;
                      setNewCustomer({ ...newCustomer, addresses });
                    }}
                    placeholder="Street address, Apartment/Unit"
                  />
                </div>

                <div className="customer-form-row">
                  <div className="customer-form-group">
                    <label>City</label>
                    <input
                      type="text"
                      value={newCustomer.addresses[0].city}
                      onChange={(e) => {
                        const addresses = [...newCustomer.addresses];
                        addresses[0].city = e.target.value;
                        setNewCustomer({ ...newCustomer, addresses });
                      }}
                      placeholder="City"
                    />
                  </div>

                  <div className="customer-form-group">
                    <label>Pincode</label>
                    <input
                      type="text"
                      value={newCustomer.addresses[0].pincode}
                      onChange={(e) => {
                        const addresses = [...newCustomer.addresses];
                        addresses[0].pincode = e.target.value;
                        setNewCustomer({ ...newCustomer, addresses });
                      }}
                      placeholder="560001"
                    />
                  </div>
                </div>

                <div className="customer-form-group">
                  <label>Landmark (optional)</label>
                  <input
                    type="text"
                    value={newCustomer.addresses[0].landmark}
                    onChange={(e) => {
                      const addresses = [...newCustomer.addresses];
                      addresses[0].landmark = e.target.value;
                      setNewCustomer({ ...newCustomer, addresses });
                    }}
                    placeholder="Near Phoenix Mall"
                  />
                </div>

                {error && <div className="customer-error-message">{error}</div>}

                <div className="customer-form-actions">
                  <button
                    type="button"
                    className="customer-btn-secondary"
                    onClick={() => setIsCreatingNew(false)}
                  >
                    Back to Search
                  </button>
                  <button type="submit" className="customer-btn-primary" disabled={loading}>
                    {loading ? 'Saving...' : 'Save & Add to Order'}
                  </button>
                </div>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default AddCustomerModal;
