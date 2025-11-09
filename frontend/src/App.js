// Add this at the very top after imports
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://127.0.0.1:8002';
const API = `${BACKEND_URL}/api`;

console.log('🔧 Using Backend URL:', BACKEND_URL);

// Make available globally for ALL components
window.API_BASE_URL = BACKEND_URL;  // ✅ Global fallback
window.API = API;  // ✅ Global API URL

// ✅ ADD THIS: Configure axios to never cache and add timestamp to all requests
axios.defaults.headers.common['Cache-Control'] = 'no-cache, no-store, must-revalidate';
axios.defaults.headers.common['Pragma'] = 'no-cache';
axios.defaults.headers.common['Expires'] = '0';

// Add timestamp to all GET requests to force fresh data
axios.interceptors.request.use(config => {
  if (config.method === 'get') {
    config.params = {
      ...config.params,
      _t: new Date().getTime()
    };
  }
  return config;
});

import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import PrintInvoice from './components/PrintInvoice';
import ConfigureSoundboxModal from './components/Payments/ConfigureSoundboxModal';  
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import './components/InvoicePrint.css';
import CustomerDetailsModal from './components/CustomerDetailsModal';
import OrderTypeSelector from './components/OrderTypeSelector';
import AddCustomerModal from './components/AddCustomerModal';
import OpenItemModal from './components/OpenItemModal';
import DiscountSection from './components/DiscountSection';
import VegNonVegIcon from './components/VegNonVegIcon';
import PrintKOT from './components/PrintKOT';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from './components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './components/ui/dialog';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Textarea } from './components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './components/ui/select';
import {
  ChefHat,
  DollarSign,
  Clock,
  Users,
  Plus,
  Edit3,
  Trash2,
  Eye,
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
  Receipt,
  Wallet,
  Volume2,
  Settings,
  Download,
  Printer,
  FileText,
  TrendingUp,
  TrendingDown,
  Calendar,
  Search,
  Filter,
  Upload,
  Bell,
  LogOut,
  Menu,
  X,
  Phone,
  Mail,
  MapPin,
  CreditCard,
  QrCode,
  Smartphone,
  History,
  AlertTriangle,
  Zap,
}
 from 'lucide-react';
import './App.css';



// Context for sharing state across components
const RestaurantContext = createContext();
const useRestaurant = () => {
  const context = useContext(RestaurantContext);
  if (!context) {
    throw new Error('useRestaurant must be used within RestaurantProvider');
  }
  return context;
};

// Table Management Component
const TableManagement = ({ onTableSelect }) => {
  const { refreshData, orders } = useRestaurant();
  const [tables, setTables] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAddTable, setShowAddTable] = useState(false); 
  const [newTableData, setNewTableData] = useState({
    table_number: '',
    capacity: 4,
    position_x: 0,
    position_y: 0
  });

  useEffect(() => {
    fetchTables();
  }, []);

  const fetchTables = async () => {
    try {
      const response = await axios.get(`${API}/tables`);
      setTables(response.data);
      
      // If no tables exist, create default ones
      if (response.data.length === 0) {
        await initializeDefaultTables();
      }
    } catch (error) {
      console.error('Error fetching tables:', error);
    }
  };

  const initializeDefaultTables = async () => {
    try {
      await axios.post(`${API}/tables/initialize-default`);
      await fetchTables();
    } catch (error) {
      console.error('Error initializing tables:', error);
    }
  };

  const getTableColor = (status) => {
    switch (status) {
      case 'available':
        return 'bg-teal-500 hover:bg-teal-600';
      case 'occupied':
        return 'bg-red-500 hover:bg-red-600';
      case 'reserved':
        return 'bg-yellow-500 hover:bg-yellow-600';
      case 'cleaning':
        return 'bg-gray-500 hover:bg-gray-600';
      default:
        return 'bg-teal-500 hover:bg-teal-600';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'available':
        return '✓';
      case 'occupied':
        return '👥';
      case 'reserved':
        return '📅';
      case 'cleaning':
        return '🧹';
      default:
        return '✓';
    }
  };

 
  const handleKotClick = (kotData) => {
  console.log('KOT Clicked:', kotData);
  setSelectedKot(kotData);
  setIsPrintModalOpen(true);
};
  const handleTableClick = async (table) => {
 

    // Check if table has active orders
    const tableOrders = orders.filter(order => 
      order.table_number === table.table_number && 
      !['served', 'cancelled'].includes(order.status)
    );

    if (tableOrders.length > 0) {
      // Table has active orders - show options
      const choice = window.confirm(
        `Table ${table.table_number} has ${tableOrders.length} active orders.\n\nOptions:\nOK - Generate Bill/Process Payment\nCancel - View Orders/Create New Order`
      );
      
      if (choice) {
        // Generate bill for the latest order
        const latestOrder = tableOrders[tableOrders.length - 1];
        if (onTableSelect) onTableSelect(table, 'generate-bill', latestOrder);
      } else {
        if (onTableSelect) onTableSelect(table, 'view-orders');
      }
    } else {
      // Table is empty - create new order
      if (onTableSelect) onTableSelect(table, 'new-order');
    }
  };

  const changeTableStatus = async (tableId, newStatus) => {
    try {
      await axios.put(`${API}/tables/${tableId}`, { status: newStatus });
      await fetchTables();
    } catch (error) {
      console.error('Error updating table status:', error);
    }
  };

  const addNewTable = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/tables`, newTableData);
      await fetchTables();
      setShowAddTable(false);
      setNewTableData({
        table_number: '',
        capacity: 4,
        position_x: 0,
        position_y: 0
      });
      alert('New table added successfully!');
    } catch (error) {
      console.error('Error adding table:', error);
      alert('Error adding table');
    }
  };

  const deleteTable = async (tableId, tableNumber) => {
    const confirmDelete = window.confirm(
      `Are you sure you want to delete Table ${tableNumber}? This action cannot be undone.`
    );
    if (confirmDelete) {
      try {
        await axios.delete(`${API}/tables/${tableId}`);
        await fetchTables();
        alert(`Table ${tableNumber} deleted successfully!`);
      } catch (error) {
        console.error('Error deleting table:', error);
        const errorMessage = error.response?.data?.detail || 'Error deleting table';
        alert(errorMessage);
      }
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span>Restaurant Tables</span>
            <Button
              onClick={fetchTables}
              size="sm"
              variant="outline"
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
          <Button 
            onClick={() => setShowAddTable(true)}
            size="sm"
            className="bg-orange-600 hover:bg-orange-700"
          >
            <Plus className="h-4 w-4 mr-1" />
            Add Table
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Legend */}
        <div className="flex flex-wrap items-center gap-4 mb-6 text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-teal-500 rounded"></div>
            <span>Available</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-red-500 rounded"></div>
            <span>Occupied</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-yellow-500 rounded"></div>
            <span>Reserved</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-gray-500 rounded"></div>
            <span>Cleaning</span>
          </div>
        </div>

        {/* Tables Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {tables.map((table) => (
            <div
              key={table.id}
              className={`relative aspect-square rounded-lg cursor-pointer transition-all duration-200 transform hover:scale-105 ${getTableColor(table.status)} text-white flex flex-col items-center justify-center p-4 shadow-md`}
              onClick={() => handleTableClick(table)}
            >
              <div className="text-xl font-bold">{table.table_number}</div>
              <div className="text-sm opacity-90">Cap: {table.capacity}</div>
              <div className="absolute top-1 right-1 text-lg">
                {getStatusIcon(table.status)}
              </div>
              
              {/* Delete Button */}
              <Button
                size="sm"
                variant="outline"
                className="absolute top-1 left-1 p-1 bg-red-500 hover:bg-red-600 text-white border-none"
                onClick={(e) => {
                  e.stopPropagation();
                  deleteTable(table.id, table.table_number);
                }}
                title={`Delete Table ${table.table_number}`}
              >
                <Trash2 className="h-3 w-3" />
              </Button>

              {/* Quick Status Change */}
              <div className="absolute bottom-1 left-1 right-1">
                <select
                  className="w-full text-xs bg-white/20 text-white rounded px-1 py-0.5"
                  value={table.status}
                  onChange={(e) => {
                    e.stopPropagation();
                    changeTableStatus(table.id, e.target.value);
                  }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <option value="available">Available</option>
                  <option value="occupied">Occupied</option>
                  <option value="reserved">Reserved</option>
                  <option value="cleaning">Cleaning</option>
                </select>
              </div>
            </div>
          ))}
        </div>

        {tables.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <p>No tables found. Initializing default tables...</p>
          </div>
        )}
      </CardContent>

      {/* Add New Table Form */}
      {showAddTable && (
        <Card className="mt-6 border-orange-200">
          <CardHeader>
            <CardTitle>Add New Table</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={addNewTable} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="table-number">Table Number</Label>
                  <Input
                    id="table-number"
                    value={newTableData.table_number}
                    onChange={(e) => setNewTableData({...newTableData, table_number: e.target.value})}
                    placeholder="e.g., T7"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="capacity">Capacity (People)</Label>
                  <Input
                    id="capacity"
                    type="number"
                    value={newTableData.capacity}
                    onChange={(e) => setNewTableData({...newTableData, capacity: parseInt(e.target.value)})}
                    min="1"
                    max="20"
                    required
                  />
                </div>
              </div>
              <div className="flex space-x-2">
                <Button type="submit" className="bg-orange-600 hover:bg-orange-700">
                  Add Table
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowAddTable(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}
    </Card>
  );
};

// Restaurant Context Provider
const RestaurantProvider = ({ children }) => {
  const [orders, setOrders] = useState([]);
  const [menuItems, setMenuItems] = useState([]);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [kots, setKots] = useState([]);
  const [dailyReport, setDailyReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [paymentHistory, setPaymentHistory] = useState([]);
  const [unmatchedPayments, setUnmatchedPayments] = useState([]);

  const [paymentStats, setPaymentStats] = useState({
    total_payments: 0,
    matched_payments: 0,
    unmatched_payments: 0,
    total_amount: 0
  });
  const [showPaymentHistory, setShowPaymentHistory] = useState(false);
  const [loadingPayments, setLoadingPayments] = useState(false);

const refreshData = async () => {
  setLoading(true);
  try {
    // ✅ ADD TIMESTAMP to force fresh data - timestamps already added by interceptor
    // but this ensures cache headers are sent
    const [ordersRes, menuRes, statsRes, kotsRes] = await Promise.all([
      axios.get(`${API}/orders`, {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      }),
      axios.get(`${API}/menu`, {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      }),
      axios.get(`${API}/dashboard`, {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      }),
      axios.get(`${API}/kot`, {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      })
    ]);
    
    setOrders(ordersRes.data);
    setMenuItems(menuRes.data);
    setDashboardStats(statsRes.data);
    setKots(kotsRes.data);
  } catch (error) {
    console.error('Error refreshing data:', error);
  }
  setLoading(false);
};


  const fetchDailyReport = async (date) => {
    try {
      const response = await axios.get(`${API}/report?date=${date}`);
      setDailyReport(response.data);
      return response.data;
    } catch (error) {
      console.error('Error fetching daily report:', error);
      // If no report exists for the date, return default structure
      return {
        date: date,
        revenue: 0,
        orders: 0,
        kots: 0,
        bills: 0,
        invoices: 0,
        orders_list: [],
        kots_list: [],
        bills_list: []
      };
    }
  };

  const refreshDailyReport = async (date) => {
    try {
      const response = await axios.post(`${API}/report/refresh?date=${date}`);
      setDailyReport(response.data);
      return response.data;
    } catch (error) {
      console.error('Error refreshing daily report:', error);
      throw error;
    }
  };

  const updateDailyReport = async (date, reportData) => {
    try {
      const response = await axios.put(`${API}/report?date=${date}`, reportData);
      setDailyReport(response.data);
      return response.data;
    } catch (error) {
      console.error('Error updating daily report:', error);
      throw error;
    }
  };

// ============= PAYMENT HISTORY FUNCTIONS =============

// Fetch payment history
const fetchPaymentHistory = async () => {
  try {
    setLoadingPayments(true);
    const response = await axios.get(`${API}/payments/history?limit=50`);
    console.log('📊 Payment history:', response.data);
    setPaymentHistory(response.data.payments || []);
  } catch (error) {
    console.error('❌ Error fetching payment history:', error);
  } finally {
    setLoadingPayments(false);
  }
};

// Fetch unmatched payments
const fetchUnmatchedPayments = async () => {
  try {
    const response = await axios.get(`${API}/payments/unmatched`);
    console.log('⚠️ Unmatched payments:', response.data);
    setUnmatchedPayments(response.data.unmatched_payments || []);
  } catch (error) {
    console.error('❌ Error fetching unmatched payments:', error);
  }
};

// Fetch payment stats
const fetchPaymentStats = async () => {
  try {
    const response = await axios.get(`${API}/payments/stats`);
    console.log('📈 Payment stats:', response.data);
    setPaymentStats(response.data);
  } catch (error) {
    console.error('❌ Error fetching payment stats:', error);
  }
};

// Manual match payment to order
const manualMatchPayment = async (transactionId, orderId) => {
  try {
    const response = await axios.post(
      `${API}/payments/${transactionId}/match/${orderId}`
    );
    
    // Refresh all data immediately
    await Promise.all([
      fetchPaymentHistory(),
      fetchUnmatchedPayments(),
      fetchPaymentStats(),
      refreshData()
    ]);
    
    // Show success notification after refresh
    setTimeout(() => {
      alert(`✅ Payment matched to order ${orderId} successfully!`);
    }, 300);
  } catch (error) {
    console.error('❌ Error matching payment:', error);
    alert('❌ Error: ' + (error.response?.data?.detail || error.message));
  }
};


// Trigger test webhook
const triggerTestWebhook = async () => {
  try {
    const response = await axios.post(`${API}/webhook/soundbox/test`);
    console.log('🎉 Test webhook response:', response.data);
    
    if (response.data.matched) {
      alert(`✅ Payment matched to order ${response.data.order_id}!`);
    } else {
      alert('⚠️ Payment received but no matching order found');
    }
    
    // Refresh all payment data
    fetchPaymentHistory();
    fetchUnmatchedPayments();
    fetchPaymentStats();
    refreshData();
  } catch (error) {
    console.error('❌ Error triggering test webhook:', error);
    alert('❌ Error: ' + (error.response?.data?.detail || error.message));
  }
};


  // ==================== WEBSOCKET SETUP ====================
const setupWebSocket = (refreshDataCallback) => {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsURL = `${wsProtocol}//${window.location.hostname}:8002/ws`;
    
    console.log("🔗 Connecting to WebSocket...");
    
    const ws = new WebSocket(wsURL);
    
    ws.onopen = () => {
        console.log("✅ WebSocket connected");
    };
    
    ws.onmessage = async (event) => {
        try {
            const message = JSON.parse(event.data);
            console.log("📨 WebSocket message:", message.type, message);
            
            // ✅ FOR PAYMENT UPDATES - Use functional setState to get latest state
            if (message.type === 'payment_updated') {
                console.log("💳 Payment update detected for order:", message.order_id);
                
                // ✅ Use functional setState to access current orders state
                setOrders(currentOrders => {
                    console.log("📝 Current orders count:", currentOrders.length);
                    const updatedOrders = currentOrders.map(order => {
                        if (order.id === message.order_id) {
                            console.log("✅ Updating order payment:", order.id);
                            return {
                                ...order,
                                payment_status: message.payment_status,
                                payment_method: message.payment_method
                            };
                        }
                        return order;
                    });
                    return updatedOrders;
                });
                return;
            }
            
            // For other events
            if (['order_created', 'order_updated', 'kot_generated'].includes(message.type)) {
                console.log(`🔄 ${message.type} - calling refreshData`);
                await refreshDataCallback();
            }
        } catch (error) {
            console.error("❌ Error parsing WebSocket message:", error);
        }
    };
    
    ws.onerror = (error) => {
        console.error("❌ WebSocket error:", error);
    };
    
    ws.onclose = () => {
        console.log("🔌 WebSocket disconnected");
        // ✅ DO NOT RECONNECT - prevents infinite loop
    };
    
    return ws;
};




useEffect(() => {
    console.log("🚀 RestaurantProvider mounting");
    refreshData();
    
    // ✅ Setup WebSocket ONLY ONCE on mount
    const ws = setupWebSocket(refreshData);
    
    // Cleanup on unmount only
    return () => {
        console.log("🔌 Cleaning up WebSocket");
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.close();
        }
    };
}, []); // ✅ Empty dependency array - runs ONLY ONCE
  


  const value = {
    orders, setOrders,
    menuItems, setMenuItems,
    dashboardStats, setDashboardStats,
    kots, setKots,
    dailyReport, setDailyReport,
    loading,
    refreshData,
    fetchDailyReport,
    refreshDailyReport,
    updateDailyReport,
    paymentHistory,
    unmatchedPayments,
    paymentStats,
    showPaymentHistory,
    setShowPaymentHistory,
    loadingPayments,
    fetchPaymentHistory,
    fetchUnmatchedPayments,
    fetchPaymentStats,
    manualMatchPayment,
    triggerTestWebhook  
  };

  return (
    <RestaurantContext.Provider value={value}>
      {children}
    </RestaurantContext.Provider>
  );
};

// Navigation Component
const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: DollarSign },
    { path: '/orders', label: 'Orders', icon: Users },
    { path: '/new-order', label: 'New Order', icon: Plus },
    { path: '/kot', label: 'KOT', icon: ChefHat },
    { path: '/menu', label: 'Menu', icon: Edit3 },
    { path: '/daily-report', label: 'Daily Report', icon: FileText },
    { path: '/payments', label: 'Payments', icon: Wallet }
  ];

  return (
    <div className="border-b bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-8">
            <h1 className="text-2xl font-bold text-orange-600">Taste Paradise</h1>
            <nav className="hidden md:flex space-x-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Button
                    key={item.path}
                    variant={isActive ? 'default' : 'ghost'}
                    className={`flex items-center space-x-2 ${isActive ? 'bg-orange-100 text-orange-700' : ''}`}
                    onClick={() => navigate(item.path)}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </Button>
                );
              })}
            </nav>
          </div>
          <RefreshDataButton />
        </div>
      </div>
    </div>
  );
};

const RefreshDataButton = () => {
  const { refreshData, loading } = useRestaurant();
  
  return (
    <Button
      onClick={refreshData}
      disabled={loading}
      variant="outline"
      size="sm"
      className="flex items-center space-x-2"
    >
      <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
      <span>Refresh</span>
    </Button>
  );
};

// Dashboard Component
const Dashboard = () => {
  const { dashboardStats, loading, orders, refreshData } = useRestaurant();
  const navigate = useNavigate();
  const [selectedTable, setSelectedTable] = useState(null);
  const [showInvoice, setShowInvoice] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);

    // ✅ ADD THIS: Force refresh dashboard data on mount
  useEffect(() => {
    console.log('Dashboard mounted - forcing data refresh');
    refreshData();
  }, []); // Empty dependency array = runs once on mount

  if (loading || !dashboardStats) {
    return <div className="flex justify-center items-center h-96">Loading...</div>;
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'busy':
        return 'bg-yellow-100 text-yellow-800';
      case 'offline':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const handleTableSelect = async (table, action = null, order = null) => {
    setSelectedTable(table);
    if (action === 'generate-bill' && order) {
      // Show invoice for payment
      setSelectedOrder(order);
      setShowInvoice(true);
    } else if (action === 'new-order') {
      // Create new order for this table
      navigate('/new-order', { state: { selectedTable: table.table_number } });
    } else if (action === 'view-orders') {
      navigate('/orders');
    }
  };

  const handlePaymentComplete = async (orderId, paymentMethod) => {
    try {
      // Update payment status
      await axios.put(`${API}/orders/${orderId}`, {
        payment_status: 'paid',
        payment_method: paymentMethod,
        status: 'served'
      });

      // Clear the table (make it available)
      const order = orders.find(o => o.id === orderId);
      if (order?.table_number) {
        // Find the table by table number and update its status
        const tablesResponse = await axios.get(`${API}/tables`);
        const table = tablesResponse.data.find(t => t.table_number === order.table_number);
        if (table) {
          await axios.put(`${API}/tables/${table.id}`, {
            status: 'available',
            current_order_id: null
          });
        }
      }

      await refreshData();
      setShowInvoice(false);
      alert(`Payment received via ${paymentMethod}! Table is now available.`);
    } catch (error) {
      console.error('Error processing payment:', error);
      alert('Error processing payment');
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-gray-900">Restaurant Dashboard</h2>
        <div className="text-sm text-gray-500">
          {new Date().toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-blue-700">Today's Orders</CardTitle>
            <Users className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-900">{dashboardStats.today_orders}</div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-green-700">Today's Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-900">₹{(dashboardStats?.today_revenue || 0).toFixed(2)}</div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-orange-700">Kitchen Status</CardTitle>
            <ChefHat className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <Badge className={`${getStatusColor(dashboardStats.kitchen_status)} capitalize`}>
              {dashboardStats.kitchen_status}
            </Badge>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-purple-700">Pending Payments</CardTitle>
            <Clock className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-900">{dashboardStats.pending_payments}</div>
          </CardContent>
        </Card>
      </div>
        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200 cursor-pointer hover:shadow-lg transition-all hover:scale-105"
          onClick={() => navigate('/payments')} >
        
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-purple-700">Pending Payments</CardTitle>
            <Clock className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-900">{dashboardStats.pending_payments}</div>
            <p className="text-xs text-gray-500 mt-2">← Clickable</p>
            <p className="text-xs text-gray-400 mt-1">
              ↓<br />
              (Clicks here → Goes to<br />
              Payments dashboard)
            </p>
          </CardContent>
        </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Order Status Overview</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Pending Orders</span>
              <Badge variant="secondary">{dashboardStats.pending_orders}</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Cooking Orders</span>
              <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-300">
                {dashboardStats.cooking_orders}
              </Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Ready Orders</span>
              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-300">
                {dashboardStats.ready_orders}
              </Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Served Today</span>
              <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-300">
                {dashboardStats.served_orders}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button className="w-full justify-start bg-orange-600 hover:bg-orange-700" asChild>
              <a href="/new-order">
                <Plus className="mr-2 h-4 w-4" />
                Create New Order
              </a>
            </Button>
            <Button variant="outline" className="w-full justify-start" asChild>
              <a href="/orders">
                <Eye className="mr-2 h-4 w-4" />
                View All Orders
              </a>
            </Button>
            <Button variant="outline" className="w-full justify-start" asChild>
              <a href="/kot">
                <ChefHat className="mr-2 h-4 w-4" />
                Kitchen Orders
              </a>
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Table Management Section */}
      <div className="mt-8">
        <TableManagement onTableSelect={handleTableSelect} />
      </div>

      {/* Invoice Modal */}
      <InvoiceModal
        order={selectedOrder}
        isOpen={showInvoice}
        onClose={() => setShowInvoice(false)}
        onPaymentComplete={handlePaymentComplete}
      />
    </div>
  );
};

// Invoice Component
const InvoiceModal = ({ order, isOpen, onClose, onPaymentComplete }) => {
  console.log('Order data:', order);
  console.log('createdat value:', order?.createdat);
const currentDate = order?.createdat ? new Date(order.createdat) : new Date();

  const gstRate = 0.05; // 5% GST
  const subtotal = order?.total_amount || 0;
  const gstAmount = subtotal * gstRate;
  const finalTotal = subtotal + gstAmount;

  //const printInvoice = () => {
    //window.print();
  //};
  const handlePrint = () => {
    const printWindow = window.open('', '', 'width=800,height=600');
    const invoiceContent = document.getElementById('invoice-content');
    
    if (!invoiceContent) {
      alert('Invoice content not found!');
      return;
    }

    // Clone the invoice content
    const clonedContent = invoiceContent.cloneNode(true);
    
    printWindow.document.write(`
      <html>
        <head>
          <title>Invoice - Taste Paradise</title>
          <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
          <style>
            @media print {
              @page { size: A4; margin: 10mm; }
              body { margin: 0; padding: 0; }
            }
            
            body {
              font-family: Arial, sans-serif;
              margin: 20px;
              background: white;
            }
            
            .invoice-container {
              max-width: 800px;
              margin: 0 auto;
              background: white;
              padding: 30px;
            }
          </style>
        </head>
        <body>
          ${clonedContent.outerHTML}
        </body>
      </html>
    `);
    
    printWindow.document.close();
    printWindow.focus();
    
    setTimeout(() => {
      printWindow.print();
    }, 50);
  };


  if (!order) return null;

    return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <style>{`
        @media print {
          @page { size: 80mm auto; margin: 0; }
  }
`}</style>

      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="invoice-container bg-white p-8 print:fixed print:inset-0 print:z-50 print:w-[80mm]" id="invoice-content" style={{overflow: 'visible', maxHeight: 'none'}}>


          {/* Invoice Header */}
          <div className="border-b-2 border-orange-600 pb-4 mb-6">
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-3xl font-bold text-orange-600">Taste Paradise</h1>
                <p className="text-gray-600">Restaurant & Billing Service</p>
                <p className="text-sm text-gray-500">123 Food Street, Flavor City, FC 12345</p>
                <p className="text-sm text-gray-500">Phone: +91 8218355207 | Email: info@tasteparadise.com</p>
              </div>
              <div className="text-right">
                <h2 className="text-2xl font-bold text-gray-800">INVOICE</h2>
                <p className="text-gray-600">{order.order_id}</p>
                <p className="text-sm text-gray-500">
                  Date: {order?.created_at ? new Date(order.created_at).toLocaleDateString('en-IN') : new Date().toLocaleDateString('en-IN')}
                </p>
                <p className="text-sm text-gray-500">
                  Time: {order?.created_at ? new Date(order.created_at).toLocaleTimeString('en-IN') : new Date().toLocaleTimeString('en-IN')}
                </p>
              </div>
            </div>
          </div>

          {/* Customer Details */}
          <div className="grid grid-cols-2 gap-8 mb-6">
            <div>
              <h3 className="font-bold text-gray-800 mb-2">Bill To:</h3>
              <p className="text-gray-700">{order.customer_name || 'Walk-in Customer'}</p>
              {order.table_number && (
                <p className="text-gray-600">Table: {order.table_number}</p>
              )}
            </div>
            <div>
              <h3 className="font-bold text-gray-800 mb-2">Order Details:</h3>
              <p className="text-gray-600">
                Status: <span className={`capitalize ${order.status === 'cancelled' ? 'text-red-600 font-semibold' : ''}`}>
                  {order.status === 'cancelled' ? 'CANCELLED' : order.status}
                </span>
              </p>
              <p className="text-gray-600">Payment: <span className="capitalize">{order.payment_status}</span></p>
              {order.payment_method && (
                <p className="text-gray-600">Method: <span className="capitalize">{order.payment_method}</span></p>
              )}
            </div>
          </div>

          {/* Items Table */}
          <div className="mb-6">
            <table className="w-full border-collapse">
              <thead className="bg-gray-50">
                <tr>
                  <th className="border border-gray-300 px-4 py-2 text-left">Item</th>
                  <th className="border border-gray-300 px-4 py-2 text-center">Qty</th>
                  <th className="border border-gray-300 px-4 py-2 text-right">Rate (₹)</th>
                  <th className="border border-gray-300 px-4 py-2 text-right">Amount (₹)</th>
                </tr>
              </thead>
              <tbody>
                {order.items.map((item, index) => (
                  <tr key={index}>
                    <td className="border border-gray-300 px-4 py-2">
                      <div>
                        <p className="font-medium">{item.menu_item_name}</p>
                        {item.special_instructions && (
                          <p className="text-sm text-gray-500 italic">Note: {item.special_instructions}</p>
                        )}
                      </div>
                    </td>
                    <td className="border border-gray-300 px-4 py-2 text-center">{item.quantity}</td>
                    <td className="border border-gray-300 px-4 py-2 text-right">₹{item.price.toFixed(2)}</td>
                    <td className="border border-gray-300 px-4 py-2 text-right">₹{(item.quantity * item.price).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Totals */}
          <div className="flex justify-end mb-6">
            <div className="w-64">
              <div className="flex justify-between py-2 border-b">
                <span className="font-medium">Subtotal:</span>
                <span>₹{subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between py-2 border-b">
                <span className="font-medium">GST (5%):</span>
                <span>₹{gstAmount.toFixed(2)}</span>
              </div>
              {order.status === 'cancelled' && (
                <div className="flex justify-between py-2 border-b text-red-600">
                  <span className="font-medium">Cancellation:</span>
                  <span>-₹{finalTotal.toFixed(2)}</span>
                </div>
              )}
              <div className={`flex justify-between py-2 border-t-2 border-orange-600 font-bold text-lg ${order.status === 'cancelled' ? 'text-red-600' : ''}`}>
                <span>Total Amount:</span>
                <span>₹{order.status === 'cancelled' ? '0.00 (REFUNDED)' : finalTotal.toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="border-t pt-4 text-center text-gray-600">
            <p className="text-sm">Thank you for dining with us at Taste Paradise!</p>
            <p className="text-xs mt-2">GST No: 27AAAAA0000A1Z5 | FSSAI Lic: 12345678901234</p>
            <p className="text-xs">This is a computer generated invoice.</p>
          </div>
        </div>

        {/* Payment & Print Buttons */}
        <div className="flex justify-end space-x-2 mt-4 no-print">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
          {/* Payment buttons - only show if payment is pending */}
          {order && order.payment_status === 'pending' && order.status !== 'cancelled' && onPaymentComplete && (
            <>
              <Button 
                onClick={() => onPaymentComplete(order.id, 'cash')}
                className="bg-green-600 hover:bg-green-700"
              >
                💰 Pay Cash
              </Button>
              <Button 
                onClick={() => onPaymentComplete(order.id, 'online')}
                className="bg-blue-600 hover:bg-blue-700"
              >
                💳 Pay Online
              </Button>
            </>
          )}
                {/* REPLACE OLD BUTTON WITH THIS: */}
          <PrintInvoice  onPrint={handlePrint} orderData={{
            invoiceNo: order.orderid,
            tableNo: order.tablenumber,
            customerName: order.customername,
            items: order.items,
            subtotal: subtotal,
            gst: gstAmount,
            serviceCharge: 0,
            total: finalTotal
          }} />
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Orders Component
const Orders = () => {
  const { orders, setOrders, refreshData } = useRestaurant();
  const location = useLocation();
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [showInvoice, setShowInvoice] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [filterDate, setFilterDate] = useState(null);
  const [highlightOrder, setHighlightOrder] = useState(null);
  const [showPaidOnly, setShowPaidOnly] = useState(false);

  // Handle navigation state from Daily Report
  useEffect(() => {
    if (location.state) {
      if (location.state.filterDate) {
        setFilterDate(location.state.filterDate);
      }
      if (location.state.highlightOrder) {
        setHighlightOrder(location.state.highlightOrder);
      }
      if (location.state.showPaidOnly) {
        setShowPaidOnly(location.state.showPaidOnly);
        setSelectedStatus('served'); // Show served orders for bills
      }
    }
  }, [location.state]);

  // Apply filters
  let filteredOrders = orders;
  
  // Filter by status
  if (selectedStatus !== 'all') {
    filteredOrders = filteredOrders.filter(order => order.status === selectedStatus);
  }
  
  // Filter by date if provided
  if (filterDate) {
    const targetDate = new Date(filterDate).toISOString().split('T')[0];
    filteredOrders = filteredOrders.filter(order => {
      const orderDate = new Date(order.created_at).toISOString().split('T')[0];
      return orderDate === targetDate;
    });
  }
  
  // Filter by payment status if showPaidOnly is true
  if (showPaidOnly) {
    filteredOrders = filteredOrders.filter(order => order.payment_status === 'paid');
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'cooking':
        return <ChefHat className="h-4 w-4 text-blue-500" />;
      case 'ready':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'served':
        return <CheckCircle className="h-4 w-4 text-gray-500" />;
      case 'cancelled':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      cooking: 'bg-blue-100 text-blue-800',
      ready: 'bg-green-100 text-green-800',
      served: 'bg-gray-100 text-gray-800',
      cancelled: 'bg-red-100 text-red-800'
    };
    
    return colors[status] || 'capitalize';
  };

const updateOrderStatus = async (orderId, newStatus) => {
  try {
    const response = await axios.put(`${API}/orders/${orderId}`, { 
      status: newStatus 
    });
    await refreshData();
    alert(`Order status updated to ${newStatus}`);
  } catch (error) {
    console.error('Error updating order status:', error);
    alert('Failed: ' + (error.response?.data?.detail || error.message));
  }
};


  const cancelOrder = async (orderId, customerName) => {
    const confirmCancel = window.confirm(
      `Are you sure you want to cancel the order for ${customerName || 'Walk-in Customer'}? This action cannot be undone.`
    );
    if (confirmCancel) {
      try {
        await axios.put(`${API}/orders/${orderId}`, { status: 'cancelled' });
        refreshData();
        alert('Order cancelled successfully!');
      } catch (error) {
        console.error('Error cancelling order:', error);
        alert('Error cancelling order');
      }
    }
  };

// ✅ OPTIMISTIC UPDATE - Update UI immediately without waiting for API
const updatePaymentStatusOptimistic = async (orderId, paymentStatus, paymentMethod = null) => {
  try {
    const updatedOrders = orders.map(order =>
      order.id === orderId 
        ? { 
            ...order, 
            paymentstatus: paymentStatus, 
            paymentmethod: paymentMethod 
          }
        : order
    );
    setOrders(updatedOrders);

    const response = await axios.put(`${API}/orders/${orderId}/pay`, {
      payment_status: paymentStatus,
      payment_method: paymentMethod
    });
    
    await refreshData();
    alert(`Payment marked as ${paymentStatus}`);
    
  } catch (error) {
    console.error('Error updating payment status:', error);
    await refreshData();
    alert('Payment failed: ' + (error.response?.data?.detail || error.message));
  }
};




  const generateBill = (order) => {
    setSelectedOrder(order);
    setShowInvoice(true);
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-gray-900">Order Management</h2>
        {(filterDate || showPaidOnly) && (
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="bg-blue-50 text-blue-700">
              {filterDate ? `Date: ${new Date(filterDate).toLocaleDateString()}` : ''}
              {showPaidOnly ? 'Paid Orders Only' : ''}
            </Badge>
            <Button 
              size="sm" 
              variant="outline" 
              onClick={() => {
                setFilterDate(null);
                setShowPaidOnly(false);
                setHighlightOrder(null);
                setSelectedStatus('all');
              }}
            >
              Clear Filters
            </Button>
          </div>
        )}
      </div>

      <div>
        <Tabs value={selectedStatus} onValueChange={setSelectedStatus}>
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="all">All Orders</TabsTrigger>
            <TabsTrigger value="pending">Pending</TabsTrigger>
            <TabsTrigger value="cooking">Cooking</TabsTrigger>
            <TabsTrigger value="ready">Ready</TabsTrigger>
            <TabsTrigger value="served">Served</TabsTrigger>
            <TabsTrigger value="cancelled">Cancelled</TabsTrigger>
          </TabsList>

          <TabsContent value={selectedStatus} className="mt-6">
            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Order ID</TableHead>
                      <TableHead>Customer</TableHead>
                      <TableHead>Table</TableHead>
                      <TableHead>Items</TableHead>
                      <TableHead>Total</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Payment</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredOrders.map((order) => (
                      <TableRow 
                        key={order.id} 
                        className={highlightOrder === order.id ? 'bg-yellow-50 border-yellow-200' : ''}
                      >
                        <TableCell className="font-mono text-sm">
                          {order.order_id || order._id.slice(-8)}
                        </TableCell>
                        <TableCell>{order.customer_name || 'Walk-in'}</TableCell>
                        <TableCell>{order.table_number || 'N/A'}</TableCell>
                        <TableCell>{order.items.length} items</TableCell>
                        <TableCell className="font-semibold">₹{order.total_amount.toFixed(2)}</TableCell>
                        <TableCell>
                          <Badge className={getStatusBadge(order.status)}>
                            <div className="flex items-center space-x-1">
                              {getStatusIcon(order.status)}
                              <span>{order.status}</span>
                            </div>
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            <Badge 
                              variant={order.payment_status === 'paid' ? 'default' : 'secondary'} // Fixed: use payment_status
                              className={order.payment_status === 'paid' ? 'bg-green-100 text-green-800' : ''}
                            >
                              {order.payment_status} {/* Fixed: use payment_status */}
                            </Badge>
                            {order.payment_method && ( // Fixed: use payment_method
                              <Badge variant="outline" className="text-xs">
                                {order.payment_method} {/* Fixed: use payment_method */}
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {/* Order Status Actions */}
                            {order.status === 'pending' && (
                              <>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => updateOrderStatus(order.id, 'cooking')}
                                  className="text-xs"
                                >
                                  Start Cooking
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => cancelOrder(order.id, order.customer_name)}
                                  className="text-xs bg-red-50 text-red-700 hover:bg-red-100"
                                >
                                  Cancel
                                </Button>
                              </>
                            )}
                            {order.status === 'cooking' && (
                              <>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => updateOrderStatus(order.id, 'ready')}
                                  className="text-xs"
                                >
                                  Ready
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => cancelOrder(order.id, order.customer_name)}
                                  className="text-xs bg-red-50 text-red-700 hover:bg-red-100"
                                >
                                  Cancel
                                </Button>
                              </>
                            )}
                            {order.status === 'ready' && (
                              <Button
                                size="sm"
                                onClick={() => updateOrderStatus(order.id, 'served')}
                                className="text-xs"
                              >
                                Served
                              </Button>
                            )}

                            {/* Payment Actions - Only for non-cancelled orders */}
                            {order.payment_status === 'pending' && order.status !== 'cancelled' && ( // Fixed: use payment_status
                              <>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => updatePaymentStatusOptimistic(order.id, 'paid', 'cash')}
                                  className="text-xs bg-green-50 text-green-700 hover:bg-green-100"
                                >
                                  💰 Cash
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => updatePaymentStatusOptimistic(order.id, 'paid', 'online')}
                                  className="text-xs bg-blue-50 text-blue-700 hover:bg-blue-100"
                                >
                                  💳 Online
                                </Button>
                              </>
                            )}

                            {/* Bill Generation - Only for served/paid orders */}
                            {order.status === 'served' && order.payment_status === 'paid' && order.status !== 'cancelled' && ( // Fixed: use payment_status
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => generateBill(order)}
                                className="text-xs bg-orange-50 text-orange-700 hover:bg-orange-100"
                              >
                                🧾 Bill
                              </Button>
                            )}

                            {/* Show bill for cancelled orders too for refund purposes */}
                            {order.status === 'cancelled' && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => generateBill(order)}
                                className="text-xs bg-gray-50 text-gray-700 hover:bg-gray-100"
                              >
                                📄 Receipt
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Invoice Modal */}
      <InvoiceModal
        order={selectedOrder}
        isOpen={showInvoice}
        onClose={() => setShowInvoice(false)}
      />
    </div>
  );
};

// New Order Component
const NewOrder = () => {
  const { menuItems, refreshData } = useRestaurant();
  const location = useLocation();
  const [cart, setCart] = useState([]);
  const [customerName, setCustomerName] = useState('');
  const [tableNumber, setTableNumber] = useState(location.state?.selectedTable || '');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  

  const categories = ['all', ...new Set(menuItems.map(item => item.category))];
const filteredItems = menuItems.filter(item => {
  // Filter by availability
  if (!item.is_available) return false;
  
  // Filter by category
  if (selectedCategory !== 'all' && item.category !== selectedCategory) {
    return false;
  }
  
  // Filter by search query
  if (searchQuery) {
    const query = searchQuery.toLowerCase();
    return item.name.toLowerCase().includes(query) || 
           item.description.toLowerCase().includes(query);
  }
  
  return true;
});


  // ADD THESE NEW LINES after line 1451:
  const [orderType, setOrderType] = useState('dine-in');
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [discount, setDiscount] = useState(null);
  const [showCustomerModal, setShowCustomerModal] = useState(false);
  const [showOpenItemModal, setShowOpenItemModal] = useState(false);
  const [viewingCustomer, setViewingCustomer] = useState(null);

  const addToCart = (menuItem) => {
    const existingItem = cart.find(item => item.menu_item_id === menuItem.id);
    if (existingItem) {
      setCart(cart.map(item => 
        item.menu_item_id === menuItem.id 
          ? { ...item, quantity: item.quantity + 1 }
          : item
      ));
    } else {
      setCart([...cart, {
        menu_item_id: menuItem.id,
        menu_item_name: menuItem.name,
        quantity: 1,
        price: menuItem.price,
        special_instructions: '',
        food_type: menuItem.food_type || 'veg',
        is_custom_item: false
      }]);
    }
  };

  const addCustomItemToCart = (customItem) => {
  setCart([...cart, customItem]);
};

// NEW: Handle customer selection
const handleCustomerSelect = (customer) => {
  setSelectedCustomer(customer);
  setCustomerName(customer.name);
  setPhone(customer.phone);
  
  // Auto-fill address if delivery order and customer has default address
  if (orderType === 'delivery' && customer.addresses && customer.addresses.length > 0) {
    const defaultAddress = customer.addresses.find(addr => addr.is_default) || customer.addresses[0];
    setAddress(`${defaultAddress.line1}, ${defaultAddress.city}, ${defaultAddress.pincode}`);
  }
};

// NEW: Handle discount changes
const handleDiscountChange = (newDiscount) => {
  setDiscount(newDiscount);
};

const handleDiscountRemove = () => {
  setDiscount(null);
};


  const updateQuantity = (menuItemId, newQuantity) => {
    if (newQuantity === 0) {
      setCart(cart.filter(item => item.menu_item_id !== menuItemId));
    } else {
      setCart(cart.map(item => 
        item.menu_item_id === menuItemId 
          ? { ...item, quantity: newQuantity }
          : item
      ));
    }
  };

  const getSubtotal = () => {
    return cart.reduce((total, item) => total + (item.quantity * item.price), 0);
  };
  const getTax = () => {
    const subtotal = getSubtotal();
    const discountAmount = discount ? discount.amount : 0;
    const taxableAmount = subtotal - discountAmount;
    return taxableAmount * 0.05; // 5% GST
  };

  const getTotalAmount = () => {
    const subtotal = getSubtotal();
    const discountAmount = discount ? discount.amount : 0;
    const tax = getTax();
    return subtotal - discountAmount + tax;
  };

  const submitOrder = async () => {
  if (cart.length === 0) {
    alert('Please add items to cart');
    return;
  }

  // Validation based on order type
  if (orderType === 'dine-in' && !tableNumber) {
    alert('Please enter table number for dine-in orders');
    return;
  }

  if (orderType === 'delivery' && !address) {
    alert('Please enter delivery address');
    return;
  }

  try {
    const orderData = {
      order_type: orderType,
      customer_id: selectedCustomer?.customer_id || null,
      customer_name: customerName || 'Walk-in',
      phone: phone || null,
      address: address || null,
      table_number: orderType === 'dine-in' ? tableNumber : null,
      items: cart,
      discount: discount || null,
      gst_applicable: true
    };

    await axios.post(`${API_BASE_URL}/api/orders`, orderData);

    // Reset form
    setCart([]);
    setCustomerName('');
    setTableNumber('');
    setPhone('');
    setAddress('');
    setDiscount(null);
    setSelectedCustomer(null);
    setOrderType('dine-in');

    alert('Order created successfully!');
    refreshData();
  } catch (error) {
    console.error('Error creating order:', error);
    alert('Error creating order: ' + (error.response?.data?.detail || error.message));
  }
};


  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Menu Items */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex justify-between items-center gap-4">
  <h2 className="text-3xl font-bold text-gray-900">New Order</h2>
  
  <div className="flex items-center gap-3">
    {/* Search Bar */}
    <div className="relative">
      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
      <Input
        type="text"
        placeholder="Search items..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        className="pl-10 w-64"
      />
      {searchQuery && (
        <button
          onClick={() => setSearchQuery('')}
          className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
    
    {/* Category Dropdown */}
    <Select value={selectedCategory} onValueChange={setSelectedCategory}>
      <SelectTrigger className="w-48">
        <SelectValue placeholder="Select category" />
      </SelectTrigger>
      <SelectContent>
        {categories.map(category => (
          <SelectItem key={category} value={category}>
            {category === 'all' ? 'All Categories' : category}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  </div>
</div>

          {/* NEW: Order Type Selector */}
          <OrderTypeSelector 
            selectedType={orderType} 
            onTypeChange={setOrderType} 
         />

          {/* NEW: Action Buttons */}
          <div className="flex gap-3 mt-4">
            <Button
              variant="outline"
              className="flex items-center gap-2"
              onClick={() => setShowCustomerModal(true)}
            >
              <Users className="h-4 w-4" />
              Add Customer
            </Button>
            <Button
              variant="outline"
              className="flex items-center gap-2"
              onClick={() => setShowOpenItemModal(true)}
            >
              <Plus className="h-4 w-4" />
              Open Item
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredItems.map(item => (
              <Card 
  key={item.id} 
  className="hover:shadow-lg transition-shadow cursor-pointer hover:border-orange-300 hover:bg-orange-50"
  onClick={() => addToCart(item)}
>
  <CardContent className="p-4">
    <div className="flex justify-between items-start">
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-2">
          <VegNonVegIcon type={item.food_type || 'veg'} />
          <h3 className="font-semibold text-lg">{item.name}</h3>
        </div>
        <p className="text-gray-600 text-sm mb-3">{item.description}</p>
        <div className="flex items-center justify-between">
          <span className="text-2xl font-bold text-orange-600">₹{item.price}</span>
          <Badge variant="outline" className="text-xs">{item.category}</Badge>
        </div>
      </div>
    </div>
  </CardContent>
</Card>

            ))}
          </div>
        </div>

        {/* Cart */}
        <div className="space-y-6 p-6 lg:sticky lg:top-6 lg:h-fit lg:overflow-y-auto lg:max-h-[calc(100vh-8rem)]">
          <Card>
            <CardHeader>
              <CardTitle>Order Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* NEW: Show selected customer info */}
                {selectedCustomer && (
                  <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-semibold text-green-800">{selectedCustomer.name}</p>
                        <p className="text-sm text-green-600">{selectedCustomer.phone}</p>
                        {selectedCustomer.order_history?.total_orders > 0 && (
                          <p className="text-xs text-green-500 mt-1">
                            {selectedCustomer.order_history.total_orders} previous orders
                          </p>
                        )}
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setSelectedCustomer(null);
                          setCustomerName('');
                          setPhone('');
                          setAddress('');
                        }}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                  </div>
                </div>
              )}
              <div>
                <Label htmlFor="customer-name">Customer Name</Label>
                <Input
                  id="customer-name"
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  placeholder="Enter customer name"
                />
              </div>
              {/* Conditional fields based on order type */}
{orderType === 'dine-in' && (
  <div>
    <Label htmlFor="table-number">Table Number *</Label>
    <Input
      id="table-number"
      value={tableNumber}
      onChange={(e) => setTableNumber(e.target.value)}
      placeholder="Enter table number"
      required
    />
  </div>
)}

{(orderType === 'takeaway' || orderType === 'delivery') && (
  <div>
    <Label htmlFor="phone">Phone Number</Label>
    <Input
      id="phone"
      value={phone}
      onChange={(e) => setPhone(e.target.value)}
      placeholder="+91-9876543210"
    />
  </div>
)}

{orderType === 'delivery' && (
  <div>
    <Label htmlFor="address">Delivery Address *</Label>
    <Textarea
      id="address"
      value={address}
      onChange={(e) => setAddress(e.target.value)}
      placeholder="Enter delivery address"
      rows={3}
      required
    />
  </div>
)}
</CardContent>

          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Cart ({cart.length} items)</CardTitle>
            </CardHeader>
            <CardContent>
              {cart.length === 0 ? (
                <p className="text-gray-500 text-center py-4">No items in cart</p>
              ) : (
                <div className="space-y-4">
                  {cart.map(item => (
  <div key={item.menu_item_id} className="flex items-center justify-between p-2 border rounded">
    <div className="flex-1">
      <div className="flex items-center gap-2">
        <VegNonVegIcon type={item.food_type || 'veg'} size="12px" />
        <h4 className="font-semibold">{item.menu_item_name}</h4>
        {item.is_custom_item && (
          <Badge variant="outline" className="text-xs bg-yellow-50">
            Custom
          </Badge>
        )}
      </div>
      <p className="text-sm text-gray-600">₹{item.price} each</p>
    </div>

                      <div className="flex items-center space-x-2">
                        <Button 
                          size="sm" 
                          variant="outline" 
                          onClick={() => updateQuantity(item.menu_item_id, item.quantity - 1)}
                        >
                          -
                        </Button>
                        <span className="w-8 text-center">{item.quantity}</span>
                        <Button 
                          size="sm" 
                          variant="outline" 
                          onClick={() => updateQuantity(item.menu_item_id, item.quantity + 1)}
                        >
                          +
                        </Button>
                      </div>
                    </div>
                  ))}
                  {/* NEW: Discount Section */}
<div className="border-t pt-4">
  <DiscountSection
    subtotal={getSubtotal()}
    discount={discount}
    onDiscountChange={handleDiscountChange}
    onDiscountRemove={handleDiscountRemove}
  />
</div>

{/* Totals */}
<div className="border-t pt-4 space-y-2">
  <div className="flex justify-between text-sm">
    <span>Subtotal</span>
    <span>₹{getSubtotal().toFixed(2)}</span>
  </div>

  {discount && (
    <div className="flex justify-between text-sm text-orange-600">
      <span>Discount</span>
      <span>- ₹{discount.amount.toFixed(2)}</span>
    </div>
  )}

  <div className="flex justify-between text-sm">
    <span>Tax (5%)</span>
    <span>₹{getTax().toFixed(2)}</span>
  </div>

  <div className="flex justify-between items-center text-lg font-bold border-t pt-2">
    <span>Total</span>
    <span className="text-orange-600">₹{getTotalAmount().toFixed(2)}</span>
  </div>
</div>

<Button
  onClick={submitOrder}
  className="w-full mt-4 bg-orange-600 hover:bg-orange-700"
  disabled={cart.length === 0}
>
  Place Order
</Button>

                </div>
              )}
            </CardContent>
                </Card>
    </div>
  </div>

  {/* NEW: Modals */}
  <AddCustomerModal 
  isOpen={showCustomerModal}
  onClose={() => setShowCustomerModal(false)}
  onCustomerSelect={handleCustomerSelect}
  onViewCustomer={(customer) => setViewingCustomer(customer)}
/>


  <OpenItemModal
    isOpen={showOpenItemModal}
    onClose={() => setShowOpenItemModal(false)}
    onAddItem={addCustomItemToCart}
    categories={categories.filter(cat => cat !== 'all')}
  />
        {/* ✅ ADD THIS NEW MODAL */}
      {viewingCustomer && (
        <CustomerDetailsModal
          customer={viewingCustomer}
          onClose={() => setViewingCustomer(null)}
        />
      )}
</div>
);
};


// KOT Component
const KOTScreen = () => {
  const { orders, kots, refreshData } = useRestaurant();
  const location = useLocation();
  const [filterDate, setFilterDate] = useState(null);
  const [selectedKot, setSelectedKot] = useState(null);              // ← ADD THIS
  const [isPrintModalOpen, setIsPrintModalOpen] = useState(false);
  const [highlightKot, setHighlightKot] = useState(null);

  // Handle navigation state from Daily Report
  useEffect(() => {
    if (location.state) {
      if (location.state.filterDate) {
        setFilterDate(location.state.filterDate);
      }
      if (location.state.highlightKot) {
        setHighlightKot(location.state.highlightKot);
      }
    }
  }, [location.state]);

  const generateKOT = async (orderId) => {
    try {
      await axios.post(`${API}/kot/${orderId}`);
      refreshData();
      alert('KOT generated successfully!');
    } catch (error) {
      console.error('Error generating KOT:', error);
      alert('Error generating KOT');
    }
  };

  const activeOrders = orders.filter(order => 
    ['pending', 'cooking', 'ready'].includes(order.status)
  );

  // Filter KOTs by date if provided
  let filteredKots = kots;
  if (filterDate) {
    const targetDate = new Date(filterDate).toISOString().split('T')[0];
    filteredKots = kots.filter(kot => {
      const kotDate = new Date(kot.created_at).toISOString().split('T')[0];
      return kotDate === targetDate;
    });
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-gray-900">Kitchen Order Tickets (KOT)</h2>
        {filterDate && (
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="bg-blue-50 text-blue-700">
              Date: {new Date(filterDate).toLocaleDateString()}
            </Badge>
            <Button 
              size="sm" 
              variant="outline" 
              onClick={() => {
                setFilterDate(null);
                setHighlightKot(null);
              }}
            >
              Clear Filter
            </Button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pending KOTs */}
        <Card>
          <CardHeader>
            <CardTitle>Orders Needing KOT</CardTitle>
          </CardHeader>
          <CardContent>
            {activeOrders.filter(order => !order.kot_generated).map(order => (
              <div key={order.id} className="border rounded p-4 mb-4">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="font-semibold">Order #{order.id.slice(-6)}</h3>
                  <Button 
                    size="sm" 
                    onClick={() => generateKOT(order.id)}
                    className="bg-orange-600 hover:bg-orange-700"
                  >
                    Generate KOT
                  </Button>
                </div>
                <p className="text-sm text-gray-600 mb-2">
                  {order.customer_name || 'Walk-in'} - Table {order.table_number || 'N/A'}
                </p>
                <div className="space-y-1">
                  {order.items.map((item, idx) => (
                    <div key={idx} className="flex justify-between text-sm">
                      <span>{item.quantity}x {item.menu_item_name}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Generated KOTs */}
        <Card>
          <CardHeader>
            <CardTitle>Recent KOTs</CardTitle>
          </CardHeader>
          <CardContent>
            {filteredKots.map(kot => (
  <div 
    key={kot._id} 
    className="border rounded p-4 mb-4 bg-gray-50 ${highlightKot === kot._id ? 'ring-2 ring-orange-500' : ''}"
    onClick={() => {
      setSelectedKot(kot);
      setIsPrintModalOpen(true);
    }}
    style={{ cursor: 'pointer' }}
  >
    <div className="flex justify-between items-center mb-2">
      <h3 className="font-semibold">{kot.order_number}</h3>
      <Badge className="bg-green-100 text-green-800">{kot.status}</Badge>
    </div>
    <p className="text-sm text-gray-600 mb-2">
      Table {kot.table_number || 'N/A'} - {new Date(kot.created_at).toLocaleTimeString()}
    </p>
    <div className="space-y-1">
      {kot.items.map((item, idx) => (
        <div key={idx} className="flex justify-between items-sm">
          <span>{item.quantity}x {item.menu_item_name}</span>
        </div>
      ))}
    </div>
  </div>
))}

<PrintKOT 
  kot={selectedKot}
  isOpen={isPrintModalOpen}
  onClose={() => {
    setIsPrintModalOpen(false);
    setSelectedKot(null);
  }}
  API={API}
/>

          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Menu Management Component
const MenuManagement = () => {
  const { menuItems, refreshData } = useRestaurant();
  const [isAddingItem, setIsAddingItem] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [importResults, setImportResults] = useState(null);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    category: '',
    preparation_time: 15
  });

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      price: '',
      category: '',
      preparation_time: 15
    });
    setIsAddingItem(false);
    setEditingItem(null);
  };
  const downloadTemplate = async () => {
  try {
    const response = await axios.get(`${API}/menu/template`, {
      responseType: 'blob'
    });
    
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    });
    
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'menu_template.xlsx';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    alert('✅ Template downloaded! Open it, add your menu items, and upload.');
  } catch (error) {
    console.error('Error downloading template:', error);
    alert('❌ Error downloading template: ' + error.message);
  }
};

const handleFileUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  
  if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
    alert('❌ Please upload an Excel file (.xlsx or .xls)');
    return;
  }
  
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    setIsImporting(true);
    const response = await axios.post(`${API}/menu/import`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    
    // Check if response has data
    if (response.data) {
      setImportResults(response.data);
      await refreshData();
      
      const imported = response.data.imported || 0;
      const skipped = response.data.skipped || 0;
      
      alert(`✅ Import Complete!\n\nImported: ${imported} items\nSkipped: ${skipped} duplicates`);
    } else {
      alert('❌ Unexpected response format from server');
    }
    
    event.target.value = '';
  } catch (error) {
    console.error('Import error:', error);
    
    // Better error message
    const errorMsg = error.response?.data?.detail || 
                     error.response?.data?.message || 
                     error.message || 
                     'Unknown error occurred';
    
    alert(`❌ Error importing file: ${errorMsg}`);
  } finally {
    setIsImporting(false);
  }
};


  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        ...formData,
        price: parseFloat(formData.price)
      };
      
      if (editingItem) {
        await axios.put(`${API}/menu/${editingItem.id}`, data);
      } else {
        await axios.post(`${API}/menu`, data);
      }
      
      refreshData();
      resetForm();
      alert(editingItem ? 'Menu item updated!' : 'Menu item added!');
    } catch (error) {
      console.error('Error saving menu item:', error);
      alert('Error saving menu item');
    }
  };

  const deleteItem = async (itemId, itemName) => {
    const confirmDelete = window.confirm(`Are you sure you want to delete "${itemName}"? This action cannot be undone.`);
    if (confirmDelete) {
      try {
        await axios.delete(`${API}/menu/${itemId}`);
        refreshData();
        alert(`"${itemName}" deleted successfully!`);
      } catch (error) {
        console.error('Error deleting menu item:', error);
        alert('Error deleting menu item');
      }
    }
  };

  const clearAllMenuItems = async () => {
    const confirmClear = window.confirm(`WARNING: This will delete ALL ${menuItems.length} menu items! This action cannot be undone. Are you absolutely sure?`);
    if (confirmClear) {
      const finalConfirm = window.confirm('This is your FINAL confirmation. OK to DELETE ALL MENU ITEMS permanently.');
      if (finalConfirm) {
        try {
          // Delete all menu items
          const deletePromises = menuItems.map(item => axios.delete(`${API}/menu/${item.id}`));
          await Promise.all(deletePromises);
          refreshData();
          alert('All menu items have been deleted successfully!');
        } catch (error) {
          console.error('Error clearing menu items:', error);
          alert('Error clearing some menu items. Please try again.');
        }
      }
    }
  };

  const startEdit = (item) => {
    setEditingItem(item);
    setFormData({
      name: item.name,
      description: item.description,
      price: item.price.toString(),
      category: item.category,
      preparation_time: item.preparation_time
    });
    setIsAddingItem(true);
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-gray-900">Menu Management</h2>
        <div className="flex space-x-2">
          <Button 
            onClick={() => setIsAddingItem(true)}
            className="bg-orange-600 hover:bg-orange-700"
          >
            <Plus className="mr-2 h-4 w-4" />
            Add Menu Item
          </Button>
          {menuItems.length > 0 && (
            <Button 
              onClick={clearAllMenuItems}
              variant="outline"
              className="border-red-500 text-red-500 hover:bg-red-50"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Clear All ({menuItems.length})
            </Button>
          )}
        </div>
      </div>

      {/* Add/Edit Form */}
      {isAddingItem && (
        <Card>
          <CardHeader>
            <CardTitle>{editingItem ? 'Edit Menu Item' : 'Add New Menu Item'}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Item Name</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="price">Price (₹)</Label>
                  <Input
                    id="price"
                    type="number"
                    step="0.01"
                    value={formData.price}
                    onChange={(e) => setFormData({...formData, price: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="category">Category</Label>
                  <Input
                    id="category"
                    value={formData.category}
                    onChange={(e) => setFormData({...formData, category: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="prep-time">Preparation Time (minutes)</Label>
                  <Input
                    id="prep-time"
                    type="number"
                    value={formData.preparation_time}
                    onChange={(e) => setFormData({...formData, preparation_time: parseInt(e.target.value)})}
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                />
              </div>
              <div className="flex space-x-2">
                <Button type="submit" className="bg-orange-600 hover:bg-orange-700">
                  {editingItem ? 'Update Item' : 'Add Item'}
                </Button>
                <Button type="button" variant="outline" onClick={resetForm}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Menu Items List */}
      {/* Excel Import Section */}
<Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200 mb-6">
  <CardHeader>
    <CardTitle>📊 Bulk Import Menu Items</CardTitle>
  </CardHeader>
  <CardContent>
    <p className="text-gray-600 mb-4">Import 100+ menu items in seconds from Excel</p>
    
    <div className="flex space-x-2 mb-4">
      <Button 
        onClick={downloadTemplate}
        className="bg-green-600 hover:bg-green-700"
      >
        📥 Download Template
      </Button>
      
      <input
        type="file"
        id="excelFile"
        accept=".xlsx,.xls"
        style={{ display: 'none' }}
        onChange={handleFileUpload}
      />
      
      <Button
        onClick={() => document.getElementById('excelFile').click()}
        className="bg-blue-600 hover:bg-blue-700"
        disabled={isImporting}
      >
        {isImporting ? 'Uploading...' : '📤 Import from Excel'}
      </Button>
    </div>
    
    {importResults && (
      <div className="bg-white p-4 rounded border">
        <p className="text-sm">✅ Imported: <strong>{importResults.imported}</strong> items</p>
        <p className="text-sm">⚠️ Skipped: <strong>{importResults.skipped}</strong> duplicates</p>
        <p className="text-sm">📊 Total: <strong>{importResults.total_rows}</strong> rows</p>
        
        {importResults.errors && importResults.errors.length > 0 && (
          <div className="mt-2 text-red-600 text-sm">
            <strong>Errors:</strong>
            {importResults.errors.map((error, i) => (
              <p key={i}>• {error}</p>
            ))}
          </div>
        )}
      </div>
    )}
  </CardContent>
</Card>

      <Card>
        <CardHeader>
          <CardTitle>Menu Items ({menuItems.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {menuItems.map(item => (
              <div key={item.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-3">
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg">{item.name}</h3>
                    <p className="text-gray-600 text-sm mb-2">{item.description}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-xl font-bold text-orange-600">₹{item.price}</span>
                      <Badge variant="outline">{item.category}</Badge>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      Prep time: {item.preparation_time} mins
                    </p>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <Button 
                    size="sm" 
                    variant="outline" 
                    onClick={() => startEdit(item)}
                  >
                    <Edit3 className="h-4 w-4" />
                  </Button>
                  <Button 
                    size="sm" 
                    variant="outline" 
                    onClick={() => deleteItem(item.id, item.name)}
                    className="text-red-600 hover:text-red-700"
                    title={`Delete ${item.name}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Daily Report Component
const DailyReport = () => {
  const { dailyReport, fetchDailyReport, refreshDailyReport, updateDailyReport, menuItems, refreshData, loading } = useRestaurant();
  const navigate = useNavigate();
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [isEditing, setIsEditing] = useState(false);
  const [editedData, setEditedData] = useState({});
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [editingOrder, setEditingOrder] = useState(null);
  const [editingKot, setEditingKot] = useState(null);
  const [editingBill, setEditingBill] = useState(null);
  const [showHistoricalReports, setShowHistoricalReports] = useState(false);
  const [historicalReports, setHistoricalReports] = useState([]);
  const [lastReportLoad, setLastReportLoad] = useState(null);

  useEffect(() => {
    loadReport();
  }, [selectedDate]);

  const loadReport = async () => {
    // Check if we already loaded this report recently (within 30 seconds)
    const now = Date.now();
    if (lastReportLoad && lastReportLoad.date === selectedDate && (now - lastReportLoad.timestamp) < 30000) {
      console.log('Using cached report data');
      return;
    }
    
    const reportData = await fetchDailyReport(selectedDate);
    setEditedData(reportData);
    setLastReportLoad({ date: selectedDate, timestamp: now });
  };

  const handleRefreshReport = async () => {
    setIsRefreshing(true);
    try {
      await refreshDailyReport(selectedDate);
      // Clear cache to force reload
      setLastReportLoad(null);
      await loadReport();
      alert('Daily report refreshed with latest data!');
    } catch (error) {
      alert('Error refreshing report');
    }
    setIsRefreshing(false);
  };

  const handleGenerateReport = async () => {
    setIsRefreshing(true);
    try {
      // Force generate a new report for the selected date
      setLastReportLoad(null);
      await loadReport();
      alert('Daily report generated successfully!');
    } catch (error) {
      alert('Error generating report');
    }
    setIsRefreshing(false);
  };

  const loadHistoricalReports = async () => {
    try {
      const response = await axios.get(`${API}/reports`);
      setHistoricalReports(response.data);
    } catch (error) {
      console.error('Error loading historical reports:', error);
    }
  };

  const resetTodayReport = async () => {
    try {
      await axios.post(`${API}/reports/reset-today`);
      await loadReport();
      alert('Today\'s report has been reset!');
    } catch (error) {
      console.error('Error resetting today\'s report:', error);
      alert('Error resetting report');
    }
  };

  const cleanupDuplicateReports = async () => {
    try {
      const response = await axios.post(`${API}/reports/cleanup-duplicates`);
      await loadHistoricalReports();
      alert(`Cleanup completed! ${response.data.removed_count} duplicate reports removed.`);
    } catch (error) {
      console.error('Error cleaning up duplicate reports:', error);
      alert('Error cleaning up duplicates');
    }
  };

  const handleSave = async () => {
    try {
      await updateDailyReport(selectedDate, editedData);
      setIsEditing(false);
      alert('Daily report updated successfully!');
    } catch (error) {
      alert('Error updating daily report');
    }
  };

  const handleCancel = () => {
    setEditedData(dailyReport || {});
    setIsEditing(false);
  };

  const handleInputChange = (field, value) => {
    setEditedData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleEditOrder = (order) => {
    setEditingOrder({...order});
  };

  const handleEditKot = (kot) => {
    setEditingKot({...kot});
  };

  const handleEditBill = (bill) => {
    setEditingBill({...bill});
  };

  const updateOrderItem = (orderId, itemIndex, updatedItem) => {
    if (!editingOrder) return;
    
    const updatedItems = [...editingOrder.items];
    updatedItems[itemIndex] = updatedItem;
    
    setEditingOrder({
      ...editingOrder,
      items: updatedItems,
      total_amount: updatedItems.reduce((total, item) => total + (item.quantity * item.price), 0)
    });
  };

  const removeOrderItem = (orderId, itemIndex) => {
    if (!editingOrder) return;
    
    const updatedItems = editingOrder.items.filter((_, index) => index !== itemIndex);
    
    setEditingOrder({
      ...editingOrder,
      items: updatedItems,
      total_amount: updatedItems.reduce((total, item) => total + (item.quantity * item.price), 0)
    });
  };

  const addOrderItem = () => {
    if (!editingOrder) return;
    
    const newItem = {
      menu_item_id: menuItems[0]?.id || '',
      menu_item_name: menuItems[0]?.name || '',
      quantity: 1,
      price: menuItems[0]?.price || 0,
      special_instructions: ''
    };
    
    setEditingOrder({
      ...editingOrder,
      items: [...editingOrder.items, newItem],
      total_amount: [...editingOrder.items, newItem].reduce((total, item) => total + (item.quantity * item.price), 0)
    });
  };

  const saveOrderChanges = async () => {
    if (!editingOrder) return;
    
    try {
      const updateData = {
        customer_name: editingOrder.customer_name,
        table_number: editingOrder.table_number,
        items: editingOrder.items,
        total_amount: editingOrder.total_amount,
        status: editingOrder.status,
        payment_status: editingOrder.payment_status
      };

      // Only include payment_method if payment_status is 'paid'
      if (editingOrder.payment_status === 'paid' && editingOrder.payment_method) {
        updateData.payment_method = editingOrder.payment_method;
      }

      console.log('Updating order with data:', updateData);
      
      const response = await axios.put(`${API}/orders/${editingOrder.id}`, updateData);
      console.log('Order update response:', response.data);
      
      await refreshData();
      await loadReport();
      setEditingOrder(null);
      alert('Order updated successfully!');
    } catch (error) {
      console.error('Error updating order:', error);
      console.error('Error details:', error.response?.data);
      alert(`Error updating order: ${error.response?.data?.detail || error.message}`);
    }
  };

  if (loading && !dailyReport) {
    return <div className="flex justify-center items-center h-96">Loading...</div>;
  }

  const report = dailyReport || editedData;

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-gray-900">Daily Report</h2>
        <div className="flex items-center space-x-4">
          <div>
            <Label htmlFor="report-date">Select Date</Label>
            <Input
              id="report-date"
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="w-40"
            />
          </div>
          <div className="flex space-x-2">
            {isEditing ? (
              <>
                <Button onClick={handleSave} className="bg-green-600 hover:bg-green-700">
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Save
                </Button>
                <Button onClick={handleCancel} variant="outline">
                  <XCircle className="h-4 w-4 mr-2" />
                  Cancel
                </Button>
              </>
            ) : (
              <>
                <Button 
                  onClick={handleGenerateReport}
                  disabled={isRefreshing}
                  variant="outline"
                  className="bg-green-50 text-green-700 hover:bg-green-100"
                >
                  <FileText className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
                  {isRefreshing ? 'Generating...' : 'Generate Report'}
                </Button>
                <Button 
                  onClick={handleRefreshReport} 
                  variant="outline"
                  disabled={isRefreshing}
                  className="bg-blue-50 text-blue-700 hover:bg-blue-100"
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
                  {isRefreshing ? 'Refreshing...' : 'Refresh Data'}
                </Button>
                <Button 
                  onClick={() => {
                    setShowHistoricalReports(true);
                    loadHistoricalReports();
                  }}
                  variant="outline"
                  className="bg-purple-50 text-purple-700 hover:bg-purple-100"
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Historical Reports
                </Button>
                <Button onClick={() => setIsEditing(true)} className="bg-orange-600 hover:bg-orange-700">
                  <Edit3 className="h-4 w-4 mr-2" />
                  Edit Report
                </Button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-green-700">Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            {isEditing ? (
              <Input
                type="number"
                value={editedData.revenue || 0}
                onChange={(e) => handleInputChange('revenue', parseFloat(e.target.value) || 0)}
                className="text-2xl font-bold"
              />
            ) : (
              <div className="text-2xl font-bold text-green-900">₹{report.revenue?.toFixed(2) || '0.00'}</div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-blue-700">Orders</CardTitle>
            <Users className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            {isEditing ? (
              <Input
                type="number"
                value={editedData.orders || 0}
                onChange={(e) => handleInputChange('orders', parseInt(e.target.value) || 0)}
                className="text-2xl font-bold"
              />
            ) : (
              <div className="text-2xl font-bold text-blue-900">{report.orders || 0}</div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-orange-700">KOTs</CardTitle>
            <ChefHat className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            {isEditing ? (
              <Input
                type="number"
                value={editedData.kots || 0}
                onChange={(e) => handleInputChange('kots', parseInt(e.target.value) || 0)}
                className="text-2xl font-bold"
              />
            ) : (
              <div className="text-2xl font-bold text-orange-900">{report.kots || 0}</div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-purple-700">Bills</CardTitle>
            <Receipt className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            {isEditing ? (
              <Input
                type="number"
                value={editedData.bills || 0}
                onChange={(e) => handleInputChange('bills', parseInt(e.target.value) || 0)}
                className="text-2xl font-bold"
              />
            ) : (
              <div className="text-2xl font-bold text-purple-900">{report.bills || 0}</div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-gray-50 to-gray-100 border-gray-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-700">Invoices</CardTitle>
            <FileText className="h-4 w-4 text-gray-600" />
          </CardHeader>
          <CardContent>
            {isEditing ? (
              <Input
                type="number"
                value={editedData.invoices || 0}
                onChange={(e) => handleInputChange('invoices', parseInt(e.target.value) || 0)}
                className="text-2xl font-bold"
              />
            ) : (
              <div className="text-2xl font-bold text-gray-900">{report.invoices || 0}</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Detailed Lists */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Orders List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Orders ({report.orders_list?.length || 0})</span>
              <Button 
                size="sm" 
                variant="outline" 
                onClick={() => navigate('/orders', { state: { filterDate: selectedDate } })}
                className="text-xs"
              >
                <Eye className="h-3 w-3 mr-1" />
                View All
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {report.orders_list?.map((order, index) => (
                <div key={index} className="border rounded p-3 bg-gray-50 hover:bg-gray-100 transition-colors">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold">#{order.id?.slice(-6) || `Order ${index + 1}`}</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-600">₹{order.total_amount?.toFixed(2) || '0.00'}</span>
                      <Button 
                        size="sm" 
                        variant="outline" 
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEditOrder(order);
                        }}
                        className="text-xs"
                      >
                        <Edit3 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600">{order.customer_name || 'Walk-in'}</p>
                  <p className="text-xs text-gray-500">Table: {order.table_number || 'N/A'}</p>
                  <Badge className={`mt-1 text-xs ${order.status === 'served' ? 'bg-green-100 text-green-800' : 
                    order.status === 'cooking' ? 'bg-blue-100 text-blue-800' : 
                    order.status === 'ready' ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'}`}>
                    {order.status}
                  </Badge>
                </div>
              )) || (
                <p className="text-gray-500 text-center py-4">No orders for this date</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* KOTs List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>KOTs ({report.kots_list?.length || 0})</span>
              <Button 
                size="sm" 
                variant="outline" 
                onClick={() => navigate('/kot', { state: { filterDate: selectedDate } })}
                className="text-xs"
              >
                <Eye className="h-3 w-3 mr-1" />
                View All
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {report.kots_list?.map((kot, index) => (
                <div key={index} className="border rounded p-3 bg-orange-50 hover:bg-orange-100 transition-colors">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold">{kot.order_number || `KOT ${index + 1}`}</span>
                    <div className="flex items-center space-x-2">
                      <Badge className="bg-orange-100 text-orange-800">{kot.status}</Badge>
                      <Button 
                        size="sm" 
                        variant="outline" 
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEditKot(kot);
                        }}
                        className="text-xs"
                      >
                        <Edit3 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600">Table: {kot.table_number || 'N/A'}</p>
                  <p className="text-xs text-gray-500">
                    {kot.created_at ? new Date(kot.created_at).toLocaleTimeString() : 'Time not available'}
                  </p>
                </div>
              )) || (
                <p className="text-gray-500 text-center py-4">No KOTs for this date</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Bills List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Bills ({report.bills_list?.length || 0})</span>
              <Button 
                size="sm" 
                variant="outline" 
                onClick={() => navigate('/orders', { state: { filterDate: selectedDate, showPaidOnly: true } })}
                className="text-xs"
              >
                <Eye className="h-3 w-3 mr-1" />
                View All
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {report.bills_list?.map((bill, index) => (
                <div key={index} className="border rounded p-3 bg-green-50 hover:bg-green-100 transition-colors">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold">#{bill.id?.slice(-6) || `Bill ${index + 1}`}</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-600">₹{bill.total_amount?.toFixed(2) || '0.00'}</span>
                      <Button 
                        size="sm" 
                        variant="outline" 
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEditBill(bill);
                        }}
                        className="text-xs"
                      >
                        <Edit3 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600">{bill.customer_name || 'Walk-in'}</p>
                  <p className="text-xs text-gray-500">
                    Payment: <span className="capitalize">{bill.payment_method || 'N/A'}</span>
                  </p>
                  <Badge className="mt-1 text-xs bg-green-100 text-green-800">Paid</Badge>
                </div>
              )) || (
                <p className="text-gray-500 text-center py-4">No bills for this date</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Report Date Info */}
      <Card>
        <CardHeader>
          <CardTitle>Report Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Report Date</Label>
              <p className="text-lg font-semibold">
                {new Date(selectedDate).toLocaleDateString('en-US', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </p>
            </div>
            <div>
              <Label>Last Updated</Label>
              <p className="text-lg font-semibold">
                {report.updated_at ? new Date(report.updated_at).toLocaleString() : 'Not available'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Order Edit Modal */}
      {editingOrder && (
        <Dialog open={!!editingOrder} onOpenChange={() => setEditingOrder(null)}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Edit Order #{editingOrder.id?.slice(-6)}</DialogTitle>
            </DialogHeader>

            <div className="p-6 space-y-6">
              {/* Order Details */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="customer-name">Customer Name</Label>
                  <Input
                    id="customer-name"
                    value={editingOrder.customer_name || ''}
                    onChange={(e) => setEditingOrder({...editingOrder, customer_name: e.target.value})}
                  />
                </div>
                <div>
                  <Label htmlFor="table-number">Table Number</Label>
                  <Input
                    id="table-number"
                    value={editingOrder.table_number || ''}
                    onChange={(e) => setEditingOrder({...editingOrder, table_number: e.target.value})}
                  />
                </div>
                <div>
                  <Label htmlFor="order-status">Order Status</Label>
                  <Select 
                    value={editingOrder.status} 
                    onValueChange={(value) => setEditingOrder({...editingOrder, status: value})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pending">Pending</SelectItem>
                      <SelectItem value="cooking">Cooking</SelectItem>
                      <SelectItem value="ready">Ready</SelectItem>
                      <SelectItem value="served">Served</SelectItem>
                      <SelectItem value="cancelled">Cancelled</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="payment-status">Payment Status</Label>
                  <Select 
                    value={editingOrder.payment_status} 
                    onValueChange={(value) => setEditingOrder({...editingOrder, payment_status: value})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pending">Pending</SelectItem>
                      <SelectItem value="paid">Paid</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Order Items */}
              <div>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold">Order Items</h3>
                  <Button onClick={addOrderItem} size="sm" className="bg-green-600 hover:bg-green-700">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Item
                  </Button>
                </div>
                
                <div className="space-y-3">
                  {editingOrder.items?.map((item, index) => (
                    <div key={index} className="border rounded p-4 bg-gray-50">
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                        <div className="md:col-span-2">
                          <Label>Menu Item</Label>
                          <Select 
                            value={item.menu_item_id} 
                            onValueChange={(value) => {
                              const selectedItem = menuItems.find(mi => mi.id === value);
                              if (selectedItem) {
                                updateOrderItem(editingOrder.id, index, {
                                  ...item,
                                  menu_item_id: selectedItem.id,
                                  menu_item_name: selectedItem.name,
                                  price: selectedItem.price
                                });
                              }
                            }}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {menuItems.map(menuItem => (
                                <SelectItem key={menuItem.id} value={menuItem.id}>
                                  {menuItem.name} - ₹{menuItem.price}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label>Quantity</Label>
                          <Input
                            type="number"
                            min="1"
                            value={item.quantity}
                            onChange={(e) => updateOrderItem(editingOrder.id, index, {
                              ...item,
                              quantity: parseInt(e.target.value) || 1
                            })}
                          />
                        </div>
                        <div className="flex space-x-2">
                          <div className="flex-1">
                            <Label>Price</Label>
                            <Input
                              type="number"
                              step="0.01"
                              value={item.price}
                              onChange={(e) => updateOrderItem(editingOrder.id, index, {
                                ...item,
                                price: parseFloat(e.target.value) || 0
                              })}
                            />
                          </div>
                          <Button
                            onClick={() => removeOrderItem(editingOrder.id, index)}
                            size="sm"
                            variant="outline"
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                      <div className="mt-2">
                        <Label>Special Instructions</Label>
                        <Textarea
                          value={item.special_instructions || ''}
                          onChange={(e) => updateOrderItem(editingOrder.id, index, {
                            ...item,
                            special_instructions: e.target.value
                          })}
                          placeholder="Any special instructions..."
                          className="text-sm"
                        />
                      </div>
                      <div className="mt-2 text-sm text-gray-600">
                        Subtotal: ₹{(item.quantity * item.price).toFixed(2)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Order Total */}
              <div className="border-t pt-4">
                <div className="flex justify-between items-center text-lg font-bold">
                  <span>Total Amount:</span>
                  <span className="text-orange-600">₹{editingOrder.total_amount?.toFixed(2) || '0.00'}</span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end space-x-2">
                <Button onClick={() => setEditingOrder(null)} variant="outline">
                  Cancel
                </Button>
                <Button onClick={saveOrderChanges} className="bg-green-600 hover:bg-green-700">
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Save Changes
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* KOT Edit Modal */}
      {editingKot && (
        <Dialog open={!!editingKot} onOpenChange={() => setEditingKot(null)}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Edit KOT {editingKot.order_number}</DialogTitle>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Order Number</Label>
                  <Input value={editingKot.order_number || ''} disabled />
                </div>
                <div>
                  <Label>Table Number</Label>
                  <Input 
                    value={editingKot.table_number || ''} 
                    onChange={(e) => setEditingKot({...editingKot, table_number: e.target.value})}
                  />
                </div>
              </div>
              
              <div>
                <Label>Status</Label>
                <Select 
                  value={editingKot.status} 
                  onValueChange={(value) => setEditingKot({...editingKot, status: value})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="cooking">Cooking</SelectItem>
                    <SelectItem value="ready">Ready</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Items</Label>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {editingKot.items?.map((item, index) => (
                    <div key={index} className="border rounded p-3 bg-gray-50">
                      <div className="flex justify-between items-center">
                        <span className="font-medium">{item.menu_item_name}</span>
                        <span className="text-sm text-gray-600">Qty: {item.quantity}</span>
                      </div>
                      {item.special_instructions && (
                        <p className="text-sm text-gray-500 mt-1">Note: {item.special_instructions}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-end space-x-2">
                <Button onClick={() => setEditingKot(null)} variant="outline">
                  Cancel
                </Button>
                <Button 
                  onClick={() => {
                    // Save KOT changes logic here
                    alert('KOT updated successfully!');
                    setEditingKot(null);
                  }} 
                  className="bg-orange-600 hover:bg-orange-700"
                >
                  Save Changes
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Bill Edit Modal */}
      {editingBill && (
        <Dialog open={!!editingBill} onOpenChange={() => setEditingBill(null)}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Edit Bill #{editingBill.id?.slice(-6)}</DialogTitle>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Customer Name</Label>
                  <Input 
                    value={editingBill.customer_name || ''} 
                    onChange={(e) => setEditingBill({...editingBill, customer_name: e.target.value})}
                  />
                </div>
                <div>
                  <Label>Table Number</Label>
                  <Input 
                    value={editingBill.table_number || ''} 
                    onChange={(e) => setEditingBill({...editingBill, table_number: e.target.value})}
                  />
                </div>
                <div>
                  <Label>Payment Method</Label>
                  <Select 
                    value={editingBill.payment_method || 'cash'} 
                    onValueChange={(value) => setEditingBill({...editingBill, payment_method: value})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="cash">Cash</SelectItem>
                      <SelectItem value="online">Online</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Total Amount</Label>
                  <Input 
                    type="number"
                    step="0.01"
                    value={editingBill.total_amount || 0} 
                    onChange={(e) => setEditingBill({...editingBill, total_amount: parseFloat(e.target.value) || 0})}
                  />
                </div>
              </div>

              <div>
                <Label>Order Items</Label>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {editingBill.items?.map((item, index) => (
                    <div key={index} className="border rounded p-3 bg-gray-50">
                      <div className="flex justify-between items-center">
                        <div>
                          <span className="font-medium">{item.menu_item_name}</span>
                          <span className="text-sm text-gray-600 ml-2">x{item.quantity}</span>
                        </div>
                        <span className="text-sm text-gray-600">₹{(item.quantity * item.price).toFixed(2)}</span>
                      </div>
                      {item.special_instructions && (
                        <p className="text-sm text-gray-500 mt-1">Note: {item.special_instructions}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-end space-x-2">
                <Button onClick={() => setEditingBill(null)} variant="outline">
                  Cancel
                </Button>
                <Button
                  onClick={async () => {
                    try {
                      await axios.put(`${API}/orders/${editingBill.id}`, {
                        paymentmethod: editingBill.paymentmethod,
                        paymentstatus: "paid",
                        customername: editingBill.customername,
                        tablenumber: editingBill.tablenumber,
                        items: editingBill.items,
                        totalamount: editingBill.totalamount,
                        status: editingBill.status,
                        paymentstatus: "paid", // or editingBill.paymentstatus
                      });
                      alert('Bill updated successfully!');
                      setEditingBill(null);
                      refreshData(); // reload updated bills/orders
                    } catch (error) {
                      alert('Failed to update bill: ' + (error.response?.data?.detail || error.message));
                    }
                  }}
                  className="bg-green-600 hover:bg-green-700"
                >
                  Save Changes
              </Button>

              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Historical Reports Modal */}
      {showHistoricalReports && (
        <Dialog open={showHistoricalReports} onOpenChange={setShowHistoricalReports}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Historical Daily Reports</DialogTitle>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <p className="text-sm text-gray-600">
                  View and access reports from previous days
                </p>
                <div className="flex gap-2">
                  <Button 
                    onClick={cleanupDuplicateReports}
                    size="sm"
                    variant="outline"
                    className="bg-yellow-50 text-yellow-700 hover:bg-yellow-100"
                  >
                    Cleanup Duplicates
                  </Button>
                  <Button 
                    onClick={resetTodayReport}
                    size="sm"
                    variant="outline"
                    className="bg-red-50 text-red-700 hover:bg-red-100"
                  >
                    Reset Today's Report
                  </Button>
                </div>
              </div>
              
              <div className="grid gap-4">
                {historicalReports.map((report) => (
                  <Card key={report.date} className="hover:shadow-md transition-shadow cursor-pointer"
                        onClick={() => {
                          setSelectedDate(report.date);
                          setShowHistoricalReports(false);
                        }}>
                    <CardContent className="p-4">
                      <div className="flex justify-between items-center">
                        <div>
                          <h3 className="font-semibold text-lg">
                            {new Date(report.date).toLocaleDateString('en-US', {
                              weekday: 'long',
                              year: 'numeric',
                              month: 'long',
                              day: 'numeric'
                            })}
                          </h3>
                          <p className="text-sm text-gray-600">
                            {report.orders} orders • {report.kots} KOTs • {report.bills} bills
                          </p>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-green-600">
                            ₹{report.revenue?.toFixed(2) || '0.00'}
                          </div>
                          <p className="text-xs text-gray-500">
                            {report.updated_at ? new Date(report.updated_at).toLocaleString() : 'No update time'}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
              
              {historicalReports.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No historical reports found</p>
                  <p className="text-sm">Reports will be created as you use the system</p>
                </div>
              )}
              
              <div className="flex justify-end">
                <Button onClick={() => setShowHistoricalReports(false)} variant="outline">
                  Close
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};
// ==================== PAYMENTS DASHBOARD COMPONENT ====================
const PaymentsDashboard = () => {
  const { 
  refreshData, 
  orders,
  paymentHistory,
  unmatchedPayments,
  paymentStats,
  showPaymentHistory,
  setShowPaymentHistory,
  loadingPayments,
  fetchPaymentHistory,
  fetchUnmatchedPayments,
  fetchPaymentStats,
  manualMatchPayment,
  triggerTestWebhook
} = useRestaurant();
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [showConfigureSoundbox, setShowConfigureSoundbox] = useState(false);
  const [soundboxStatus, setSoundboxStatus] = useState({
    connected: false,
    provider: 'Not Configured',
    last_checked: null,
    merchant_upi_id: ''
  });
  const [selectedUnmatchedPayment, setSelectedUnmatchedPayment] = useState(null);
  const [selectedOrderId, setSelectedOrderId] = useState('');

  const [showAllOrdersDialog, setShowAllOrdersDialog] = useState(false);
  const [paymentsData, setPaymentsData] = useState({
    today_online: 0,
    today_cash: 0,
    pending_orders: [],
    today_payments: [],
    unmatched_payments: []
  });
const [selectedPaymentOrder, setSelectedPaymentOrder] = useState(null);
const [showOrderDetailsDialog, setShowOrderDetailsDialog] = useState(false);
  // Helper function to format date for API (YYYY-MM-DD)
  const formatDateForAPI = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };
  // Fetch soundbox configuration status

// Fetch soundbox configuration status - FINAL FIXED VERSION
// Fetch soundbox configuration status - FIXED
// Fetch soundbox configuration status - COMPLETE FIX
const fetchSoundboxStatus = async () => {
  try {
    console.log('🔍 Fetching soundbox config from:', `http://localhost:8002/api/soundbox/config`);
    
    const response = await axios.get(`http://localhost:8002/api/soundbox/config`, {
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });
    
    console.log('📡 Response received:', response);
    console.log('📊 Response data:', response.data);
    
    // Check if config exists AND is_active is true
    if (response.data && typeof response.data === 'object' && response.data.provider) {
      const isConnected = response.data.is_active !== false; // Check is_active field
      
      console.log(`✅ Config found. is_active: ${response.data.is_active}, Connected: ${isConnected}`);
      
      setSoundboxStatus({
        connected: isConnected,
        provider: response.data.provider,
        last_ping: response.data.updated_at || response.data.created_at,
        merchant_upi_id: response.data.merchant_upi_id || ''
      });
      
      console.log(`✅ State updated: ${isConnected ? 'Connected' : 'Disconnected'}`);
    } else {
      console.log('❌ No valid config found');
      setSoundboxStatus({
        connected: false,
        provider: 'Not Configured',
        last_ping: null,
        merchant_upi_id: ''
      });
    }
  } catch (error) {
    console.error('❌ Error fetching soundbox status:', error);
    setSoundboxStatus({
      connected: false,
      provider: 'Not Configured',
      last_ping: null,
      merchant_upi_id: ''
    });
  }
};







  // Test soundbox connection
  const testSoundboxConnection = async () => {
    try {
      const response = await axios.post(`${API}/soundbox/test-connection`);
      if (response.data.connected) {
        alert('✅ Connection successful!');
        fetchSoundboxStatus();
      } else {
        alert('❌ ' + response.data.message);
      }
    } catch (error) {
      alert('❌ Connection failed: ' + error.message);
    }
  };

  // Disconnect soundbox (set to offline mode)
  // Disconnect soundbox - COMPLETE FIX
// Disconnect soundbox - SIMPLIFIED FIX
const disconnectSoundbox = async () => {
  if (!window.confirm('⚠️ Disconnect soundbox?\n\nPayment notifications will stop until you reconnect.')) {
    return;
  }

  try {
    console.log('🔌 Attempting to disconnect soundbox...');
    
    // Try DELETE first
    try {
      const response = await axios.delete(`http://localhost:8002/api/soundbox/config`);
      console.log('✅ Soundbox disconnected via DELETE:', response.data);
      
      // Update state immediately
      setSoundboxStatus({
        ...soundboxStatus,
        connected: false
      });
      
      alert('✅ Soundbox disconnected successfully!');
      
      // Refresh status after 1 second
      setTimeout(() => {
        fetchSoundboxStatus();
      }, 1000);
      
      return;
      
    } catch (deleteError) {
      console.log('DELETE failed, trying PUT...');
      
      // Fallback to PUT
      const response = await axios.put(`http://localhost:8002/api/soundbox/config`, {
        is_active: false
      });
      console.log('✅ Soundbox disconnected via PUT:', response.data);
    }
    
    // Update state immediately
    setSoundboxStatus({
      ...soundboxStatus,
      connected: false
    });
    
    alert('✅ Soundbox disconnected successfully!');
    
    // Refresh status after 1 second
    setTimeout(() => {
      fetchSoundboxStatus();
    }, 1000);
    
  } catch (error) {
    console.error('❌ Error disconnecting soundbox:', error);
    alert('❌ Error: ' + (error.response?.data?.detail || error.message));
  }
};


  // Calculate payments data whenever date or orders change

  // Calculate payments data whenever date or orders change
  useEffect(() => {
    calculatePaymentsData();
    fetchSoundboxStatus();
    fetchPaymentHistory();
    fetchUnmatchedPayments();
    fetchPaymentStats();
  }, [orders, selectedDate]);
  // Add this RIGHT AFTER the useEffect you just modified (around line 3307)

// Auto-refresh payment data every 30 seconds
  useEffect(() => {
  const interval = setInterval(() => {
    fetchPaymentHistory();
    fetchUnmatchedPayments();
    fetchPaymentStats();
    fetchSoundboxStatus();
  }, 30000); // 30 seconds

  return () => clearInterval(interval);
}, []);

  const calculatePaymentsData = async () => {
    try {
      const formattedDate = formatDateForAPI(selectedDate);
      console.log('🔍 Fetching payments for date:', formattedDate);
      
      // Fetch orders from backend
      const response = await axios.get(`http://localhost:8002/api/payments/${formattedDate}`);
      // Fetch pending orders
let pendingOrders = [];
try {
  const pendingResponse = await axios.get(`http://localhost:8002/api/payments/pending/${formattedDate}`);
  pendingOrders = Array.isArray(pendingResponse.data) ? pendingResponse.data : [];
  console.log('⏳ Pending orders from API:', pendingOrders.length);
} catch (error) {
  console.warn('⚠️ Could not fetch pending orders:', error.message);
}

      console.log('📦 Total orders from API:', response.data?.length);
      
            
      // ⭐ Calculate cash total from API response
      const cashTotal = response.data
        .filter(p => p.payment_method === 'cash')
        .reduce((sum, p) => sum + (p.final_amount || 0), 0);
      
      // ⭐ Calculate online total from API response
      const onlineTotal = response.data
        .filter(p => p.payment_method === 'online')
        .reduce((sum, p) => sum + (p.final_amount || 0), 0);
      
      console.log('💰 Cash Total:', cashTotal, '| 💳 Online Total:', onlineTotal);
      
      // ⭐ Update state with payments data (now includes order_id!)
      setPaymentsData({
        today_online: onlineTotal,
        today_cash: cashTotal,
        pending_orders: pendingOrders,
        today_payments: response.data, // This now includes order_id from backend!
        unmatched_payments: []
      });


    } catch (error) {
      console.error('❌ Error fetching payment data:', error.message);
      setPaymentsData({
        today_online: 0,
        today_cash: 0,
        pending_orders: [],
        today_payments: [],
        unmatched_payments: []
      });
    }
  };
  
  // Mark order as cash payment
  const markAsCash = async (orderId) => {
    try {
      const response = await fetch(`http://localhost:8002/api/payments/${orderId}/mark-cash`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      if (data.success) {
        alert('✅ Order marked as cash payment!');
        refreshOrders();
        calculatePaymentsData();
      } else {
        alert('❌ Failed to mark as cash');
      }
    } catch (error) {
      console.error('Error marking as cash:', error);
      alert('❌ Error: ' + error.message);
    }
  };

  // Cancel order
  const cancelOrder = async (orderId) => {
    if (!window.confirm('Are you sure you want to cancel this order?')) return;
    
    try {
      const response = await fetch(`http://localhost:8002/api/payments/${orderId}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      if (data.success) {
        alert('✅ Order cancelled successfully!');
        refreshOrders();
        calculatePaymentsData();
      } else {
        alert('❌ Failed to cancel order');
      }
    } catch (error) {
      console.error('Error cancelling order:', error);
      alert('❌ Error: ' + error.message);
    }
  };

  const getTimeSince = (createdAt) => {
    const now = new Date();
    const created = new Date(createdAt);
    const diffMs = now - created;
    const diffMins = Math.floor(diffMs / 60000);
    const diffSecs = Math.floor((diffMs % 60000) / 1000);
    return `${diffMins}m ${diffSecs}s`;
  };

    return (
    <div className="p-64 px-6 py-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">💳 Payments Dashboard</h1>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2">
            <Label htmlFor="payment-date" className="text-sm font-medium">
              Select Date:
            </Label>
            <Input
              id="payment-date"
              type="date"
              value={selectedDate.toISOString().split('T')[0]}
              onChange={(e) => {
                const dateValue = e.target.value;
                if (dateValue) {
                  const newDate = new Date(dateValue + 'T12:00:00');
                  setSelectedDate(newDate);
                  
                }
              }}
              className="w-48"
            />
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              const today = new Date();
              console.log('📅 Today button clicked:', today.toDateString()); 
              setSelectedDate(new Date());
              calculatePaymentsData();
            }}
          >
            Today
          </Button>
        </div>
      </div>


      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-green-700">💳 Online Payments</CardTitle>
            <DollarSign className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-900">₹{paymentsData.today_online.toLocaleString()}</div>
            <p className="text-xs text-green-600 mt-1">
              {paymentsData.today_payments.filter(o => o.payment_method === 'online').length} orders
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-blue-700">💵 Cash Payments</CardTitle>
            <Wallet className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-900">₹{paymentsData.today_cash.toLocaleString()}</div>
            <p className="text-xs text-blue-600 mt-1">
              {paymentsData.today_payments.filter(o => o.payment_method === 'cash').length} orders
            </p>
          </CardContent>
        </Card>

                {/* Unknown Payments Card - NEW! */}
        {paymentsData.today_unknown > 0 && (
          <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-orange-700">⚠️ Unknown Payments</CardTitle>
              <AlertTriangle className="h-4 w-4 text-orange-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-900">
                ₹{paymentsData.today_unknown?.toFixed(2) || '0.00'}
              </div>
              <p className="text-xs text-orange-600 mt-1">
                {paymentsData.unknown_orders_count || 0} orders
              </p>
              <p className="text-xs text-orange-500 mt-2">
                No payment method recorded
              </p>
            </CardContent>
          </Card>
        )}


        <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-yellow-700">⏳ Pending Payments</CardTitle>
            <Clock className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-900">{paymentsData.pending_orders.length}</div>
            <p className="text-xs text-yellow-600 mt-1">orders awaiting payment</p>
          </CardContent>
        </Card>
      </div>

        
        {/* Soundbox Status Card - FIXED */}
        <Card className="border-2 border-purple-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Volume2 className="h-5 w-5 text-purple-600" />
              Soundbox Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-800">
                  {soundboxStatus?.connected && soundboxStatus?.provider && soundboxStatus.provider !== 'Not Configured'
                    ? `${soundboxStatus.provider.charAt(0).toUpperCase() + soundboxStatus.provider.slice(1)} Soundbox`
                    : 'Paytm Soundbox (Not Configured)'}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {soundboxStatus?.connected
                    ? `Last ping: ${soundboxStatus.last_ping 
                        ? new Date(soundboxStatus.last_ping).toLocaleString('en-IN', {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })
                        : 'Just now'}`
                    : 'Configure soundbox API to enable automatic payment detection'}
                </p>
                {soundboxStatus?.connected && soundboxStatus?.merchant_upi_id && (
                  <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                    <span>UPI:</span>
                    <span className="font-mono bg-gray-100 px-2 py-0.5 rounded text-xs">
                      {soundboxStatus.merchant_upi_id}
                    </span>
                  </p>
                )}
              </div>
              <Badge
                variant="secondary"
                className={soundboxStatus?.connected 
                  ? 'bg-green-100 text-green-700 border-green-200' 
                  : 'bg-gray-200 text-gray-600 border-gray-300'}
              >
                {soundboxStatus?.connected ? (
                  <span className="flex items-center gap-1.5">
                    <span className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></span>
                    Live Connected
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5">
                    <span className="h-2 w-2 bg-gray-400 rounded-full"></span>
                    Offline
                  </span>
                )}
              </Badge>
            </div>

            <div className="mt-4 flex gap-2 flex-wrap">
              {soundboxStatus?.connected ? (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowConfigureSoundbox(true)}
                    className="flex items-center gap-2"
                  >
                    <Settings className="h-4 w-4" />
                    Edit Configuration
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={testSoundboxConnection}
                    className="flex items-center gap-2"
                  >
                    <RefreshCw className="h-4 w-4" />
                    Test Connection
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={disconnectSoundbox}
                    className="flex items-center gap-2"
                  >
                    <XCircle className="h-4 w-4" />
                    Disconnect
                  </Button>
                </>
              ) : (
                <Button
                  variant="default"
                  size="sm"
                  onClick={() => setShowConfigureSoundbox(true)}
                  className="flex items-center gap-2 bg-orange-600 hover:bg-orange-700"
                >
                  <Settings className="h-4 w-4" />
                  Configure Soundbox
                </Button>
              )}
            </div>
          </CardContent>
        </Card>





      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            ⏳ Pending Payments ({paymentsData.pending_orders.length})
            <Badge variant="secondary" className="ml-2">🔄 Auto-refresh 5s</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {paymentsData.pending_orders.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Clock className="h-12 w-12 mx-auto mb-2 text-gray-300" />
              <p>No pending payments</p>
              <p className="text-sm">All orders are paid ✅</p>
            </div>
          ) : (
            paymentsData.pending_orders.map(order => (
              <Card key={order.order_id} className="border-2 border-yellow-200 bg-yellow-50">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="font-semibold text-lg">Order #{order.order_id}</span>
                        <Badge variant="outline" className="bg-white">
                          {order.table ? `Table ${order.table}` : 'N/A'}
                        </Badge>
                        <Badge variant="outline" className="bg-white">
                          ₹{order.amount}
                        </Badge>
                        <Badge className="bg-yellow-500">
                          ⏱️ {getTimeSince(order.created_at)}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600">
                        Customer: {order.customer || 'Walk-in'} | {order.items?.length || 0} items
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => markAsCash(order.order_id)}
                      >
                        Mark as Cash
                      </Button>
                      <Button 
                        size="sm" 
                        variant="destructive"
                        onClick={() => cancelOrder(order.order_id)}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-3">
                    💡 Customer should scan QR on soundbox counter to pay
                  </p>
                </CardContent>
              </Card>
            ))
          )}
        </CardContent>
      </Card>
{/* ============= MATCH PAYMENT DIALOG ============= */}
{selectedUnmatchedPayment && (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <Card className="w-full max-w-md mx-4">
      <CardHeader>
        <CardTitle>Match Payment to Order</CardTitle>
        <p className="text-sm text-gray-500">
          Payment Amount: ₹{selectedUnmatchedPayment.amount.toFixed(2)}
        </p>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <Label>Select Pending Order</Label>
            <Select value={selectedOrderId} onValueChange={setSelectedOrderId}>
              <SelectTrigger>
                <SelectValue placeholder="Choose an order..." />
              </SelectTrigger>
              <SelectContent>
                  {paymentsData?.pending_orders?.length > 0 ? (
                    paymentsData.pending_orders.map((order) => {
                      const fullOrderId = order.order_id || order.id || '';
                      const shortOrderId = fullOrderId.slice(0, 8);
                      const orderAmount = order.final_amount || order.total_amount || 0;
                      
                      return (
                        <SelectItem key={fullOrderId} value={fullOrderId}>
                          Order #{shortOrderId} - ₹{orderAmount.toFixed(2)}
                        </SelectItem>
                      );
                    })
                  ) : (
                    <SelectItem value="no-orders" disabled>
                      No pending orders for today
                    </SelectItem>
                  )}
                </SelectContent>

            </Select>
          </div>
          
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setSelectedUnmatchedPayment(null);
                setSelectedOrderId('');
              }}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={() => {
                if (selectedOrderId) {
                  manualMatchPayment(
                    selectedUnmatchedPayment.transaction_id,
                    selectedOrderId
                  );
                  setSelectedUnmatchedPayment(null);
                  setSelectedOrderId('');
                }
              }}
              className="flex-1"
              disabled={!selectedOrderId}
            >
              Match
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
)}



{/* ============= PAYMENT STATISTICS CARDS ============= */}
<div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
  <Card>
    <CardContent className="pt-6">
      <div className="text-sm text-gray-500">Total Payments Today</div>
      <div className="text-3xl font-bold text-blue-600">
        {paymentStats.total_payments}
      </div>
    </CardContent>
  </Card>
  
  <Card>
    <CardContent className="pt-6">
      <div className="text-sm text-gray-500">Matched Payments</div>
      <div className="text-3xl font-bold text-green-600">
        {paymentStats.matched_payments}
      </div>
    </CardContent>
  </Card>
  
  <Card>
    <CardContent className="pt-6">
      <div className="text-sm text-gray-500">Unmatched Payments</div>
      <div className="text-3xl font-bold text-orange-600">
        {paymentStats.unmatched_payments}
      </div>
    </CardContent>
  </Card>
  
  <Card>
    <CardContent className="pt-6">
      <div className="text-sm text-gray-500">Total Amount</div>
      <div className="text-3xl font-bold text-purple-600">
        ₹{paymentStats.total_amount.toFixed(2)}
      </div>
    </CardContent>
  </Card>
</div>

{/* ============= UNMATCHED PAYMENTS ALERT ============= */}
{unmatchedPayments.length > 0 && (
  <Card className="mb-6 border-orange-500 bg-orange-50">
    <CardHeader>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-orange-600" />
          <CardTitle className="text-orange-800">
            {unmatchedPayments.length} Unmatched Payment{unmatchedPayments.length > 1 ? 's' : ''}
          </CardTitle>
        </div>
        <Button variant="outline" size="sm" onClick={fetchUnmatchedPayments}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>
    </CardHeader>
    <CardContent>
      <div className="space-y-2">
        {unmatchedPayments.slice(0, 3).map((payment) => (
          <div 
            key={payment.id} 
            className="flex items-center justify-between p-3 bg-white rounded border border-orange-200"
          >
            <div className="flex-1">
              <div className="font-semibold text-gray-800">
                ₹{payment.amount.toFixed(2)}
              </div>
              <div className="text-sm text-gray-500">
                {payment.transaction_id} • {payment.upi_id}
              </div>
              <div className="text-xs text-gray-400">
                {new Date(payment.timestamp).toLocaleString()}
              </div>
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setSelectedUnmatchedPayment(payment)}
            >
              Match to Order
            </Button>

          </div>
        ))}
      </div>
    </CardContent>
  </Card>
)}

{/* ============= PAYMENT HISTORY TABLE ============= */}
<Card className="mb-6">
  <CardHeader>
    <div className="flex items-center justify-between">
      <CardTitle className="flex items-center gap-2">
        <History className="h-5 w-5" />
        Payment History
      </CardTitle>
      <div className="flex gap-2">
        <Button 
          variant="outline" 
          size="sm"
          onClick={triggerTestWebhook}
        >
          <Zap className="h-4 w-4 mr-2" />
          Test Webhook
        </Button>
        <Button 
          variant="outline" 
          size="sm"
          onClick={() => {
            fetchPaymentHistory();
            fetchUnmatchedPayments();
            fetchPaymentStats();
          }}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowPaymentHistory(!showPaymentHistory)}
        >
          {showPaymentHistory ? 'Hide' : 'Show'} All
        </Button>
      </div>
    </div>
  </CardHeader>
  
  {showPaymentHistory && (
    <CardContent>
      {loadingPayments ? (
        <div className="text-center py-8 text-gray-500">
          Loading payment history...
        </div>
      ) : paymentHistory.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No payment history found
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Time
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Transaction ID
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Amount
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  UPI ID
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Order ID
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {paymentHistory.map((payment) => (
                <tr key={payment.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {new Date(payment.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="px-4 py-3 text-sm font-mono text-gray-800">
                    {payment.transaction_id}
                  </td>
                  <td className="px-4 py-3 text-sm font-semibold text-gray-900">
                    ₹{payment.amount.toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {payment.upi_id}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {payment.order_id || '-'}
                  </td>
                  <td className="px-4 py-3">
                    {payment.matched ? (
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                        ✓ Matched
                      </span>
                    ) : (
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-orange-100 text-orange-800">
                        ⚠ Unmatched
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </CardContent>
  )}
</Card>


<Card>
  <CardHeader className="flex flex-row items-center justify-between">
      <CardTitle>💰 Recent Payment Activity</CardTitle>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setShowAllOrdersDialog(true)}
      >
        <Eye className="h-4 w-4 mr-2" />
        View All Orders ({paymentsData.today_payments.length})
      </Button>    
  </CardHeader>
  <CardContent>
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Order ID</TableHead>
          <TableHead>Time</TableHead>
          <TableHead>Amount</TableHead>
          <TableHead>Method</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {paymentsData.today_payments.length === 0 ? (
          <TableRow>
            <TableCell colSpan={6} className="text-center py-8 text-gray-500">
              No payment activity today
            </TableCell>
          </TableRow>
        ) : (
          paymentsData.today_payments.slice(0, 10).map((payment) => (
            <TableRow key={payment._id}>
              <TableCell className="font-medium">
                {payment.order_id || payment._id?.slice(-8).toUpperCase() || 'N/A'}
              </TableCell>
              <TableCell>
                {new Date(payment.created_at).toLocaleTimeString('en-US', {
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </TableCell>
              <TableCell className="text-right font-semibold">
                ₹{(payment.final_amount || 0).toFixed(2)}
              </TableCell>
              <TableCell className="text-center">
                <Badge 
                  className={payment.payment_method === 'online' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}
                >
                  {payment.payment_method === 'online' ? '💳 Online' : '💵 Cash'}
                </Badge>
              </TableCell>
              <TableCell className="text-center">
                <Badge className="bg-green-100 text-green-700">✓ Paid</Badge>
              </TableCell>
              <TableCell>
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => {
                    setSelectedPaymentOrder(payment);
                    setShowOrderDetailsDialog(true);
                  }}
                >
                  <Eye className="h-4 w-4 mr-1" />
                  View
                </Button>
              </TableCell>
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  </CardContent>
</Card>

{/* Order Details Dialog - Add this after the Recent Payment Activity Card */}
<Dialog open={showOrderDetailsDialog} onOpenChange={setShowOrderDetailsDialog}>
  <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
    <DialogHeader>
      <DialogTitle>Order Details - {selectedPaymentOrder?.order_id || selectedPaymentOrder?._id?.slice(-8) || 'N/A'}</DialogTitle>
    </DialogHeader>
    
    {selectedPaymentOrder && (
      <div className="space-y-4">
        {/* Order Information */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label className="text-sm text-gray-600">Customer</Label>
            <p className="font-semibold">{selectedPaymentOrder.customer_name || 'Walk-in'}</p>
          </div>
          <div>
            <Label className="text-sm text-gray-600">Table</Label>
            <p className="font-semibold">
              {selectedPaymentOrder.table_number ? `Table ${selectedPaymentOrder.table_number}` : 'N/A'}
            </p>
          </div>
          <div>
            <Label className="text-sm text-gray-600">Payment Method</Label>
            <Badge className={selectedPaymentOrder.payment_method === 'online' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}>
              {selectedPaymentOrder.payment_method === 'online' ? '💳 Online' : '💵 Cash'}
            </Badge>
          </div>
          <div>
            <Label className="text-sm text-gray-600">Order Time</Label>
            <p className="font-semibold">
              {new Date(selectedPaymentOrder.created_at).toLocaleString('en-US', {
                dateStyle: 'short',
                timeStyle: 'short'
              })}
            </p>
          </div>
        </div>

        {/* Order Items */}
        <div>
          <Label className="text-sm text-gray-600 mb-2 block">Order Items</Label>
          <div className="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Item</TableHead>
                  <TableHead className="text-center">Qty</TableHead>
                  <TableHead className="text-right">Price</TableHead>
                  <TableHead className="text-right">Total</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {selectedPaymentOrder.items && selectedPaymentOrder.items.length > 0 ? (
                  selectedPaymentOrder.items.map((item, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{item.menu_item_name || item.menuitem_name || item.menuitemname || item.name || "Unknown Item"}</p>
                          {item.special_instructions && (
                            <p className="text-xs text-gray-500 italic">
                              Note: {item.special_instructions}
                            </p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-center">{item.quantity}</TableCell>
                      <TableCell className="text-right">₹{(item.price || 0).toFixed(2)}</TableCell>
                      <TableCell className="text-right font-semibold">
                        ₹{((item.quantity || 0) * (item.price || 0)).toFixed(2)}
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center text-gray-500">
                      No items found
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </div>

        {/* Total */}
        <div className="border-t pt-4">
          <div className="flex justify-between items-center text-lg font-bold">
            <span>Total Amount:</span>
            <span className="text-green-600">
              ₹{(selectedPaymentOrder.final_amount || selectedPaymentOrder.finalamount || selectedPaymentOrder.totalamount || selectedPaymentOrder.total_amount || 0).toFixed(2)}
            </span>
          </div>
        </div>

        {/* Close Button */}
        <div className="flex justify-end">
          <Button onClick={() => setShowOrderDetailsDialog(false)}>
            Close
          </Button>
        </div>
      </div>
    )}
  </DialogContent>
</Dialog>
{/* View All Orders Dialog */}
<Dialog open={showAllOrdersDialog} onOpenChange={setShowAllOrdersDialog}>
  <DialogContent className="max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
    <DialogHeader>
      <DialogTitle>
        All Payment Orders - {selectedDate.toLocaleDateString('en-US', { dateStyle: 'medium' })}
        <span className="ml-2 text-sm text-gray-500">
          ({paymentsData.today_payments.length} orders)
        </span>
      </DialogTitle>
    </DialogHeader>
    
    <div className="flex-1 overflow-y-auto">
      <Table>
        <TableHeader className="sticky top-0 bg-white z-10">
          <TableRow>
            <TableHead>Order ID</TableHead>
            <TableHead>Customer</TableHead>
            <TableHead>Table</TableHead>
            <TableHead>Time</TableHead>
            <TableHead className="text-right">Amount</TableHead>
            <TableHead className="text-center">Method</TableHead>
            <TableHead className="text-center">Status</TableHead>
            <TableHead className="text-center">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {paymentsData.today_payments.length === 0 ? (
            <TableRow>
              <TableCell colSpan={8} className="text-center py-8 text-gray-500">
                No payment activity for this date
              </TableCell>
            </TableRow>
          ) : (
            paymentsData.today_payments.map((payment) => (
              <TableRow key={payment._id} className="hover:bg-gray-50">
                <TableCell className="font-medium">
                  {payment.order_id || payment._id?.slice(-8).toUpperCase() || 'N/A'}
                </TableCell>
                <TableCell>
                  {payment.customer_name || 'Walk-in'}
                </TableCell>
                <TableCell>
                  {payment.table_number ? `Table ${payment.table_number}` : 'N/A'}
                </TableCell>
                <TableCell>
                  {new Date(payment.created_at).toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </TableCell>
                <TableCell className="text-right font-semibold">
                  ₹{(payment.final_amount || 0).toFixed(2)}
                </TableCell>
                <TableCell className="text-center">
                  <Badge 
                    className={payment.payment_method === 'online' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}
                  >
                    {payment.payment_method === 'online' ? '💳 Online' : '💵 Cash'}
                  </Badge>
                </TableCell>
                <TableCell className="text-center">
                  <Badge className="bg-green-100 text-green-700">✓ Paid</Badge>
                </TableCell>
                <TableCell className="text-center">
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => {
                      setSelectedPaymentOrder(payment);
                      setShowAllOrdersDialog(false);
                      setShowOrderDetailsDialog(true);
                    }}
                  >
                    <Eye className="h-4 w-4 mr-1" />
                    View
                  </Button>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>

    <div className="border-t pt-4 mt-4 flex justify-between items-center">
      <div className="text-sm text-gray-600">
        <strong>Total:</strong> ₹{paymentsData.today_payments.reduce((sum, p) => sum + (p.total_amount || 0), 0).toFixed(2)}
        <span className="ml-4">
          <strong>Cash:</strong> ₹{paymentsData.today_cash.toFixed(2)}
        </span>
        <span className="ml-4">
          <strong>Online:</strong> ₹{paymentsData.today_online.toFixed(2)}
        </span>
      </div>
      <Button onClick={() => setShowAllOrdersDialog(false)}>
        Close
      </Button>
    </div>
  </DialogContent>
</Dialog>

            {/* Quick Actions Panel - ADD THIS NEW SECTION */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🔧 Quick Actions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* View Static QR Code */}
            <Button 
              variant="outline" 
              className="flex flex-col items-center gap-2 h-auto py-4"
              onClick={() => alert('QR Code feature coming soon!')}
            >
              <FileText className="h-6 w-6 text-blue-600" />
              <span className="text-sm">View Static QR Code</span>
            </Button>

            {/* Print QR Sticker */}
            <Button 
              variant="outline" 
              className="flex flex-col items-center gap-2 h-auto py-4"
              onClick={() => alert('Print QR feature coming soon!')}
            >
              <Printer className="h-6 w-6 text-green-600" />
              <span className="text-sm">Print QR Sticker</span>
            </Button>

            {/* Record Cash Payment */}
            <Button 
              variant="outline" 
              className="flex flex-col items-center gap-2 h-auto py-4"
              onClick={() => alert('Record Cash Payment feature coming soon!')}
            >
              <Wallet className="h-6 w-6 text-orange-600" />
              <span className="text-sm">Record Cash Payment</span>
            </Button>

            {/* Bank Reconciliation */}
            <Button 
              variant="outline" 
              className="flex flex-col items-center gap-2 h-auto py-4"
              onClick={() => alert('Bank Reconciliation feature coming soon!')}
            >
              <RefreshCw className="h-6 w-6 text-purple-600" />
              <span className="text-sm">Bank Reconciliation</span>
            </Button>

            {/* Payment Settings */}
            <Button 
              variant="outline" 
              className="flex flex-col items-center gap-2 h-auto py-4"
              onClick={() => alert('Payment Settings feature coming soon!')}
            >
              <Settings className="h-6 w-6 text-gray-600" />
              <span className="text-sm">Payment Settings</span>
            </Button>

            {/* Export Report */}
            <Button 
              variant="outline" 
              className="flex flex-col items-center gap-2 h-auto py-4"
              onClick={() => alert('Export Report feature coming soon!')}
            >
              <Download className="h-6 w-6 text-indigo-600" />
              <span className="text-sm">Export Report</span>
            </Button>
          </div>
        </CardContent>
      </Card>
        {/* ========== ADD MODAL HERE ========== */}
        {/* Configure Soundbox Modal */}
        <ConfigureSoundboxModal
          isOpen={showConfigureSoundbox}
          onClose={() => setShowConfigureSoundbox(false)}
          onSave={() => {
            fetchSoundboxStatus();
            calculatePaymentsData();
          }}
        />
        {/* ========== END OF NEW CODE ========== */}      
    </div>
  );
};


// Main App Component
function App() {
  return (
    <RestaurantProvider>
      <div className="min-h-screen bg-gray-50">
        <BrowserRouter>
          <Navigation />
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/orders" element={<Orders />} />
            <Route path="/new-order" element={<NewOrder />} />
            <Route path="/kot" element={<KOTScreen />} />
            <Route path="/menu" element={<MenuManagement />} />
            <Route path="/daily-report" element={<DailyReport />} />
            <Route path="/payments" element={<PaymentsDashboard />} />
          </Routes>
        </BrowserRouter>
      </div>
    </RestaurantProvider>
  );
}

export default App;
