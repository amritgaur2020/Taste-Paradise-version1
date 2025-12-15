import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { AlertTriangle, ArrowLeft, Edit, TrendingDown, Package } from 'lucide-react';
import './inventory.css';

const API = window.API || 'http://127.0.0.1:8002/api';

const LowStockAlerts = () => {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    count: 0,
    critical_count: 0
  });

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/inventory/alerts/low-stock`);
      setAlerts(response.data.low_stock_items || []);
      setStats({
        count: response.data.count || 0,
        critical_count: response.data.critical_count || 0
      });
      setLoading(false);
    } catch (error) {
      console.error('Error fetching alerts:', error);
      setLoading(false);
    }
  };

  const getUrgencyIcon = (urgency) => {
    if (urgency === 'critical') {
      return <AlertTriangle className="urgency-icon critical" />;
    }
    return <TrendingDown className="urgency-icon warning" />;
  };

  const calculatePercentage = (current, reorder) => {
    return ((current / reorder) * 100).toFixed(0);
  };

  return (
    <div className="alerts-page">
      {/* Header */}
      <div className="page-header">
        <button className="btn-back" onClick={() => navigate('/inventory')}>
          <ArrowLeft size={20} />
        </button>
        <div>
          <h1>Low Stock Alerts</h1>
          <p>{stats.count} items need attention</p>
        </div>
      </div>

      {/* Stats */}
      <div className="alerts-stats">
        <div className="alert-stat alert-stat-warning">
          <AlertTriangle size={24} />
          <div>
            <div className="stat-value">{stats.count}</div>
            <div className="stat-label">Low Stock Items</div>
          </div>
        </div>
        <div className="alert-stat alert-stat-critical">
          <AlertTriangle size={24} />
          <div>
            <div className="stat-value">{stats.critical_count}</div>
            <div className="stat-label">Critical Items</div>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      {loading ? (
        <div className="loading-state">Loading alerts...</div>
      ) : (
        <div className="alerts-container">
          {alerts.map(item => (
            <div 
              key={item.id} 
              className={`alert-card alert-card-${item.urgency}`}
            >
              <div className="alert-card-header">
                {getUrgencyIcon(item.urgency)}
                <div className="alert-item-info">
                  <h3>{item.name}</h3>
                  <span className="category-badge">{item.category}</span>
                </div>
                <span className={`urgency-badge urgency-${item.urgency}`}>
                  {item.urgency}
                </span>
              </div>

              <div className="alert-card-body">
                <div className="stock-info">
                  <div className="stock-item">
                    <span className="stock-label">Current Stock</span>
                    <span className="stock-value current-stock">
                      {item.current_stock_display || `${item.current_stock} ${item.unit}`}
                    </span>
                  </div>
                  <div className="stock-divider">/</div>
                  <div className="stock-item">
                    <span className="stock-label">Reorder Level</span>
                    <span className="stock-value reorder-level">
                      {item.reorder_level} {item.unit}
                    </span>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="stock-progress">
                  <div 
                    className={`progress-bar progress-${item.urgency}`}
                    style={{ 
                      width: `${Math.min(100, calculatePercentage(item.current_stock, item.reorder_level))}%` 
                    }}
                  />
                </div>
                <div className="progress-label">
                  {calculatePercentage(item.current_stock, item.reorder_level)}% of reorder level
                </div>

                <div className="needed-quantity">
                  <Package size={16} />
                  <span>
                    Need to order: <strong>{item.needed.toFixed(2)} {item.unit}</strong>
                  </span>
                </div>

                {item.supplier && (
                  <div className="supplier-info">
                    <div className="supplier-detail">
                      <span className="supplier-label">Supplier:</span>
                      <span className="supplier-value">{item.supplier}</span>
                    </div>
                    {item.supplier_contact && (
                      <div className="supplier-detail">
                        <span className="supplier-label">Contact:</span>
                        <span className="supplier-value">{item.supplier_contact}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="alert-card-footer">
                <button
                  className="btn-action btn-edit"
                  onClick={() => navigate(`/inventory/edit/${item.id}`)}
                >
                  <Edit size={16} />
                  Update Stock
                </button>
              </div>
            </div>
          ))}

          {alerts.length === 0 && (
            <div className="empty-state">
              <AlertTriangle size={48} className="text-success" />
              <h3>All Good!</h3>
              <p>No low stock items at the moment</p>
              <button 
                className="btn-primary"
                onClick={() => navigate('/inventory/items')}
              >
                View Inventory
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default LowStockAlerts;