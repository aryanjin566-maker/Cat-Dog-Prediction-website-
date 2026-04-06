import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { predictAPI } from '../services/api';
import { FiLogOut, FiUser, FiImage, FiUpload, FiDownload } from 'react-icons/fi';
import toast from 'react-hot-toast';
import '../styles/dashboard.css';

const Dashboard = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully');
    navigate('/login');
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFiles(files);
    }
  };

  const handleFileInput = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFiles(files);
    }
  };

  const handleFiles = (files) => {
    const fileArray = Array.from(files);
    
    const validFiles = fileArray.filter((file) => {
      const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
      if (!validTypes.includes(file.type)) {
        toast.error(`${file.name} is not a valid image format`);
        return false;
      }
      return true;
    });

    if (validFiles.length + uploadedFiles.length > 20) {
      toast.error('Maximum 20 files allowed');
      return;
    }

    setUploadedFiles((prev) => [...prev, ...validFiles]);
    toast.success(`${validFiles.length} image(s) added`);
  };

  const removeFile = (index) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUploadAndPredict = async () => {
    if (uploadedFiles.length === 0) {
      toast.error('Please select at least one image');
      return;
    }

    setLoading(true);

    try {
      console.log(`📤 Uploading ${uploadedFiles.length} images...`);
      const response = await predictAPI.uploadImages(uploadedFiles);
      
      console.log('Response:', response.data);
      
      if (response.data.results) {
        const resultsWithUrls = response.data.results.map((result) => ({
          ...result,
          image_url: result.success 
            ? `${API_URL}/api/uploads/${result.filename}`
            : null,
        }));
        
        setPredictions(resultsWithUrls);
        setUploadedFiles([]);
        
        const successful = resultsWithUrls.filter(r => r.success).length;
        toast.success(`${successful}/${resultsWithUrls.length} images classified!`);
      } else {
        toast.error('No results received');
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast.error(error.response?.data?.message || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const downloadResults = () => {
    const successful = predictions.filter(p => p.success);
    if (successful.length === 0) {
      toast.error('No successful predictions to download');
      return;
    }

    const csv = [
      ['Filename', 'Prediction', 'Confidence (%)'],
      ...successful.map(p => [
        p.original_filename, 
        p.prediction.toUpperCase(), 
        p.confidence.toFixed(2)
      ])
    ]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', 'classification_results.csv');
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    toast.success('Results downloaded!');
  };

  return (
    <div className="dashboard">
      {/* Navbar */}
      <nav className="navbar">
        <div className="container">
          <div className="navbar-content">
            <div className="navbar-brand">
              <h1>🐕🐱 Dog-Cat Classifier</h1>
            </div>
            <div className="navbar-actions">
              <button 
                className="btn-icon"
                onClick={() => navigate('/profile')}
                title="Profile"
              >
                <FiUser size={20} />
              </button>
              <button 
                className="btn-icon btn-logout"
                onClick={handleLogout}
                title="Logout"
              >
                <FiLogOut size={20} />
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="dashboard-main">
        <div className="container">
          <div className="welcome-section">
            <h2>Welcome, {user?.name}! 👋</h2>
            <p>Upload images to classify them as dogs or cats using AI</p>
          </div>

          <div className="dashboard-grid">
            {/* Upload Section */}
            <div className="upload-section">
              <div className="card">
                <div className="section-header">
                  <FiUpload size={24} />
                  <h3>Upload Images</h3>
                </div>

                <div
                  className={`drag-drop-area ${dragActive ? 'active' : ''}`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                  onClick={() => {
                    const fileInput = document.getElementById('file-input');
                    if (fileInput) {
                      fileInput.click();
                    }
                  }}
                  role="button"
                  tabIndex={0}
                >
                  <div className="drag-drop-content">
                    <FiImage size={48} />
                    <h4>Drag and drop images here</h4>
                    <p>or click to browse</p>
                  </div>
                  <input
                    type="file"
                    multiple
                    accept="image/*"
                    onChange={handleFileInput}
                    className="file-input"
                    id="file-input"
                  />
                </div>

                {/* File List */}
                {uploadedFiles.length > 0 && (
                  <div className="file-list">
                    <h4>Selected Files ({uploadedFiles.length}/20)</h4>
                    <div className="files-grid">
                      {uploadedFiles.map((file, index) => (
                        <div key={index} className="file-item">
                          <img 
                            src={URL.createObjectURL(file)} 
                            alt={file.name}
                            className="file-preview"
                          />
                          <div className="file-info">
                            <p className="file-name">{file.name}</p>
                            <p className="file-size">
                              {(file.size / 1024).toFixed(2)} KB
                            </p>
                          </div>
                          <button
                            className="btn-remove"
                            onClick={() => removeFile(index)}
                            title="Remove file"
                            type="button"
                          >
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>

                    <button
                      className="btn btn-primary btn-upload"
                      onClick={handleUploadAndPredict}
                      disabled={loading || uploadedFiles.length === 0}
                      type="button"
                    >
                      {loading ? (
                        <>
                          <span className="spinner-small"></span>
                          Processing...
                        </>
                      ) : (
                        `Classify ${uploadedFiles.length} Image${uploadedFiles.length !== 1 ? 's' : ''}`
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Results Section */}
            {predictions.length > 0 && (
              <div className="results-section">
                <div className="card">
                  <div className="section-header">
                    <FiImage size={24} />
                    <h3>Results ({predictions.filter(p => p.success).length}/{predictions.length})</h3>
                  </div>

                  <div className="results-grid">
                    {predictions.map((prediction, index) => (
                      <div key={index} className="result-card">
                        {prediction.success ? (
                          <>
                            <div className="result-image">
                              {prediction.image_url && (
                                <img 
                                  src={prediction.image_url}
                                  alt={prediction.original_filename}
                                  onError={(e) => {
                                    e.target.style.display = 'none';
                                  }}
                                />
                              )}
                            </div>
                            <div className="result-content">
                              <h4 title={prediction.original_filename}>
                                {prediction.original_filename}
                              </h4>
                              <div className="result-prediction">
                                <span className={`badge ${prediction.prediction}`}>
                                  {prediction.prediction.toUpperCase()}
                                </span>
                                <span className="confidence">
                                  {prediction.confidence.toFixed(2)}%
                                </span>
                              </div>
                              <div className="confidence-bar">
                                <div
                                  className="confidence-fill"
                                  style={{ width: `${prediction.confidence}%` }}
                                ></div>
                              </div>
                            </div>
                          </>
                        ) : (
                          <div className="result-error">
                            <p className="error-name">{prediction.original_filename}</p>
                            <p className="error-message">❌ Failed to process</p>
                            <p className="error-detail">{prediction.error?.split('\n')[0]}</p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  <div className="results-actions">
                    <button
                      className="btn btn-secondary"
                      onClick={downloadResults}
                      type="button"
                    >
                      <FiDownload /> Download Results
                    </button>
                    <button
                      className="btn btn-primary"
                      onClick={() => {
                        setPredictions([]);
                        setUploadedFiles([]);
                      }}
                      type="button"
                    >
                      Classify More Images
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;