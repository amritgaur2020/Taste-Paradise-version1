import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Package, 
  AlertTriangle, 
  TrendingUp, 
  Activity,
  Upload,
  Plus,
  RefreshCw,
  ArrowRight
} from 'lucide-react';
import './inventory.css';

// ✅ Use the global API from App.js
const API = window.API || 'http://127.0.0.1:8002/api';

const InventoryDashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    total_items: 0,
    low_stock_items: 0,
    total_inventory_value: 0,
    recent_transactions: 0
  });
  const [loading, setLoading] = useState(true);
  const [lowStockItems, setLowStockItems] = useState([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);

      // Fetch dashboard stats
      const statsRes = await axios.get(`${API}/inventory/dashboard/stats`);
      setStats(statsRes.data);

      // Fetch low stock items
      const alertsRes = await axios.get(`${API}/inventory/alerts/low-stock`);
      setLowStockItems(alertsRes.data.low_stock_items || []);

      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, icon: Icon, color, subtitle, onClick }) => (
    <div className={`stat-card stat-card-${color}`} onClick={onClick}>
      <div className="stat-card-header">
        <div className="stat-card-icon">
          <Icon size={24} />
        </div>
        <h3>{title}</h3>
      </div>
      <div className="stat-card-value">{value}</div>
      {subtitle && <div className="stat-card-subtitle">{subtitle}</div>}
    </div>
  );

  return (
    <div className="inventory-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div>
          <h1>Inventory Management</h1>
          <p className="dashboard-date">
            {new Date().toLocaleDateString('en-IN', { 
              weekday: 'long', 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}
          </p>
        </div>
        <button className="btn-refresh" onClick={fetchDashboardData}>
          <RefreshCw size={18} />
          Refresh
        </button>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <StatCard
          title="Total Items"
          value={stats.total_items}
          icon={Package}
          color="blue"
          subtitle="Active inventory items"
          onClick={() => navigate('/inventory/items')}
        />

        <StatCard
          title="Inventory Value"
          value={`₹${stats.total_inventory_value.toLocaleString('en-IN')}`}
          icon={TrendingUp}
          color="green"
          subtitle="Total stock value"
        />

        <StatCard
          title="Low Stock Alerts"
          value={stats.low_stock_items}
          icon={AlertTriangle}
          color="orange"
          subtitle={stats.low_stock_items > 0 ? "Items need reorder" : "All items stocked"}
          onClick={() => navigate('/inventory/alerts')}
        />

        <StatCard
          title="Recent Transactions"
          value={stats.recent_transactions}
          icon={Activity}
          color="purple"
          subtitle="Last 24 hours"
          onClick={() => navigate('/inventory/transactions')}
        />
      </div>

      {/* Quick Actions */}
      <div className="quick-actions-section">
        <h2>Quick Actions</h2>
        <div className="quick-actions-grid">
          <button 
            className="action-btn action-btn-primary"
            onClick={() => navigate('/inventory/add')}
          >
            <Plus size={20} />
            Add New Item
          </button>

          <button 
            className="action-btn action-btn-secondary"
            onClick={() => navigate('/inventory/items')}
          >
            <Package size={20} />
            View All Items
          </button>

          <button 
            className="action-btn action-btn-secondary"
            onClick={() => navigate('/inventory/import')}
          >
            <Upload size={20} />
            Import from Excel
          </button>

          <button 
            className="action-btn action-btn-secondary"
            onClick={() => navigate('/inventory/transactions')}
          >
            <Activity size={20} />
            View Transactions
          </button>
        </div>
      </div>

      {/* Low Stock Alerts */}
      {lowStockItems.length > 0 && (
        <div className="low-stock-section">
          <div className="section-header">
            <h2>
              <AlertTriangle size={20} className="text-warning" />
              Low Stock Alerts
            </h2>
            <button 
              className="btn-view-all"
              onClick={() => navigate('/inventory/alerts')}
            >
              View All
              <ArrowRight size={16} />
            </button>
          </div>

          <div className="alerts-list">
            {lowStockItems.slice(0, 5).map(item => (
              <div 
                key={item.id} 
                className={`alert-item alert-${item.urgency}`}
              >
                <div className="alert-icon">
                  <AlertTriangle size={20} />
                </div>
                <div className="alert-content">
                  <h4>{item.name}</h4>
                  <p>
                    Current: {item.current_stock_display || `${item.current_stock} ${item.unit}`} / 
                    Reorder: {item.reorder_level} {item.unit}
                  </p>
                </div>
                <div className={`alert-badge badge-${item.urgency}`}>
                  {item.urgency}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Activity */}
      <div className="recent-activity-section">
        <div className="section-header">
          <h2>Recent Activity</h2>
          <button 
            className="btn-view-all"
            onClick={() => navigate('/inventory/transactions')}
          >
            View All
            <ArrowRight size={16} />
          </button>
        </div>

        <div className="activity-summary">
          <div className="activity-item">
            <div className="activity-dot"></div>
            <span>{stats.recent_transactions} transactions in last 24 hours</span>
          </div>
          <div className="activity-item">
            <div className="activity-dot activity-dot-warning"></div>
            <span>{stats.low_stock_items} items below reorder level</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InventoryDashboard;