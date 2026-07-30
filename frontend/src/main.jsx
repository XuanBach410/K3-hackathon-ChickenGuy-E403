import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import DecisionWorkspace from './DecisionWorkspace.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <DecisionWorkspace />
  </StrictMode>,
)
