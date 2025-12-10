import { Activity, LayoutDashboard, FileCode } from 'lucide-react'

interface HeaderProps {
  activeView: 'dashboard' | 'review'
  onViewChange: (view: 'dashboard' | 'review') => void
}

export default function Header({ activeView, onViewChange }: HeaderProps) {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Workflow Engine</h1>
              <p className="text-xs text-gray-500">Mini-LangGraph</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex space-x-2">
            <NavButton
              icon={<LayoutDashboard className="w-4 h-4" />}
              label="Dashboard"
              active={activeView === 'dashboard'}
              onClick={() => onViewChange('dashboard')}
            />
            <NavButton
              icon={<FileCode className="w-4 h-4" />}
              label="Code Review"
              active={activeView === 'review'}
              onClick={() => onViewChange('review')}
            />
          </nav>

          {/* Status */}
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-sm text-gray-600">Connected</span>
          </div>
        </div>
      </div>
    </header>
  )
}

interface NavButtonProps {
  icon: React.ReactNode
  label: string
  active: boolean
  onClick: () => void
}

function NavButton({ icon, label, active, onClick }: NavButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${
        active
          ? 'bg-primary-100 text-primary-700'
          : 'text-gray-600 hover:bg-gray-100'
      }`}
    >
      {icon}
      <span className="text-sm font-medium">{label}</span>
    </button>
  )
}
