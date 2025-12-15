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
      
      // ✅ FIXED: Changed item.name to item.menuitemname and item.notes to item.specialinstructions
      const itemsHTML = (kot.items || []).map(item => `
        <tr>
          <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">
            ${item.quantity}x ${item.menuitemname || item.name || 'Unknown Item'}
          </td>
          <td style="padding: 8px; border: 1px solid #ddd;">
            ${item.specialinstructions ? `(${item.specialinstructions})` : ''}
          </td>
        </tr>
      `).join('');

      const printContent = `
        <!DOCTYPE html>
        <html>
        <head>
          <title>Kitchen Order Ticket</title>
          <style>
            @media print {
              @page { size: 80mm auto; margin: 0; }
              body { margin: 0; padding: 10px; }
            }
            body {
              font-family: 'Courier New', monospace;
              max-width: 80mm;
              margin: 0 auto;
              padding: 10px;
            }
            h1 {
              text-align: center;
              font-size: 20px;
              margin: 10px 0;
              border-bottom: 2px solid #000;
              padding-bottom: 5px;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              margin: 10px 0;
            }
            th, td {
              padding: 5px;
              text-align: left;
              border: 1px solid #ddd;
            }
            .info-table td {
              font-size: 12px;
            }
            .items-table {
              margin-top: 15px;
            }
            .items-table th {
              background-color: #f0f0f0;
              font-weight: bold;
            }
            .no-items {
              text-align: center;
              padding: 20px;
              font-style: italic;
              color: #666;
            }
            .special-instructions {
              margin-top: 15px;
              padding: 10px;
              background-color: #fff3cd;
              border: 1px solid #ffc107;
              border-radius: 4px;
            }
            .footer {
              text-align: center;
              margin-top: 20px;
              font-size: 12px;
              border-top: 2px dashed #000;
              padding-top: 10px;
            }
          </style>
        </head>
        <body>
          <h1>Kitchen Order Ticket</h1>
          
          <table class="info-table">
            <tr>
              <td><strong>Order ID:</strong></td>
              <td>${kot.order_id || 'N/A'}</td>
            </tr>
            <tr>
              <td><strong>KOT ID:</strong></td>
              <td>${kot._id?.substring(0, 8) || 'N/A'}</td>
            </tr>
            <tr>
              <td><strong>Table:</strong></td>
              <td>${kot.table_number || 'N/A'}</td>
            </tr>
            <tr>
              <td><strong>Time:</strong></td>
              <td>${date} ${time}</td>
            </tr>
          </table>

          <table class="items-table">
            <thead>
              <tr>
                <th>Item</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              ${itemsHTML || '<tr><td colspan="2" class="no-items">No items</td></tr>'}
            </tbody>
          </table>

          ${kot.special_instructions ? `
            <div class="special-instructions">
              <strong>⚠️ SPECIAL INSTRUCTIONS:</strong><br/>
              ${kot.special_instructions}
            </div>
          ` : ''}

          <div class="footer">
            <p>Thank You!</p>
            <p>Prepared by: Kitchen Staff</p>
          </div>
        </body>
        </html>
      `;

      printWindow.document.write(printContent);
      printWindow.document.close();
      
      setTimeout(() => {
        printWindow.print();
        printWindow.close();
        setIsLoading(false);
      }, 500);

    } catch (err) {
      console.error('Print error:', err);
      setError('Failed to print KOT');
      setIsLoading(false);
    }
  };

  // Handle Download as PDF
  const handleDownload = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await axios.post(`${API}/kot/download`, {
        kot_id: kot._id || kot.id,
        order_id: kot.order_id
      }, {
        responseType: 'blob'
      });

      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `KOT-${kot.order_id || 'unknown'}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      setIsLoading(false);
    } catch (err) {
      console.error('Download error:', err);
      setError('Failed to download KOT. Please try again.');
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-xl font-bold">Kitchen Order Ticket</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mx-4 mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
            <AlertCircle className="h-5 w-5" />
            <span>{error}</span>
          </div>
        )}

        {/* KOT Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]" ref={printRef}>
          <div className="border-2 border-gray-300 rounded-lg p-6">
            <h3 className="text-2xl font-bold text-center mb-4 pb-2 border-b-2 border-gray-300">
              Kitchen Order Ticket
            </h3>

            {/* Order Information */}
            <div className="grid grid-cols-2 gap-4 mb-6 text-sm">
              <div>
                <span className="font-semibold">Order ID:</span>
                <p>{kot.order_id || 'N/A'}</p>
              </div>
              <div>
                <span className="font-semibold">KOT ID:</span>
                <p>{kot.id ? kot.id.substring(0, 8) : 'N/A'}</p>
              </div>
              <div>
                <span className="font-semibold">Table:</span>
                <p>{kot.table_number || 'N/A'}</p>
              </div>
              <div>
                <span className="font-semibold">Date & Time:</span>
                <p>{date} {time}</p>
              </div>
            </div>

            {/* Items Table */}
            <table className="w-full border-collapse mb-4">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border border-gray-300 px-3 py-2 text-left">Item</th>
                  <th className="border border-gray-300 px-3 py-2 text-left">Notes</th>
                </tr>
              </thead>
              <tbody>
                {/* ✅ FIXED: Changed item.name to item.menuitemname and item.notes to item.specialinstructions */}
                {(kot.items || []).map((item, index) => (
                  <tr key={index}>
                    <td className="border border-gray-300 px-3 py-2">
                      {item.quantity}x {' '}
                      {item.menuitemname || item.name || 'Unknown Item'}
                    </td>
                    <td className="border border-gray-300 px-3 py-2 text-sm text-gray-600">
                      {item.specialinstructions && `(${item.specialinstructions})`}
                    </td>
                  </tr>
                ))}
                {(!kot.items || kot.items.length === 0) && (
                  <tr>
                    <td colSpan="2" className="text-center py-4 text-gray-500">
                      No items found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>

            {/* Special Instructions */}
            {kot.special_instructions && (
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
                <p className="font-semibold text-sm">⚠️ SPECIAL INSTRUCTIONS:</p>
                <p className="text-sm mt-1">{kot.special_instructions}</p>
              </div>
            )}

            {/* Footer */}
            <div className="text-center mt-6 pt-4 border-t-2 border-dashed border-gray-300">
              <p className="text-sm">Thank You!</p>
              <p className="text-xs text-gray-500 mt-1">Prepared by: Kitchen Staff</p>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 p-4 border-t bg-gray-50">
          <Button
            onClick={handleDownload}
            disabled={isLoading}
            variant="outline"
            className="flex items-center gap-2"
          >
            <Download className="h-4 w-4" />
            {isLoading ? 'Downloading...' : 'Download PDF'}
          </Button>
          <Button
            onClick={handlePrint}
            disabled={isLoading}
            className="flex items-center gap-2 bg-orange-600 hover:bg-orange-700"
          >
            <Printer className="h-4 w-4" />
            {isLoading ? 'Printing...' : 'Print KOT'}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default PrintKOT;
