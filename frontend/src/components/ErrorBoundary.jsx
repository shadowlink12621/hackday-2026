import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="notice notice-error" style={{ margin: '2rem' }}>
          <div>
            <strong>UI Render Error</strong>
            <p style={{ margin: '4px 0 0' }}>Something went wrong while rendering the dashboard. Please refresh.</p>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
