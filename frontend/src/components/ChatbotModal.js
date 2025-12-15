import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { X, Send, ShoppingCart, CheckCircle, ChevronDown } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card } from './ui/card';
import './ChatbotModal.css';

const BACKEND_URL = window.APIBASEURL || 'http://127.0.0.1:8002';

const ChatbotModal = ({ isOpen, onClose, tableNumber, onOrderComplete }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [sessionId] = useState(() => `session-${Date.now()}`);
  const [isLoading, setIsLoading] = useState(false);
  const [orderSummary, setOrderSummary] = useState(null);
  const [currentOrderId, setCurrentOrderId] = useState(null);
  const [orderStage, setOrderStage] = useState('ordering');
  const [categories, setCategories] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [expandedMessages, setExpandedMessages] = useState(new Set());
  const [isCreatingOrder, setIsCreatingOrder] = useState(false);
  const messagesEndRef = useRef(null);
  const hasInitialized = useRef(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && !hasInitialized.current) {
      hasInitialized.current = true;
      setMessages([{
        type: 'bot',
        text: `Hi! 👋 I'm your order assistant. ${tableNumber ? `Table ${tableNumber} - ` : ''}What would you like to order today?`,
        timestamp: new Date(),
        id: Date.now()
      }]);
      setOrderSummary(null);
      setCurrentOrderId(null);
      setOrderStage('ordering');
      setIsCreatingOrder(false);
      loadCategories();
    }
    
    if (!isOpen) {
      hasInitialized.current = false;
      setMessages([]);
      setOrderSummary(null);
      setCurrentOrderId(null);
      setOrderStage('ordering');
      setIsCreatingOrder(false);
    }
  }, [isOpen, tableNumber]);

  const loadCategories = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/menuitems`);
      const uniqueCategories = [...new Set(response.data.map(item => item.category))];
      setCategories(uniqueCategories.slice(0, 8));
    } catch (error) {
      console.error('Error loading categories:', error);
      setCategories(['Desserts', 'Vegetarian', 'Chicken', 'Beverages']);
    }
  };

  const handleInputChange = async (e) => {
    const value = e.target.value;
    setInputMessage(value);
    
    if (value.length > 2) {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/menuitems`);
        const allCategories = [...new Set(response.data.map(i => i.category))];
        const matches = allCategories.filter(c => 
          c.toLowerCase().includes(value.toLowerCase())
        );
        setSuggestions(matches.slice(0, 5));
      } catch (error) {
        setSuggestions([]);
      }
    } else {
      setSuggestions([]);
    }
  };

  const sendMessage = async (text = inputMessage) => {
    if (!text.trim() || isLoading) return;

    const messageId = Date.now();
    const userMessage = {
      type: 'user',
      text: text,
      timestamp: new Date(),
      id: messageId
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setSuggestions([]);
    setIsLoading(true);

    try {
      const response = await axios.post(`${BACKEND_URL}/api/ai-chat`, {
        message: text,
        table_number: tableNumber || 0
      });

      const botMessage = {
        type: 'bot',
        text: response.data.response,
        timestamp: new Date(),
        menuItems: response.data.menu_items || [],
        orderItems: response.data.order_items || [],
        intent: response.data.intent || 'search',
        id: Date.now() + 1
      };

      setMessages(prev => [...prev, botMessage]);

      if (response.data.order_items && response.data.order_items.length > 0) {
        const items = response.data.order_items;
        const subtotal = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        const tax = Math.round(subtotal * 0.05 * 100) / 100;
        const total = Math.round((subtotal + tax) * 100) / 100;
        
        setOrderSummary({
          items: items.map(item => ({
            id: item.id,
            name: item.name,
            quantity: parseInt(item.quantity),
            price: parseFloat(item.price)
          })),
          subtotal: subtotal,
          tax: tax,
          total: total
        });
        
        setOrderStage('ordering');
      }

    } catch (error) {
      console.error('AI chat error:', error);
      setMessages(prev => [...prev, {
        type: 'bot',
        text: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
        id: Date.now() + 2
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmOrder = async () => {
    if (!orderSummary || !orderSummary.items || orderSummary.items.length === 0) {
      alert('No items in order');
      return;
    }

    if (currentOrderId) {
      console.log('✅ Order already exists:', currentOrderId);
      setOrderStage('payment');
      return;
    }

    if (isCreatingOrder) {
      console.log('⏳ Order creation already in progress...');
      return;
    }

    setIsLoading(true);
    setIsCreatingOrder(true);
    
    try {
      const orderData = {
        order_type: "dine-in",
        table_number: String(tableNumber || 0),
        customer_name: "AI Order",
        items: orderSummary.items.map(item => ({
          menu_item_id: item.id,
          name: String(item.name),
          price: parseFloat(item.price),
          quantity: parseInt(item.quantity)
        })),
        subtotal: parseFloat(orderSummary.subtotal.toFixed(2)),
        tax: parseFloat(orderSummary.tax.toFixed(2)),
        total_amount: parseFloat(orderSummary.total.toFixed(2)),
        payment_status: "pending",
        payment_method: null,
        status: "pending",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      console.log('📤 Creating order (ONCE):', JSON.stringify(orderData, null, 2));

      const response = await axios.post(`${BACKEND_URL}/api/orders`, orderData);
      
      console.log('✅ Order created successfully:', response.data);
      
      const orderId = response.data._id || response.data.id || response.data.order_id;
      
      if (!orderId) {
        console.error('❌ No order ID in response:', response.data);
        throw new Error('Order created but no ID returned');
      }
      
      setCurrentOrderId(orderId);
      
      const orderIdShort = orderId && orderId.length >= 8 ? orderId.slice(0, 8) : orderId;
      
      setMessages(prev => [...prev, {
        type: 'bot',
        text: `✅ **Order Confirmed!** (Order #${orderIdShort})\n\n💳 Please select payment method:`,
        timestamp: new Date(),
        id: Date.now()
      }]);

      setOrderStage('payment');

    } catch (error) {
      console.error('❌ Order creation error:', error);
      console.error('❌ Full error:', error.response);
      
      setIsCreatingOrder(false);
      
      let errorMsg = 'Unknown error';
      
      if (error.response?.data) {
        if (error.response.data.detail) {
          if (Array.isArray(error.response.data.detail)) {
            errorMsg = error.response.data.detail.map(err => 
              `Field: ${err.loc.join('.')} - ${err.msg}`
            ).join('\n');
          } else {
            errorMsg = JSON.stringify(error.response.data.detail);
          }
        } else {
          errorMsg = JSON.stringify(error.response.data);
        }
      } else if (error.message) {
        errorMsg = error.message;
      }
      
      console.error('📋 Error details:', errorMsg);
      alert(`Failed to create order:\n\n${errorMsg}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePayment = async (paymentMethod) => {
    if (!currentOrderId) {
      alert('No order ID found. Please create order first.');
      return;
    }

    setIsLoading(true);
    try {
      console.log(`💳 Processing ${paymentMethod} payment for order:`, currentOrderId);
      
      const response = await axios.patch(
        `${BACKEND_URL}/api/orders/${currentOrderId}`, 
        {
          payment_status: 'paid',
          payment_method: paymentMethod,
          status: 'confirmed'
        }
      );

      console.log('✅ Payment successful:', response.data);

      try {
        await axios.get(`${BACKEND_URL}/api/orders/${currentOrderId}/bill`);
        console.log('📄 Bill generated');
      } catch (billError) {
        console.error('⚠️ Bill print error:', billError);
      }

      setMessages(prev => [...prev, {
        type: 'bot',
        text: `✅ **Payment Successful!**\n\n💳 ${paymentMethod.toUpperCase()}\n💵 ₹${orderSummary?.total ? orderSummary.total.toFixed(2) : '0.00'}\n\n📄 Bill sent to kitchen!\n🎉 Thank you!`,
        timestamp: new Date(),
        id: Date.now()
      }]);

      setOrderStage('completed');

      setTimeout(() => {
        if (onOrderComplete) {
          onOrderComplete(currentOrderId, response.data);
        }
        onClose();
      }, 2000);

    } catch (error) {
      console.error('❌ Payment error:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      alert(`Payment failed: ${errorMsg}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAction = (action) => {
    sendMessage(action);
  };

  const toggleExpanded = (messageId) => {
    setExpandedMessages(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  };

  const getCategoryEmoji = (category) => {
    const emojiMap = {
      'desserts': '🍰',
      'beverages': '🥤',
      'street food': '🍔',
      'starters': '🍢',
      'main course': '🍛',
      'chicken': '🍗',
      'breads': '🥖',
      'chinese': '🥢',
      'indian': '🍛',
      'rice': '🍚',
      'soup': '🍲',
      'vegetarian': '🥗'
    };
    return emojiMap[category.toLowerCase()] || '🍽️';
  };

  if (!isOpen) return null;

  return (
    <div className="chatbot-modal-overlay" onClick={onClose}>
      <div className="chatbot-modal" onClick={(e) => e.stopPropagation()}>
        <div className="chatbot-header">
          <div className="chatbot-header-left">
            <ShoppingCart className="h-5 w-5" />
            <div>
              <h3>Order Assistant</h3>
              <p className="chatbot-status">
                {orderStage === 'ordering' && '● Online'}
                {orderStage === 'payment' && '💳 Payment'}
                {orderStage === 'completed' && '✓ Done'}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="chatbot-close-btn">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="chatbot-messages">
          {messages.map((msg) => {
            const isExpanded = expandedMessages.has(msg.id);
            const showViewAll = msg.menuItems && msg.menuItems.length > 5;
            
            return (
              <div key={msg.id} className={`message ${msg.type}`}>
                <div className="message-content">
                  <p style={{whiteSpace: 'pre-wrap'}}>{msg.text}</p>
                  
                  {msg.menuItems && msg.menuItems.length > 0 && (
                    <div className="menu-items-grid">
                      {(isExpanded ? msg.menuItems : msg.menuItems.slice(0, 5)).map((item) => (
                        <div key={item.id} className="menu-item-card">
                          <div className="menu-item-header">
                            <div>
                              <p className="menu-item-name">{item.name}</p>
                              <p className="menu-item-category">{item.category}</p>
                            </div>
                            <p className="menu-item-price">₹{item.price}</p>
                          </div>
                          {item.description && (
                            <p className="menu-item-description">{item.description}</p>
                          )}
                        </div>
                      ))}
                      
                      {showViewAll && (
                        <button 
                          onClick={() => toggleExpanded(msg.id)}
                          className="view-all-btn"
                        >
                          {isExpanded ? (
                            <>Show Less <ChevronDown className="icon-rotate" /></>
                          ) : (
                            <>View All {msg.menuItems.length} Items <ChevronDown /></>
                          )}
                        </button>
                      )}
                    </div>
                  )}

                  <span className="message-time">
                    {msg.timestamp.toLocaleTimeString('en-US', { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </span>
                </div>
              </div>
            );
          })}

          {isLoading && (
            <div className="message bot">
              <div className="message-content">
                <p>Typing...</p>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {orderStage === 'ordering' && categories.length > 0 && !orderSummary && (
          <div className="quick-actions">
            {categories.map((category, index) => (
              <Button
                key={index}
                size="sm"
                variant="outline"
                onClick={() => handleQuickAction(category)}
                className="category-pill"
              >
                {getCategoryEmoji(category)} {category}
              </Button>
            ))}
          </div>
        )}

        {orderSummary && orderStage === 'ordering' && (
          <Card className="order-summary-card" style={{padding: '1rem', marginBottom: '1rem'}}>
            <h4 style={{marginBottom: '0.5rem'}}>📋 Order Summary</h4>
            <div style={{marginBottom: '1rem'}}>
              {orderSummary.items?.map((item, idx) => (
                <div key={idx} style={{display: 'flex', justifyContent: 'space-between', padding: '0.25rem 0'}}>
                  <span>{item.quantity}x {item.name}</span>
                  <span>₹{(item.price * item.quantity).toFixed(2)}</span>
                </div>
              ))}
            </div>
            <div style={{borderTop: '1px solid #e5e7eb', paddingTop: '0.5rem', marginBottom: '0.5rem'}}>
              <div style={{display: 'flex', justifyContent: 'space-between', padding: '0.25rem 0'}}>
                <span>Subtotal:</span>
                <span>₹{orderSummary.subtotal?.toFixed(2) || '0.00'}</span>
              </div>
              <div style={{display: 'flex', justifyContent: 'space-between', padding: '0.25rem 0'}}>
                <span>Tax (5%):</span>
                <span>₹{orderSummary.tax?.toFixed(2) || '0.00'}</span>
              </div>
              <div style={{display: 'flex', justifyContent: 'space-between', padding: '0.25rem 0', fontWeight: 'bold', fontSize: '1.1em'}}>
                <span>Total:</span>
                <span>₹{orderSummary.total?.toFixed(2) || '0.00'}</span>
              </div>
            </div>
            <Button 
              onClick={handleConfirmOrder} 
              style={{width: '100%', marginTop: '0.5rem'}} 
              disabled={isLoading || currentOrderId || isCreatingOrder}
            >
              <CheckCircle className="h-4 w-4" style={{marginRight: '0.5rem'}} />
              {isLoading || isCreatingOrder ? 'Creating Order...' : currentOrderId ? 'Order Created ✓' : 'Confirm Order'}
            </Button>
          </Card>
        )}

        {orderStage === 'payment' && orderSummary && (
          <Card className="payment-card" style={{padding: '1rem', marginBottom: '1rem'}}>
            <h4 style={{marginBottom: '1rem'}}>💳 Select Payment Method</h4>
            <div style={{marginBottom: '1rem'}}>
              <div style={{display: 'flex', justifyContent: 'space-between', padding: '0.25rem 0'}}>
                <span>Subtotal:</span>
                <span>₹{orderSummary.subtotal?.toFixed(2) || '0.00'}</span>
              </div>
              <div style={{display: 'flex', justifyContent: 'space-between', padding: '0.25rem 0'}}>
                <span>Tax (5%):</span>
                <span>₹{orderSummary.tax?.toFixed(2) || '0.00'}</span>
              </div>
              <div style={{display: 'flex', justifyContent: 'space-between', padding: '0.25rem 0', fontWeight: 'bold', fontSize: '1.1em'}}>
                <span>Total:</span>
                <span>₹{orderSummary.total?.toFixed(2) || '0.00'}</span>
              </div>
            </div>
            <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem'}}>
              <Button onClick={() => handlePayment('cash')} disabled={isLoading}>
                💵 Cash
              </Button>
              <Button onClick={() => handlePayment('card')} disabled={isLoading}>
                💳 Card
              </Button>
              <Button onClick={() => handlePayment('upi')} disabled={isLoading}>
                📱 UPI
              </Button>
            </div>
          </Card>
        )}

        {orderStage === 'ordering' && !orderSummary && (
          <div className="chatbot-input-container">
            <div className="input-wrapper">
              <Input
                value={inputMessage}
                onChange={handleInputChange}
                onKeyPress={(e) => e.key === 'Enter' && !isLoading && sendMessage()}
                placeholder="Type your order... e.g., '2 paneer tikka'"
                disabled={isLoading}
              />
              
              {suggestions.length > 0 && (
                <div className="suggestions-dropdown">
                  {suggestions.map((suggestion, idx) => (
                    <div 
                      key={idx}
                      className="suggestion-item"
                      onClick={() => {
                        setInputMessage(suggestion);
                        setSuggestions([]);
                        sendMessage(suggestion);
                      }}
                    >
                      {getCategoryEmoji(suggestion)} {suggestion}
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            <Button
              onClick={() => sendMessage()}
              disabled={isLoading || !inputMessage.trim()}
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        )}

        {orderStage === 'completed' && (
          <div style={{textAlign: 'center', padding: '2rem'}}>
            <CheckCircle className="h-12 w-12 text-green-500" style={{margin: '0 auto 1rem'}} />
            <h3 style={{marginBottom: '0.5rem'}}>Thank you! 🎉</h3>
            <p>Your order has been placed successfully!</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatbotModal;
