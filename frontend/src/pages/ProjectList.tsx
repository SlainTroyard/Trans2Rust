import React from 'react'
import { Link } from 'react-router-dom'
import { FolderOpen, Clock, CheckCircle, XCircle } from 'lucide-react'

export function ProjectList() {
  const projects = [
    { 
      id: '1', 
      name: 'Simple Calculator', 
      path: '/input/01-Primary',
      status: 'completed', 
      files: 8, 
      progress: 100,
      lastModified: '2024-01-15 10:30'
    },
    { 
      id: '2', 
      name: 'Data Structures', 
      path: '/input/02-Medium',
      status: 'in-progress', 
      files: 15, 
      progress: 75,
      lastModified: '2024-01-16 14:20'
    },
    { 
      id: '3', 
      name: 'Network Library', 
      path: '/input/03-Advanced',
      status: 'pending', 
      files: 24, 
      progress: 0,
      lastModified: '2024-01-10 09:15'
    },
  ]
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'in-progress':
        return <Clock className="h-5 w-5 text-blue-600" />
      case 'pending':
        return <XCircle className="h-5 w-5 text-gray-600" />
      default:
        return null
    }
  }
  
  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Completed'
      case 'in-progress':
        return 'In Progress'
      case 'pending':
        return 'Pending'
      default:
        return status
    }
  }
  
  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-xl p-8 text-white shadow-xl">
        <h1 className="text-4xl font-bold mb-2">Projects</h1>
        <p className="text-blue-100 text-lg">Manage and monitor your translation projects</p>
      </div>
      
      <div className="grid gap-6">
        {projects.map((project) => (
          <div key={project.id} className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 hover:shadow-xl transition-all duration-300">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-5 flex-1">
                <div className={`p-4 rounded-xl ${
                  project.status === 'completed' ? 'bg-gradient-to-br from-green-500 to-emerald-600' :
                  project.status === 'in-progress' ? 'bg-gradient-to-br from-blue-500 to-indigo-600' : 
                  'bg-gradient-to-br from-gray-400 to-gray-500'
                } shadow-lg`}>
                  <FolderOpen className="h-6 w-6 text-white" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-xl font-bold text-gray-900">{project.name}</h3>
                    <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${
                      project.status === 'completed' ? 'bg-green-100' :
                      project.status === 'in-progress' ? 'bg-blue-100' : 'bg-gray-100'
                    }`}>
                      {getStatusIcon(project.status)}
                      <span className={`text-sm font-semibold ${
                        project.status === 'completed' ? 'text-green-700' :
                        project.status === 'in-progress' ? 'text-blue-700' : 'text-gray-700'
                      }`}>
                        {getStatusLabel(project.status)}
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 font-mono bg-gray-50 px-3 py-1 rounded-lg inline-block mb-2">{project.path}</p>
                  <div className="flex items-center space-x-6 mt-3 text-sm">
                    <span className="text-gray-600 font-medium">{project.files} files</span>
                    <span className="text-gray-500">Last modified: {project.lastModified}</span>
                  </div>
                  {project.progress > 0 && (
                    <div className="mt-4">
                      <div className="w-full bg-gray-200 rounded-full h-3 shadow-inner">
                        <div
                          className="bg-gradient-to-r from-blue-500 to-indigo-600 h-3 rounded-full transition-all shadow-sm"
                          style={{ width: `${project.progress}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-600 mt-2 font-medium">{project.progress}% complete</p>
                    </div>
                  )}
                </div>
              </div>
              
              <div className="flex items-center space-x-2 ml-6">
                <Link
                  to={`/translate?project=${project.path}`}
                  className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all shadow-lg hover:shadow-xl font-semibold"
                >
                  {project.status === 'completed' ? 'View' : project.status === 'in-progress' ? 'Resume' : 'Start'}
                </Link>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

