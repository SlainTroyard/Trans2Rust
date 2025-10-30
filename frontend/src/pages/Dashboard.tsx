import React from 'react'
import { Link } from 'react-router-dom'
import { Play, FolderOpen, Settings, BarChart3, Sparkles, Zap, ArrowRight, Code2 } from 'lucide-react'

export function Dashboard() {
  const stats = [
    { label: 'Total Projects', value: '12', icon: FolderOpen, color: 'blue', gradient: 'from-blue-500 to-blue-600', bgGradient: 'from-blue-50 to-blue-100' },
    { label: 'Translations Completed', value: '48', icon: BarChart3, color: 'green', gradient: 'from-green-500 to-green-600', bgGradient: 'from-green-50 to-emerald-100' },
    { label: 'Success Rate', value: '94%', icon: Sparkles, color: 'purple', gradient: 'from-purple-500 to-purple-600', bgGradient: 'from-purple-50 to-violet-100' },
    { label: 'Active Sessions', value: '2', icon: Zap, color: 'orange', gradient: 'from-orange-500 to-orange-600', bgGradient: 'from-orange-50 to-amber-100' },
  ]
  
  const recentProjects = [
    { name: 'Simple Calculator', status: 'Completed', progress: 100, lastModified: '2 hours ago', files: 8 },
    { name: 'Data Structures', status: 'In Progress', progress: 75, lastModified: '1 day ago', files: 15 },
    { name: 'Network Library', status: 'Pending', progress: 0, lastModified: '3 days ago', files: 24 },
  ]
  
  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="relative bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-700 rounded-2xl p-8 text-white shadow-2xl overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmZmZmYiIGZpbGwtb3BhY2l0eT0iMC4xIj48Y2lyY2xlIGN4PSIzMCIgY3k9IjMwIiByPSIyIi8+PC9nPjwvZz48L3N2Zz4=')] opacity-20"></div>
        <div className="relative z-10">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-5xl font-extrabold mb-3 drop-shadow-lg">Dashboard</h1>
              <p className="text-blue-100 text-xl font-medium">Welcome to Trans2Rust - Advanced C/C++ to Rust Translation</p>
            </div>
            <div className="hidden lg:block">
              <div className="p-6 bg-white/20 backdrop-blur-sm rounded-2xl border border-white/30 animate-float shadow-2xl">
                <Code2 className="h-16 w-16 text-white drop-shadow-lg" />
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map(({ label, value, icon: Icon, gradient, bgGradient }, index) => (
          <div 
            key={label} 
            className={`relative bg-gradient-to-br ${bgGradient} rounded-2xl shadow-xl border-2 border-white/50 p-6 hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 group overflow-hidden`}
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16 blur-2xl"></div>
            <div className="relative z-10 flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-gray-700 mb-2 uppercase tracking-wide">{label}</p>
                <p className="text-4xl font-extrabold text-gray-900">{value}</p>
              </div>
              <div className={`p-5 rounded-2xl bg-gradient-to-br ${gradient} shadow-xl group-hover:scale-110 transition-transform duration-300`}>
                <Icon className="h-7 w-7 text-white" />
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Quick Actions - 横向排列 */}
      <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-2xl border-2 border-gray-200/50 p-8">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <div className="p-2 bg-gradient-to-br from-purple-500 to-violet-600 rounded-xl mr-3 shadow-lg">
              <Sparkles className="h-6 w-6 text-white" />
            </div>
            Quick Actions
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Link
            to="/translate"
            className="group relative flex flex-col items-center justify-center p-8 rounded-2xl border-2 border-blue-400 bg-gradient-to-br from-blue-50 via-blue-100 to-indigo-100 hover:from-blue-100 hover:via-blue-200 hover:to-indigo-200 transition-all duration-300 shadow-lg hover:shadow-2xl hover:-translate-y-1 overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/0 to-indigo-600/0 group-hover:from-blue-500/10 group-hover:to-indigo-600/10 transition-all duration-300"></div>
            <div className="relative z-10 p-5 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl mb-5 group-hover:scale-110 group-hover:rotate-3 transition-all duration-300 shadow-xl">
              <Play className="h-10 w-10 text-white" />
            </div>
            <span className="relative z-10 font-bold text-lg text-gray-900 text-center mb-1">Start Translation</span>
            <span className="relative z-10 text-xs text-gray-600 font-medium">开始新的翻译任务</span>
            <ArrowRight className="absolute bottom-4 right-4 h-5 w-5 text-blue-600 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300" />
          </Link>
          
          <Link
            to="/projects"
            className="group relative flex flex-col items-center justify-center p-8 rounded-2xl border-2 border-green-400 bg-gradient-to-br from-green-50 via-emerald-100 to-teal-100 hover:from-green-100 hover:via-emerald-200 hover:to-teal-200 transition-all duration-300 shadow-lg hover:shadow-2xl hover:-translate-y-1 overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-green-500/0 to-emerald-600/0 group-hover:from-green-500/10 group-hover:to-emerald-600/10 transition-all duration-300"></div>
            <div className="relative z-10 p-5 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl mb-5 group-hover:scale-110 group-hover:rotate-3 transition-all duration-300 shadow-xl">
              <FolderOpen className="h-10 w-10 text-white" />
            </div>
            <span className="relative z-10 font-bold text-lg text-gray-900 text-center mb-1">Browse Projects</span>
            <span className="relative z-10 text-xs text-gray-600 font-medium">浏览项目列表</span>
            <ArrowRight className="absolute bottom-4 right-4 h-5 w-5 text-green-600 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300" />
          </Link>
          
          <Link
            to="/settings"
            className="group relative flex flex-col items-center justify-center p-8 rounded-2xl border-2 border-purple-400 bg-gradient-to-br from-purple-50 via-violet-100 to-fuchsia-100 hover:from-purple-100 hover:via-violet-200 hover:to-fuchsia-200 transition-all duration-300 shadow-lg hover:shadow-2xl hover:-translate-y-1 overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-purple-500/0 to-violet-600/0 group-hover:from-purple-500/10 group-hover:to-violet-600/10 transition-all duration-300"></div>
            <div className="relative z-10 p-5 bg-gradient-to-br from-purple-500 to-violet-600 rounded-2xl mb-5 group-hover:scale-110 group-hover:rotate-3 transition-all duration-300 shadow-xl">
              <Settings className="h-10 w-10 text-white" />
            </div>
            <span className="relative z-10 font-bold text-lg text-gray-900 text-center mb-1">Settings</span>
            <span className="relative z-10 text-xs text-gray-600 font-medium">配置系统设置</span>
            <ArrowRight className="absolute bottom-4 right-4 h-5 w-5 text-purple-600 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300" />
          </Link>
        </div>
      </div>
      
      {/* Recent Projects - 横向排列 */}
      <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-2xl border-2 border-gray-200/50 p-8">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <div className="p-2 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl mr-3 shadow-lg">
              <FolderOpen className="h-6 w-6 text-white" />
            </div>
            Recent Projects
          </h2>
          <Link to="/projects" className="text-sm text-blue-600 hover:text-blue-700 font-semibold flex items-center">
            View All <ArrowRight className="h-4 w-4 ml-1" />
          </Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {recentProjects.map((project, index) => (
            <div 
              key={project.name} 
              className={`group relative flex flex-col p-6 rounded-2xl border-2 hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 overflow-hidden ${
                project.status === 'Completed' ? 'border-green-400 bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50' :
                project.status === 'In Progress' ? 'border-blue-400 bg-gradient-to-br from-blue-50 via-indigo-50 to-cyan-50' : 
                'border-gray-300 bg-gradient-to-br from-gray-50 via-slate-50 to-zinc-50'
              }`}
            >
              {/* Decorative background element */}
              <div className={`absolute top-0 right-0 w-24 h-24 rounded-full -mr-12 -mt-12 blur-3xl opacity-30 ${
                project.status === 'Completed' ? 'bg-green-400' :
                project.status === 'In Progress' ? 'bg-blue-400' : 'bg-gray-400'
              }`}></div>
              
              <div className="relative z-10">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className={`inline-block p-2 rounded-xl mb-3 ${
                      project.status === 'Completed' ? 'bg-green-100' :
                      project.status === 'In Progress' ? 'bg-blue-100' : 'bg-gray-100'
                    }`}>
                      <FolderOpen className={`h-5 w-5 ${
                        project.status === 'Completed' ? 'text-green-600' :
                        project.status === 'In Progress' ? 'text-blue-600' : 'text-gray-600'
                      }`} />
                    </div>
                    <h3 className="font-bold text-xl text-gray-900 mb-2">{project.name}</h3>
                    <p className="text-sm text-gray-600 mb-3 flex items-center">
                      <span className="inline-block w-2 h-2 rounded-full bg-gray-400 mr-2"></span>
                      {project.lastModified}
                    </p>
                    <p className="text-xs text-gray-500 font-medium mb-4">{project.files} files</p>
                  </div>
                  <span className={`text-xs font-bold px-3 py-1.5 rounded-full shadow-md ${
                    project.status === 'Completed' ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white' :
                    project.status === 'In Progress' ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white' : 
                    'bg-gradient-to-r from-gray-400 to-gray-500 text-white'
                  }`}>
                    {project.status}
                  </span>
                </div>
                
                {project.progress > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Progress</span>
                      <span className="text-sm font-bold text-gray-900">{project.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200/80 rounded-full h-4 shadow-inner overflow-hidden">
                      <div
                        className={`h-4 rounded-full transition-all duration-500 ${
                          project.status === 'Completed' ? 'bg-gradient-to-r from-green-500 via-emerald-500 to-teal-500' :
                          'bg-gradient-to-r from-blue-500 via-indigo-500 to-cyan-500'
                        } shadow-sm`}
                        style={{ width: `${project.progress}%` }}
                      />
                    </div>
                  </div>
                )}
                
                {project.progress === 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="w-full bg-gray-200/50 rounded-full h-2">
                      <div className="w-0 h-2 rounded-full bg-gray-400"></div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* System Status */}
      <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-2xl border-2 border-gray-200/50 p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-8 flex items-center">
          <div className="p-2 bg-gradient-to-br from-yellow-500 to-orange-600 rounded-xl mr-3 shadow-lg">
            <Zap className="h-6 w-6 text-white" />
          </div>
          System Status
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="relative text-center p-8 rounded-2xl bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 border-2 border-green-300 shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 group overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-green-400/20 rounded-full -mr-16 -mt-16 blur-2xl group-hover:bg-green-400/30 transition-all"></div>
            <div className="relative z-10">
              <div className="inline-block p-4 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl mb-4 shadow-xl group-hover:scale-110 transition-transform">
                <div className="w-4 h-4 bg-white rounded-full animate-pulse"></div>
              </div>
              <div className="text-4xl font-extrabold text-green-600 mb-2">Online</div>
              <div className="text-sm text-green-700 font-semibold uppercase tracking-wide">Translation Service</div>
            </div>
          </div>
          
          <div className="relative text-center p-8 rounded-2xl bg-gradient-to-br from-blue-50 via-indigo-50 to-cyan-50 border-2 border-blue-300 shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 group overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-400/20 rounded-full -mr-16 -mt-16 blur-2xl group-hover:bg-blue-400/30 transition-all"></div>
            <div className="relative z-10">
              <div className="inline-block p-4 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl mb-4 shadow-xl group-hover:scale-110 transition-transform">
                <BarChart3 className="h-6 w-6 text-white" />
              </div>
              <div className="text-4xl font-extrabold text-blue-600 mb-2">5</div>
              <div className="text-sm text-blue-700 font-semibold uppercase tracking-wide">Active Agents</div>
            </div>
          </div>
          
          <div className="relative text-center p-8 rounded-2xl bg-gradient-to-br from-purple-50 via-violet-50 to-fuchsia-50 border-2 border-purple-300 shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 group overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-purple-400/20 rounded-full -mr-16 -mt-16 blur-2xl group-hover:bg-purple-400/30 transition-all"></div>
            <div className="relative z-10">
              <div className="inline-block p-4 bg-gradient-to-br from-purple-500 to-violet-600 rounded-2xl mb-4 shadow-xl group-hover:scale-110 transition-transform">
                <Sparkles className="h-6 w-6 text-white" />
              </div>
              <div className="text-4xl font-extrabold text-purple-600 mb-2">2.1s</div>
              <div className="text-sm text-purple-700 font-semibold uppercase tracking-wide">Avg Response Time</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
