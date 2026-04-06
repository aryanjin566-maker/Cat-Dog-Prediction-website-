import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FiMail, FiLock, FiUser, FiPhone, FiMapPin } from 'react-icons/fi';
import toast from 'react-hot-toast';
import '../styles/auth.css';

const Signup = () => {
  const navigate = useNavigate();
  const { signup } = useAuth();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    name: '',
    phone_number: '',
    address: '',
  });

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
      await signup(formData);
      toast.success('Signup successful! Please login.');
      navigate('/login');
    } catch (error) {
      toast.error(error?.message || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>🐕 Create Account</h1>
          <p>Join our Dog-Cat Classifier community</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label>Username</label>
            <div className="input-with-icon">
              <FiUser />
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                placeholder="Choose username"
                required
                minLength={3}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Email</label>
            <div className="input-with-icon">
              <FiMail />
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="your@email.com"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label>Full Name</label>
            <div className="input-with-icon">
              <FiUser />
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="Full name"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label>Password</label>
            <div className="input-with-icon">
              <FiLock />
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Min 8 chars (uppercase, lowercase, number)"
                required
                minLength={8}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Phone Number (Optional)</label>
            <div className="input-with-icon">
              <FiPhone />
              <input
                type="tel"
                name="phone_number"
                value={formData.phone_number}
                onChange={handleChange}
                placeholder="9876543210"
              />
            </div>
          </div>

          <div className="form-group">
            <label>Address (Optional)</label>
            <div className="input-with-icon">
              <FiMapPin />
              <input
                type="text"
                name="address"
                value={formData.address}
                onChange={handleChange}
                placeholder="Your address"
              />
            </div>
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Creating Account...' : 'Sign Up'}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account? <Link to="/login">Login here</Link>
        </p>
      </div>
    </div>
  );
};

export default Signup;