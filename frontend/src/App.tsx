import { useState } from 'react'
import Dashboard from './components/Dashboard'
import Header from './components/Header'
import CodeReviewForm from './components/CodeReviewForm'

function App() {
  const [activeView, setActiveView] = useState<'dashboard' | 'review'>('dashboard')

  return (
    <div className="min-h-screen bg-gray-50">
      <Header activeView={activeView} onViewChange={setActiveView} />

      <main className="container mx-auto px-4 py-8">
        <div className={activeView === 'dashboard' ? '' : 'hidden'}>
          <Dashboard />
        </div>
        <div className={activeView === 'review' ? '' : 'hidden'}>
          <CodeReviewForm />
        </div>
      </main>
    </div>
  )
}

export default App
