import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { PermissionProvider } from './context/PermissionContext'

const API_BASE = import.meta.env.DEV ? "http://localhost:5000" : window.location.origin;

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <PermissionProvider API_BASE={API_BASE}>
      <App />
    </PermissionProvider>
  </StrictMode>,
)
