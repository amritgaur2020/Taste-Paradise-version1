import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X, User, Phone, Mail, ShoppingBag, DollarSign, Calendar, Eye } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import './ViewCustomerModal.css';

const API_BASE_URL = 'http://localhost:8002';

const ViewCustomerModal = ({ customer, onClose }) => {
  const [customerData, setCustomerData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCustomerDetails();
  }, [customer]);

  const fetchCustomerDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(
        `${API_BASE_URL}/api/customers/${customer.customer_id}/history`
      );
      setCustomerData(response.data);
    } catch (err) {
      console.error('Error fetching customer details:', err);
      setError(err.message || 'Failed to load customer details');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <p>Loading customer details...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
        <div className="sticky top-0 bg-white border-b-2 border-orange-600 p-6 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-800">Customer Details</h2>
          <button onClick={onClose} className="text-gray-600 hover:text-gray-800">
            <X size={24} />
          </button>
        </div>

        {error && (
          <div className="m-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        {customerData && (
          <div className="p-6 space-y-6">
            {/* Customer Info */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center space-x-3">
                <User className="text-orange-600" size={20} />
                <div>
                  <p className="text-sm text-gray-600">Name</p>
                  <p className="font-semibold text-gray-800">{customerData.customer.name}</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Phone className="text-orange-600" size={20} />
                <div>
                  <p className="text-sm text-gray-600">Phone</p>
                  <p className="font-semibold text-gray-800">{customerData.customer.phone}</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Mail className="text-orange-600" size={20} />
                <div>
                  <p className="text-sm text-gray-600">Email</p>
                  <p className="font-semibold text-gray-800">{customerData.customer.email}</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <ShoppingBag className="text-orange-600" size={20} />
                <div>
                  <p className="text-sm text-gray-600">Total Orders</p>
                  <p className="font-semibold text-gray-800">{customerData.statistics.total_orders}</p>
                </div>
              </div>
            </div>

            {/* Statistics */}
            <div className="grid grid-cols-2 gap-4 bg-orange-50 p-4 rounded-lg">
              <div>
                <p className="text-sm text-gray-600">Total Spent</p>
                <p className="text-2xl font-bold text-orange-600">₹{customerData.statistics.total_spent.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Avg Order Value</p>
                <p className="text-2xl font-bold text-orange-600">₹{customerData.statistics.average_order_value.toFixed(2)}</p>
              </div>
            </div>

            {/* Recent Orders */}
            <div>
              <h3 className="font-bold text-gray-800 mb-3 flex items-center">
                <Calendar className="mr-2 text-orange-600" size={18} />
                Recent Orders
              </h3>
              {customerData.recent_orders.length > 0 ? (
                <div className="space-y-2">
                  {customerData.recent_orders.map((order) => (
                    <div key={order.order_id} className="border border-gray-200 p-3 rounded-lg">
                      <div className="flex justify-between items-center">
                        <div>
                          <p className="font-semibold text-gray-800">Order #{order.order_id}</p>
                          <p className="text-sm text-gray-600">{new Date(order.created_at).toLocaleDateString()}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-orange-600">₹{order.final_amount}</p>
                          <Badge className={order.status === 'served' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}>
                            {order.status}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600">No recent orders</p>
              )}
            </div>
          </div>
        )}

        <div className="border-t p-6 flex justify-end">
          <Button onClick={onClose} className="bg-orange-600 hover:bg-orange-700 text-white">
            Close
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ViewCustomerModal;
