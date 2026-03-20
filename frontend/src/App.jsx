import React, { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import api from './services/api'
import Sidebar from './components/Sidebar'
import LoginPage from './pages/LoginPage'
import WorkerDashboard from './pages/WorkerDashboard'
import AdminDashboard from './pages/AdminDashboard'
import ClaimsPage from './pages/ClaimsPage'
import PolicyPage from './pages/PolicyPage'
import FraudPanel from './pages/FraudPanel'
import DisruptionsPage from './pages/DisruptionsPage'

export default function App() {
  const [isAuth, setIsAuth] = useState(api.isAuthenticated())
  const [user, setUser] = useState(api.getUser())
  const [activePage, setActivePage] = useState('dashboard')

  const handleLogin = (authData) => {
    api.setAuth(authData)
    setIsAuth(true)
    setUser(api.getUser())
  }

  const handleLogout = () => {
    api.logout()
    setIsAuth(false)
    setUser(null)
  }

  if (!isAuth) {
    return <LoginPage onLogin={handleLogin} />
  }

  const isAdmin = user?.role === 'admin'

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard':
        return isAdmin ? <AdminDashboard /> : <WorkerDashboard />
      case 'claims':
        return <ClaimsPage isAdmin={isAdmin} />
      case 'policy':
        return <PolicyPage />
      case 'fraud':
        return <FraudPanel />
      case 'disruptions':
        return <DisruptionsPage />
      default:
        return isAdmin ? <AdminDashboard /> : <WorkerDashboard />
    }
  }

  return (
    <div className="app-layout">
      <Sidebar
        user={user}
        isAdmin={isAdmin}
        activePage={activePage}
        onNavigate={setActivePage}
        onLogout={handleLogout}
      />
      <main className="main-content">
        {renderPage()}
      </main>
    </div>
  )
}
