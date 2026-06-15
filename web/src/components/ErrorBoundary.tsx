import { Component, type ReactNode } from 'react'

// Surfaces render errors instead of blanking the page, and prints them to the
// console for debugging.
export default class ErrorBoundary extends Component<
  { children: ReactNode },
  { error: Error | null }
> {
  state = { error: null as Error | null }

  static getDerivedStateFromError(error: Error) {
    return { error }
  }

  componentDidCatch(error: Error) {
    console.error('UI error:', error)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="p-6 text-red-300">
          <h1 className="font-bold mb-2">Something went wrong</h1>
          <pre className="text-sm whitespace-pre-wrap text-red-400">
            {this.state.error.message}
            {'\n'}
            {this.state.error.stack}
          </pre>
        </div>
      )
    }
    return this.props.children
  }
}
