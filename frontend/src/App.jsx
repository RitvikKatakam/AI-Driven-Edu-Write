import { useState, useEffect } from 'react'
import './App.css'
import Login from './components/Login'
import Dashboard from './components/Dashboard'

const App = () => {
  console.log("App: rendering...");
  const [user, setUser] = useState(null);

  // Check if user is already logged in on mount
  useEffect(() => {
    try {
      const savedUser = localStorage.getItem('user');
      if (savedUser && savedUser !== "undefined") {
        setUser(JSON.parse(savedUser));
      }
    } catch (e) {
      console.error("Failed to parse user from localStorage", e);
      localStorage.removeItem('user');
    }
  }, []);

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('user');
  };

  return (
    <div className="App" style={{ minHeight: '100vh', background: '#05131e' }}>
      {console.log("App: current user state:", user)}
      {!user ? (
        <Login onLoginSuccess={handleLoginSuccess} />
      ) : (
        <Dashboard user={user} onLogout={handleLogout} />
      )}
    </div>
  );
};

export default App