import { Routes, Route } from 'react-router-dom'
import { RouteTransition } from './components/RouteTransition'
import HomePage from './pages/HomePage'
import AboutPage from './pages/AboutPage'
import DashboardPage from './pages/DashboardPage'
import ProfilePage from './pages/ProfilePage'

function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <RouteTransition>
            <HomePage />
          </RouteTransition>
        }
      />
      <Route
        path="/about"
        element={
          <RouteTransition>
            <AboutPage />
          </RouteTransition>
        }
      />
      <Route
        path="/dashboard"
        element={
          <RouteTransition>
            <DashboardPage />
          </RouteTransition>
        }
      />
      <Route
        path="/profile"
        element={
          <RouteTransition>
            <ProfilePage />
          </RouteTransition>
        }
      />
    </Routes>
  )
}

export default App