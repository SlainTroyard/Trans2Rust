import React, { useState } from 'react'
import { Play, Pause, Square, FolderOpen, FileCode } from 'lucide-react'

export function TranslationPage() {
  const [projectPath, setProjectPath] = useState('')
  const [outputPath, setOutputPath] = useState('')
  const [isTranslating, setIsTranslating] = useState(false)
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState<string>('idle')
  
  const handleStartTranslation = async () => {
    if (!projectPath) {
      alert('Please enter a project path')
      return
    }
    
    setIsTranslating(true)
    setStatus('translating')
    setProgress(0)
    
    try {
      // TODO: Call actual API
      // const response = await fetch('/api/translate', { ... })
      
      // Simulate progress
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 100) {
            clearInterval(interval)
            setIsTranslating(false)
            setStatus('completed')
            return 100
          }
          return prev + 10
        })
      }, 500)
    } catch (error) {
      console.error('Translation failed:', error)
      setIsTranslating(false)
      setStatus('error')
    }
  }
  
  const handlePause = () => {
    setIsTranslating(false)
    setStatus('paused')
  }
  
  const handleResume = () => {
    setIsTranslating(true)
    setStatus('translating')
  }
  
  const handleStop = () => {
    setIsTranslating(false)
    setStatus('stopped')
  }
  
  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-xl p-8 text-white shadow-xl">
        <h1 className="text-4xl font-bold mb-2">Translation</h1>
        <p className="text-blue-100 text-lg">Translate C/C++ projects to Rust</p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Translation Form */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
            <FolderOpen className="h-5 w-5 mr-2 text-blue-600" />
            Project Configuration
          </h2>
          
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                <FolderOpen className="h-4 w-4 inline mr-2 text-blue-600" />
                Source Project Path
              </label>
              <input
                type="text"
                value={projectPath}
                onChange={(e) => setProjectPath(e.target.value)}
                placeholder="e.g., input/01-Primary"
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all font-mono bg-gray-50"
                disabled={isTranslating}
              />
            </div>
            
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                <FileCode className="h-4 w-4 inline mr-2 text-indigo-600" />
                Output Path (optional)
              </label>
              <input
                type="text"
                value={outputPath}
                onChange={(e) => setOutputPath(e.target.value)}
                placeholder="e.g., output/01-Primary"
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all font-mono bg-gray-50"
                disabled={isTranslating}
              />
            </div>
            
            <div className="flex items-center space-x-3 pt-4">
              {!isTranslating ? (
                <button
                  onClick={handleStartTranslation}
                  className="flex items-center space-x-2 px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all shadow-lg hover:shadow-xl font-semibold"
                >
                  <Play className="h-5 w-5" />
                  <span>Start Translation</span>
                </button>
              ) : (
                <>
                  <button
                    onClick={handlePause}
                    className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-yellow-500 to-orange-600 text-white rounded-xl hover:from-yellow-600 hover:to-orange-700 transition-all shadow-lg font-semibold"
                  >
                    <Pause className="h-5 w-5" />
                    <span>Pause</span>
                  </button>
                  <button
                    onClick={handleStop}
                    className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-xl hover:from-red-600 hover:to-red-700 transition-all shadow-lg font-semibold"
                  >
                    <Square className="h-5 w-5" />
                    <span>Stop</span>
                  </button>
                </>
              )}
              {status === 'paused' && (
                <button
                  onClick={handleResume}
                  className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl hover:from-green-600 hover:to-emerald-700 transition-all shadow-lg font-semibold"
                >
                  <Play className="h-5 w-5" />
                  <span>Resume</span>
                </button>
              )}
            </div>
          </div>
        </div>
        
        {/* Progress Section */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg mr-2">
              <FileCode className="h-5 w-5 text-blue-600" />
            </div>
            Translation Progress
          </h2>
          
          <div className="space-y-6">
            <div>
              <div className="flex justify-between items-center mb-3">
                <span className="text-sm font-semibold text-gray-700">Status</span>
                <span className={`text-sm font-bold px-4 py-1.5 rounded-full ${
                  status === 'completed' ? 'bg-green-100 text-green-700' :
                  status === 'translating' ? 'bg-blue-100 text-blue-700' :
                  status === 'error' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'
                }`}>
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-4 shadow-inner">
                <div
                  className={`h-4 rounded-full transition-all shadow-sm ${
                    status === 'completed' ? 'bg-gradient-to-r from-green-500 to-emerald-600' :
                    status === 'translating' ? 'bg-gradient-to-r from-blue-500 to-indigo-600' : 'bg-gray-400'
                  }`}
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-sm text-gray-600 mt-3 font-semibold">{progress}% complete</p>
            </div>
            
            {status === 'translating' && (
              <div className="p-5 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border-2 border-blue-200">
                <p className="text-sm text-blue-800 font-medium">
                  Translation in progress... Please wait.
                </p>
              </div>
            )}
            
            {status === 'completed' && (
              <div className="p-5 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border-2 border-green-200">
                <p className="text-sm text-green-800 font-medium">
                  Translation completed successfully! ✓
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

