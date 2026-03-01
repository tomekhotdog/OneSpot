import { Component } from 'react'

export default class ErrorBoundary extends Component {
  state = { hasError: false, error: null }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 text-center">
          <h2 className="text-title-section font-bold text-accent-red mb-2">Something went wrong</h2>
          <p className="text-text-secondary mb-4">{this.state.error?.message}</p>
          <button
            onClick={() => { this.setState({ hasError: false }); window.location.reload() }}
            className="px-4 py-2 bg-primary text-white rounded-button"
          >
            Try Again
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
