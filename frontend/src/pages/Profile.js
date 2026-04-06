import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FiArrowLeft, FiEdit2, FiSave } from 'react-icons/fi';
import toast from 'react-hot-toast';
import '../styles/profile.css';

const Profile = () => {
  const navigate = useNavigate();
  const { user, updateProfile } = useAuth();
  const [loading, setLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: user?.name || '',
    phone_number: user?.phone_number || '',
    address: user?.address || '',
  });

  useEffect(() => {
    if (user) {
      setFormData({
        name: user.name || '',
        phone_number: user.phone_number || '',
        address: user.address || '',
      });
    }
  }, [user]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await updateProfile(formData);
      toast.success('Profile updated successfully!');
      setIsEditing(false);
    } catch (error) {
      toast.error(error?.message || 'Update failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="profile-page">
      <div className="profile-header">
        <button 
          className="btn-back"
          onClick={() => navigate('/dashboard')}
        >
          <FiArrowLeft /> Back to Dashboard
        </button>
      </div>

      <div className="container">
        <div className="profile-card">
          <div className="profile-top">
            <div className="profile-avatar">
              <span>{user?.name?.charAt(0)?.toUpperCase() || 'U'}</span>
            </div>
            <div className="profile-info">
              <h1>{user?.name}</h1>
              <p className="unique-id">ID: {user?.unique_id}</p>
            </div>
          </div>

          {!isEditing ? (
            <>
              <div className="profile-details">
                <div className="detail-item">
                  <label>Email</label>
                  <p>{user?.email}</p>
                </div>
                <div className="detail-item">
                  <label>Phone Number</label>
                  <p>{user?.phone_number || 'Not provided'}</p>
                </div>
                <div className="detail-item">
                  <label>Address</label>
                  <p>{user?.address || 'Not provided'}</p>
                </div>
              </div>

              <button
                className="btn btn-primary"
                onClick={() => setIsEditing(true)}
              >
                <FiEdit2 /> Edit Profile
              </button>
            </>
          ) : (
            <form onSubmit={handleSubmit} className="profile-form">
              <div className="form-group">
                <label>Full Name</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>Phone Number</label>
                <input
                  type="tel"
                  name="phone_number"
                  value={formData.phone_number}
                  onChange={handleChange}
                />
              </div>

              <div className="form-group">
                <label>Address</label>
                <textarea
                  name="address"
                  value={formData.address}
                  onChange={handleChange}
                  rows={4}
                ></textarea>
              </div>

              <div className="form-actions">
                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={loading}
                >
                  <FiSave /> {loading ? 'Saving...' : 'Save Changes'}
                </button>
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={() => setIsEditing(false)}
                  disabled={loading}
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default Profile;