import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Upload, Download, CheckCircle, XCircle, ArrowLeft, FileText } from 'lucide-react';
import './inventory.css';

const API = window.API || 'http://127.0.0.1:8002/api';

const ImportInventory = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.xlsx') && !selectedFile.name.endsWith('.xls')) {
        alert('Please upload an Excel file (.xlsx or .xls)');
        return;
      }
      setFile(selectedFile);
      setResult(null);
    }
  };

  const handleImport = async () => {
    if (!file) {
      alert('Please select a file first');
      return;
    }

    try {
      setImporting(true);
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(
        `${API}/inventory/import-inventory-items`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      setResult(response.data);
      setImporting(false);
    } catch (error) {
      console.error('Import error:', error);
      alert(error.response?.data?.detail || 'Import failed');
      setImporting(false);
    }
  };

  const downloadTemplate = async () => {
    try {
      const response = await axios.get(
        `${API}/inventory/template`,
        { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'inventory_template.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Template download error:', error);
      alert('Failed to download template');
    }
  };

  return (
    <div className="import-inventory-page">
      {/* Header */}
      <div className="page-header">
        <button className="btn-back" onClick={() => navigate('/inventory/items')}>
          <ArrowLeft size={20} />
        </button>
        <div>
          <h1>Import Inventory Items</h1>
          <p>Upload Excel file to bulk import inventory items</p>
        </div>
      </div>

      {/* Instructions */}
      <div className="import-instructions">
        <h2>How to Import</h2>
        <ol>
          <li>Download the Excel template</li>
          <li>Fill in your inventory items data</li>
          <li>Upload the completed Excel file</li>
          <li>Review the results and check for any errors</li>
        </ol>

        <button className="btn-download-template" onClick={downloadTemplate}>
          <Download size={18} />
          Download Template
        </button>
      </div>

      {/* Upload Section */}
      <div className="upload-section">
        <div className="upload-card">
          <div className="upload-area">
            <Upload size={48} />
            <h3>Select Excel File</h3>
            <p>Supports .xlsx and .xls formats</p>

            <label className="file-input-label">
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              <span className="btn-secondary">
                <FileText size={18} />
                Choose File
              </span>
            </label>

            {file && (
              <div className="selected-file">
                <FileText size={20} />
                <span>{file.name}</span>
                <button onClick={() => setFile(null)}>
                  <XCircle size={16} />
                </button>
              </div>
            )}
          </div>

          {file && (
            <button
              className="btn-primary btn-import"
              onClick={handleImport}
              disabled={importing}
            >
              {importing ? 'Importing...' : 'Import Items'}
            </button>
          )}
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="import-results">
          <div className="results-header">
            <CheckCircle size={24} className="text-success" />
            <h2>Import Complete!</h2>
          </div>

          <div className="results-stats">
            <div className="result-stat result-stat-success">
              <div className="stat-value">{result.imported}</div>
              <div className="stat-label">New Items Added</div>
            </div>
            <div className="result-stat result-stat-warning">
              <div className="stat-value">{result.updated || 0}</div>
              <div className="stat-label">Items Updated</div>
            </div>
            <div className="result-stat result-stat-info">
              <div className="stat-value">{result.total}</div>
              <div className="stat-label">Total Processed</div>
            </div>
          </div>

          <button
            className="btn-primary"
            onClick={() => navigate('/inventory/items')}
          >
            View Inventory
          </button>
        </div>
      )}

      {/* Template Format Info */}
      <div className="format-info">
        <h3>Excel Template Format</h3>
        <p>Your Excel file should include these columns:</p>
        <div className="format-columns">
          <div className="format-column">
            <strong>name</strong>
            <span className="required-badge">Required</span>
            <p>Item name (e.g., "Paneer")</p>
          </div>
          <div className="format-column">
            <strong>category</strong>
            <span className="required-badge">Required</span>
            <p>Category (e.g., "Dairy")</p>
          </div>
          <div className="format-column">
            <strong>unit</strong>
            <span className="required-badge">Required</span>
            <p>Unit of measurement (kg, gm, ltr, ml, pieces)</p>
          </div>
          <div className="format-column">
            <strong>current_stock</strong>
            <span className="required-badge">Required</span>
            <p>Current stock quantity</p>
          </div>
          <div className="format-column">
            <strong>reorder_level</strong>
            <span className="required-badge">Required</span>
            <p>Minimum stock level</p>
          </div>
          <div className="format-column">
            <strong>unit_cost</strong>
            <span className="required-badge">Required</span>
            <p>Cost per unit (₹)</p>
          </div>
          <div className="format-column">
            <strong>supplier</strong>
            <span className="optional-badge">Optional</span>
            <p>Supplier name</p>
          </div>
          <div className="format-column">
            <strong>supplier_contact</strong>
            <span className="optional-badge">Optional</span>
            <p>Supplier contact info</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImportInventory;
