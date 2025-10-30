import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Code2, Settings, Home, FolderOpen } from 'lucide-react'

export function Header() {
  const location = useLocation()
  
  const navItems = [
    { path: '/', label: 'Dashboard', icon: Home },
    { path: '/projects', label: 'Projects', icon: FolderOpen },
    { path: '/translate', label: 'Translate', icon: Code2 },
    { path: '/settings', label: 'Settings', icon: Settings },
  ]
  
  return (
    <header className="bg-gradient-to-r from-blue-600 to-indigo-700 shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-8">
            <Link to="/" className="flex items-center space-x-3 group">
              <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm group-hover:bg-white/30 transition-all">
                <Code2 className="h-6 w-6 text-white" />
              </div>
              <span className="text-xl font-bold text-white">Trans2Rust</span>
            </Link>
            
            <nav className="hidden md:flex space-x-2">
              {navItems.map(({ path, label, icon: Icon }) => (
                <Link
                  key={path}
                  to={path}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    location.pathname === path
                      ? 'bg-white/20 text-white shadow-md backdrop-blur-sm'
                      : 'text-white/80 hover:text-white hover:bg-white/10'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{label}</span>
                </Link>
              ))}
            </nav>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="hidden lg:block px-3 py-1.5 bg-white/20 rounded-lg backdrop-blur-sm">
              <span className="text-sm text-white/90 font-medium">Multi-Agent System</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
