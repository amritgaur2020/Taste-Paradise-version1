import React, { useRef, useEffect, useState } from "react";
import "./InvoicePrint.css";
import PrintInvoice from "./PrintInvoice";

const InvoiceTemplate = (props) => {
  const invoiceRef = useRef();
  const [orderData, setOrderData] = useState(props.orderData || {});

  // Update orderData when props change
  useEffect(() => {
    console.log('🔄 InvoiceTemplate props updated:', props.orderData);
    if (props.orderData) {
      setOrderData(props.orderData);
      console.log('📦 Items in order:', props.orderData.items);
    }
  }, [props.orderData]);

  const handlePrint = () => {
    const printContents = invoiceRef.current.outerHTML;
    const printWindow = window.open("", "", "width=400,height=600,left=200,top=200");
    
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Invoice - ${orderData.id || orderData.order_id || 'NA'}</title>
          <style>
            @media print {
              @page { size: 80mm auto; margin: 0; }
              body { margin: 0; padding: 10px; font-family: Arial, sans-serif; }
            }
            body { font-family: Arial, sans-serif; max-width: 80mm; margin: 0 auto; }
            table { width: 100%; border-collapse: collapse; margin: 10px 0; }
            th, td { padding: 5px; text-align: left; border-bottom: 1px solid #ddd; }
            .text-center { text-align: center; }
            .text-right { text-align: right; }
            .font-bold { font-weight: bold; }
            .border-top { border-top: 2px solid #000; }
          </style>
        </head>
        <body>${printContents}</body>
      </html>
    `);
    
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
      printWindow.print();
      printWindow.close();
    }, 250);
  };

  // Safety check
  const items = orderData?.items || [];
  console.log('🎯 Rendering invoice with items:', items);

  return (
    <div>
      <div ref={invoiceRef} style={{ padding: "20px", maxWidth: "80mm", margin: "0 auto" }}>
        {/* Header */}
        <div className="text-center" style={{ borderBottom: "2px solid #d97706", paddingBottom: "10px", marginBottom: "10px" }}>
          <h2 style={{ margin: 0, fontSize: "20px", color: "#d97706" }}>Taste Paradise</h2>
          <p style={{ margin: "5px 0", fontSize: "12px" }}>Restaurant & Billing Service</p>
          <p style={{ margin: "5px 0", fontSize: "10px" }}>123 Food Street, Flavor City, FC 12345</p>
          <p style={{ margin: "5px 0", fontSize: "10px" }}>Phone: +91 8218355207 | Email: info@tasteparadise.com</p>
        </div>

        {/* Invoice Number and Date */}
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "15px", fontSize: "12px" }}>
          <div>
            <p style={{ margin: "2px 0", fontWeight: "bold", fontSize: "16px" }}>INVOICE</p>
            <p style={{ margin: "2px 0" }}>{orderData.order_id || orderData.id || 'NA'}</p>
          </div>
          <div style={{ textAlign: "right" }}>
            <p style={{ margin: "2px 0" }}>Date: {new Date().toLocaleDateString("en-IN")}</p>
            <p style={{ margin: "2px 0" }}>Time: {new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}</p>
          </div>
        </div>

        {/* Bill To and Order Details */}
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "15px", fontSize: "12px" }}>
          <div>
            <p style={{ margin: "2px 0", fontWeight: "bold" }}>Bill To:</p>
            <p style={{ margin: "2px 0" }}>{orderData.customer_name || "Walk-in"}</p>
            <p style={{ margin: "2px 0" }}>Table: {orderData.table_number || 0}</p>
          </div>
          <div style={{ textAlign: "right" }}>
            <p style={{ margin: "2px 0", fontWeight: "bold" }}>Order Details:</p>
            <p style={{ margin: "2px 0" }}>Status: {orderData.status}</p>
            <p style={{ margin: "2px 0" }}>Payment: {orderData.payment_status}</p>
            <p style={{ margin: "2px 0" }}>Method: {orderData.payment_method}</p>
          </div>
        </div>

        {/* Items Table */}
        <table style={{ width: "100%", fontSize: "11px", border: "1px solid #ddd", marginBottom: "15px" }}>
          <thead>
            <tr style={{ backgroundColor: "#f5f5f5", borderBottom: "2px solid #d97706" }}>
              <th style={{ textAlign: "left", padding: "8px", fontWeight: "bold" }}>Item</th>
              <th style={{ textAlign: "center", padding: "8px", fontWeight: "bold" }}>Qty</th>
              <th style={{ textAlign: "right", padding: "8px", fontWeight: "bold" }}>Rate (₹)</th>
              <th style={{ textAlign: "right", padding: "8px", fontWeight: "bold" }}>Amount (₹)</th>
            </tr>
          </thead>
          <tbody>
            {items.length > 0 ? (
              items.map((item, index) => {
                const itemName = item?.menuitemname || item?.name || 'Unknown Item';
                const quantity = item?.quantity || 0;
                const price = parseFloat(item?.price || item?.rate || 0);
                const amount = price * quantity;
                
                console.log(`📝 Item ${index}:`, itemName, 'Qty:', quantity, 'Price:', price);
                
                return (
                  <tr key={index} style={{ borderBottom: "1px solid #eee" }}>
                    <td style={{ padding: "8px" }}>{itemName}</td>
                    <td style={{ textAlign: "center", padding: "8px" }}>{quantity}</td>
                    <td style={{ textAlign: "right", padding: "8px" }}>₹{price.toFixed(2)}</td>
                    <td style={{ textAlign: "right", padding: "8px" }}>₹{amount.toFixed(2)}</td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan="4" style={{ textAlign: "center", padding: "20px", color: "#999" }}>
                  No items found
                </td>
              </tr>
            )}
          </tbody>
        </table>

        {/* Totals */}
        <div style={{ borderTop: "2px solid #333", paddingTop: "10px", fontSize: "12px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", margin: "5px 0" }}>
            <span style={{ fontWeight: "bold" }}>Subtotal:</span>
            <span>₹{(parseFloat(orderData.total_amount || 0)).toFixed(2)}</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", margin: "5px 0", paddingBottom: "10px", borderBottom: "2px solid #d97706" }}>
            <span style={{ fontWeight: "bold" }}>GST (5%):</span>
            <span>₹{(parseFloat(orderData.total_amount || 0) * 0.05).toFixed(2)}</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", margin: "10px 0", fontWeight: "bold", fontSize: "16px" }}>
            <span>Total Amount:</span>
            <span>₹{(parseFloat(orderData.total_amount || 0) * 1.05).toFixed(2)}</span>
          </div>
        </div>

        {/* Footer */}
        <div style={{ textAlign: "center", marginTop: "20px", fontSize: "10px", borderTop: "1px solid #ddd", paddingTop: "10px" }}>
          <p style={{ margin: "5px 0", fontWeight: "bold" }}>Thank you for dining with us at Taste Paradise!</p>
          <p style={{ margin: "5px 0" }}>GST No: 27AAAAA0000A1Z5 | FSSAI Lic: 12345678901234</p>
          <p style={{ margin: "5px 0" }}>This is a computer generated invoice.</p>
        </div>
      </div>

      {/* Print Button */}
      <div style={{ textAlign: "center", marginTop: "20px" }}>
        <PrintInvoice onPrint={handlePrint} orderData={orderData} />
      </div>
    </div>
  );
};

export default InvoiceTemplate;
