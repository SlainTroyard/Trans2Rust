import React, { useState } from 'react'
import { Save, Key, Server, Cpu } from 'lucide-react'

export function Settings() {
  const [settings, setSettings] = useState({
    apiProvider: 'openai',
    apiKey: '',
    baseUrl: 'https://api.openai.com/v1',
    modelName: 'deepseek-chat',
    maxParallelWorkers: '5',
    enableQualityCheck: true,
    enableMemory: true,
  })
  
  const [saved, setSaved] = useState(false)
  
  const handleSave = () => {
    // TODO: Save settings to backend
    localStorage.setItem('trans2rust-settings', JSON.stringify(settings))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }
  
  const handleChange = (key: string, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }))
    setSaved(false)
  }
  
  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-xl p-8 text-white shadow-xl">
        <h1 className="text-4xl font-bold mb-2">Settings</h1>
        <p className="text-blue-100 text-lg">Configure Trans2Rust translation parameters</p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Model Configuration */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg mr-3">
              <Server className="h-5 w-5 text-blue-600" />
            </div>
            Model Configuration
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                API Provider
              </label>
              <select
                value={settings.apiProvider}
                onChange={(e) => handleChange('apiProvider', e.target.value)}
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-gray-50 font-medium"
              >
                <option value="openai">OpenAI / DeepSeek</option>
                <option value="anthropic">Anthropic</option>
                <option value="zhipu">智谱AI</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Key className="h-4 w-4 inline mr-2" />
                API Key
              </label>
              <input
                type="password"
                value={settings.apiKey}
                onChange={(e) => handleChange('apiKey', e.target.value)}
                placeholder="Enter your API key"
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-gray-50 font-mono"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Base URL
              </label>
              <input
                type="text"
                value={settings.baseUrl}
                onChange={(e) => handleChange('baseUrl', e.target.value)}
                placeholder="https://api.openai.com/v1"
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-gray-50 font-mono"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Model Name
              </label>
              <input
                type="text"
                value={settings.modelName}
                onChange={(e) => handleChange('modelName', e.target.value)}
                placeholder="deepseek-chat"
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-gray-50 font-medium"
              />
            </div>
          </div>
        </div>
        
        {/* Translation Settings */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
            <div className="p-2 bg-indigo-100 rounded-lg mr-3">
              <Cpu className="h-5 w-5 text-indigo-600" />
            </div>
            Translation Settings
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Parallel Workers
              </label>
              <input
                type="number"
                value={settings.maxParallelWorkers}
                onChange={(e) => handleChange('maxParallelWorkers', e.target.value)}
                min="1"
                max="20"
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-gray-50 font-medium"
              />
              <p className="text-xs text-gray-500 mt-1">Number of parallel translation tasks</p>
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Enable Quality Check
                </label>
                <p className="text-xs text-gray-500">Automatically verify translation quality</p>
              </div>
              <input
                type="checkbox"
                checked={settings.enableQualityCheck}
                onChange={(e) => handleChange('enableQualityCheck', e.target.checked)}
                className="h-5 w-5 text-blue-600 rounded focus:ring-blue-500"
              />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Enable Memory
                </label>
                <p className="text-xs text-gray-500">Save translation experience for reuse</p>
              </div>
              <input
                type="checkbox"
                checked={settings.enableMemory}
                onChange={(e) => handleChange('enableMemory', e.target.checked)}
                className="h-5 w-5 text-blue-600 rounded focus:ring-blue-500"
              />
            </div>
            
            <button
              onClick={handleSave}
              className={`w-full flex items-center justify-center space-x-2 px-6 py-4 rounded-xl transition-all shadow-lg hover:shadow-xl font-semibold ${
                saved
                  ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white'
                  : 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700'
              }`}
            >
              <Save className="h-5 w-5" />
              <span>{saved ? 'Saved!' : 'Save Settings'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

