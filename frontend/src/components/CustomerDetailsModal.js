import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X, User, Phone, Mail, ShoppingBag, DollarSign, Calendar } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';

const API_BASE_URL = 'http://localhost:8002';

const CustomerDetailsModal = ({ customer, onClose }) => {
  const [customerData, setCustomerData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCustomerHistory();
  }, [customer]);

  const fetchCustomerHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('Fetching history for:', customer);
      
      const response = await axios.get(
         `${API_BASE_URL}/api/customers/${customer.customer_id}/history`// Use the actual customer_id value// Use the actual customer_id value// Use the actual customer_id value// Use the actual customer_id value// Use the actual customer_id value// Use the actual customer_id value// Use the actual customer_id value
      );
      
      console.log('API Response:', response.data);
      setCustomerData(response.data);
    } catch (error) {
      console.error('Error fetching customer history:', error);
      setError(error.message || 'Failed to load customer details');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-2xl w-full mx-4">
          <p className="text-center text-gray-600">Loading customer details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-2xl w-full mx-4">
          <p className="text-center text-red-600">Error: {error}</p>
          <button onClick={onClose} className="mt-4 w-full bg-orange-600 text-white py-2 rounded">
            Close
          </button>
        </div>
      </div>
    );
  }

  const { customer: customerInfo, statistics, recent_orders } = customerData || {};

  // ✅ Get customer info from either the API response or the passed customer prop
  const displayCustomer = customerInfo || customer;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Customer Details</h2>
            <p className="text-sm text-gray-500">{displayCustomer?.customer_id}</p>
          </div>
          <button 
            onClick={onClose} 
            className="text-gray-400 hover:text-gray-600 transition"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Customer Info Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-lg">
            <User className="h-5 w-5 text-blue-600" />
            <div>
              <p className="text-sm text-gray-600">Name</p>
              <p className="font-semibold text-gray-800">{displayCustomer?.name || 'N/A'}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-4 bg-green-50 rounded-lg">
            <Phone className="h-5 w-5 text-green-600" />
            <div>
              <p className="text-sm text-gray-600">Phone</p>
              <p className="font-semibold text-gray-800">{displayCustomer?.phone || 'N/A'}</p>
            </div>
          </div>

          {displayCustomer?.email && (
            <div className="flex items-center gap-3 p-4 bg-purple-50 rounded-lg">
              <Mail className="h-5 w-5 text-purple-600" />
              <div>
                <p className="text-sm text-gray-600">Email</p>
                <p className="font-semibold text-gray-800">{displayCustomer?.email}</p>
              </div>
            </div>
          )}
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white p-4 rounded-lg">
            <ShoppingBag className="h-8 w-8 mb-2" />
            <p className="text-sm opacity-90">Total Orders</p>
            <p className="text-3xl font-bold">
              {statistics?.total_orders || 0}
            </p>
          </div>

          <div className="bg-gradient-to-br from-green-500 to-green-600 text-white p-4 rounded-lg">
            <DollarSign className="h-8 w-8 mb-2" />
            <p className="text-sm opacity-90">Total Spent</p>
            <p className="text-3xl font-bold">
              ₹{(statistics?.total_spent || 0).toLocaleString('en-IN')}
            </p>
          </div>

          <div className="bg-gradient-to-br from-purple-500 to-purple-600 text-white p-4 rounded-lg">
            <Calendar className="h-8 w-8 mb-2" />
            <p className="text-sm opacity-90">Avg Order</p>
            <p className="text-3xl font-bold">
              ₹{(statistics?.average_order_value || 0).toLocaleString('en-IN')}
            </p>
          </div>
        </div>

        {/* Recent Orders */}
        <div>
          <h3 className="text-lg font-semibold mb-4 text-gray-900">Recent Orders</h3>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {recent_orders && recent_orders.length > 0 ? (
              recent_orders.map((order) => (
                <div
                  key={order.order_id || order._id}
                  className="border rounded-lg p-4 hover:bg-gray-50 transition"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-gray-900">{order.order_id}</p>
                      <p className="text-sm text-gray-500">
                        {order.created_at 
                          ? new Date(order.created_at).toLocaleDateString('en-IN') 
                          : 'N/A'}
                        {' at '}
                        {order.created_at
                          ? new Date(order.created_at).toLocaleTimeString('en-IN', {
                              hour: '2-digit',
                              minute: '2-digit'
                            })
                          : ''}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-green-600">
                        ₹{(order.final_amount || order.total_amount || 0).toFixed(2)}
                      </p>
                      <Badge variant={order.status === 'served' ? 'default' : 'secondary'}>
                        {order.status || 'pending'}
                      </Badge>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-center py-8 bg-gray-50 rounded-lg">
                No orders found
              </p>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 flex justify-end gap-3">
          <Button 
            onClick={onClose} 
            className="bg-orange-600 hover:bg-orange-700 text-white"
          >
            Close
          </Button>
        </div>
      </div>
    </div>
  );
};

export default CustomerDetailsModal;
