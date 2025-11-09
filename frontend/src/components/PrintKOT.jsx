import React, { useRef, useState } from 'react';
import axios from 'axios';
import { Printer, Download, X, AlertCircle } from 'lucide-react';
import { Button } from './ui/button';
import './KOTStyles.css';

const PrintKOT = ({ kot, isOpen, onClose, API }) => {
  const printRef = useRef();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen || !kot) return null;

  // Format date and time
  const formatDateTime = (dateString) => {
    if (!dateString) return { date: 'N/A', time: 'N/A' };
    const date = new Date(dateString);
    return {
      date: date.toLocaleDateString('en-IN'),
      time: date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
    };
  };

  const { date, time } = formatDateTime(kot.created_at);

  // Handle Print to Thermal Printer
const handlePrint = () => {
  try {
    setIsLoading(true);
    const printWindow = window.open('', '', 'height=600,width=800');
    
    const itemsHTML = (kot.items || []).map(item => 
      `<tr><td style="padding:8px; border:1px solid #000;">${item.quantity}x ${item.name}</td><td style="padding:8px; border:1px solid #000;">${item.notes || ''}</td></tr>`
    ).join('');
    
    const content = `
      <html>
        <head>
          <title>KOT Print</title>
          <style>
            body { font-family: 'Courier New', monospace; padding: 20px; margin: 0; }
            .header { text-align: center; font-weight: bold; font-size: 16px; margin: 10px 0; }
            table { width: 100%; border-collapse: collapse; margin: 10px 0; }
            td { border: 1px solid #000; padding: 8px; font-size: 12px; }
            th { background: #f0f0f0; border: 1px solid #000; padding: 8px; font-weight: bold; }
            .section-title { font-weight: bold; margin: 15px 0 5px 0; font-size: 14px; }
            .footer { text-align: center; margin-top: 20px; font-weight: bold; }
          </style>
        </head>
        <body>
          <div class="header">TASTE PARADISE</div>
          <div class="header" style="font-size: 12px;">Kitchen Order Ticket</div>
          
          <table>
            <tr><td><b>Order ID:</b></td><td>${kot.order_id || 'N/A'}</td></tr>
            <tr><td><b>KOT ID:</b></td><td>${kot._id?.substring(0, 8) || 'N/A'}</td></tr>
            <tr><td><b>Table:</b></td><td>${kot.table_number || 'N/A'}</td></tr>
            <tr><td><b>Time:</b></td><td>${date} ${time}</td></tr>
          </table>
          
          <div class="section-title">ORDER ITEMS</div>
          <table>
            <tr><th>Item</th><th>Notes</th></tr>
            ${itemsHTML || '<tr><td colspan="2">No items</td></tr>'}
          </table>
          
          ${kot.special_instructions ? `<div class="section-title">SPECIAL INSTRUCTIONS:</div><div style="padding: 10px; border: 1px dashed #000; margin: 10px 0;">${kot.special_instructions}</div>` : ''}
          
          <div class="footer">Thank You!</div>
        </body>
      </html>
    `;
    
    printWindow.document.write(content);
    printWindow.document.close();
    
    setTimeout(() => {
      printWindow.print();
      setIsLoading(false);
    }, 250);
  } catch (err) {
    setError(err.message);
    setIsLoading(false);
  }
};




  // Handle Download as PDF
  const handleDownload = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await axios.post(`${API}/kots/${kot.id}/generate-pdf`, {}, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `KOT-${kot.id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);

      alert('KOT downloaded successfully');
    } catch (err) {
      setError('Failed to download: ' + (err.response?.data?.detail || err.message));
      console.error('Download error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Update KOT status
  const updateKOTStatus = async (status) => {
    try {
      await axios.put(`${API}/kots/${kot.id}`, { status: status });
      alert(`KOT marked as ${status}`);
    } catch (err) {
      console.error('Error updating KOT status:', err);
      setError('Failed to update KOT status');
    }
  };

  return (
    <>
      {/* Modal Overlay */}
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">

          {/* Header */}
          <div className="flex justify-between items-center p-4 border-b sticky top-0 bg-white z-10">
            <h2 className="text-xl font-bold text-gray-800">🍽️ Kitchen Order Ticket (KOT)</h2>
            <button
              onClick={onClose}
              className="p-1 hover:bg-gray-100 rounded transition"
              disabled={isLoading}
            >
              <X size={24} />
            </button>
          </div>

          {/* Error Alert */}
          {error && (
            <div className="mx-4 mt-4 p-3 bg-red-50 border border-red-200 rounded flex items-start gap-2">
              <AlertCircle size={20} className="text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-red-800">Error</p>
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            </div>
          )}

          {/* KOT Content */}
          <div className="p-6 bg-white">
            <div ref={printRef} className="kot-container">
              {/* Header */}
              <div className="text-center mb-6 pb-4 border-b-2">
                <h1 className="text-2xl font-bold mb-1">🍽️ TASTE PARADISE</h1>
                <p className="text-sm text-gray-600">Kitchen Order Ticket</p>
              </div>

              {/* KOT Details */}
              <div className="grid grid-cols-2 gap-4 mb-6 text-sm">
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-gray-600 text-xs uppercase">Order ID</p>
                  <p className="font-bold text-lg text-blue-600">{kot.order_id || 'N/A'}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-gray-600 text-xs uppercase">KOT ID</p>
                  <p className="font-bold text-lg">{kot.id ? kot.id.substring(0, 8) : 'N/A'}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-gray-600 text-xs uppercase">Table</p>
                  <p className="font-bold text-lg">{kot.table_number || 'N/A'}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-gray-600 text-xs uppercase">Date & Time</p>
                  <p className="font-bold text-sm">{date} {time}</p>
                </div>
              </div>

              {/* Divider */}
              <div className="border-t-2 border-dashed border-gray-400 my-4"></div>

              {/* Items Section */}
              <div className="mb-6">
                <h3 className="font-bold text-lg mb-3 text-gray-800">📋 ORDER ITEMS</h3>
                <table className="w-full text-sm">
                  <tbody>
                    {kot.items && kot.items.length > 0 ? (
                      kot.items.map((item, idx) => (
                        <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50">
                          <td className="py-2 pl-2">
                            <span className="font-bold text-blue-600">{item.quantity}x</span>
                            {' '}{item.name}
                          </td>
                          <td className="text-right pr-2 text-gray-600">
                            {item.notes && `(${item.notes})`}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="2" className="py-2 text-center text-gray-500">No items found</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Special Instructions */}
              {kot.special_instructions && (
                <>
                  <div className="border-t-2 border-dashed border-gray-400 my-4"></div>
                  <div className="mb-6 p-4 bg-yellow-50 border-l-4 border-yellow-400 rounded">
                    <p className="font-bold text-sm text-yellow-900 mb-2">⚠️ SPECIAL INSTRUCTIONS:</p>
                    <p className="text-sm text-yellow-800 whitespace-pre-wrap">{kot.special_instructions}</p>
                  </div>
                </>
              )}

              {/* Footer */}
              <div className="border-t-2 border-dashed border-gray-400 pt-4 mt-4 text-center">
                <p className="text-xs text-gray-600 font-semibold">Thank You!</p>
                <p className="text-xs text-gray-500">Prepared by: Kitchen Staff</p>
              </div>
            </div>
          </div>

          {/* Actions Footer */}
          <div className="flex gap-2 p-4 border-t bg-gray-50 sticky bottom-0">
            <Button
              onClick={handlePrint}
              disabled={isLoading}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Printer size={18} />
              {isLoading ? 'Processing...' : 'Print KOT'}
            </Button>
            <Button
              onClick={handleDownload}
              disabled={isLoading}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Download size={18} />
              {isLoading ? 'Processing...' : 'Download PDF'}
            </Button>
            <Button
              onClick={onClose}
              disabled={isLoading}
              variant="outline"
              className="px-4"
            >
              <X size={18} />
            </Button>
          </div>
        </div>
      </div>
    </>
  );
};

export default PrintKOT;