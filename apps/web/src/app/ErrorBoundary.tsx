/** Error boundary for panel trees only — never around the scene (a remount would recreate the viewer). */
import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props { name: string; children: ReactNode }
interface State { error: Error | null }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error(`[${this.props.name}]`, error, info.componentStack);
  }

  render(): ReactNode {
    if (this.state.error) {
      return (
        <section className="panel panel-error" role="alert">
          <p className="error">{this.props.name} failed to render: {this.state.error.message}</p>
          <button type="button" className="link-button" onClick={() => this.setState({ error: null })}>retry</button>
        </section>
      );
    }
    return this.props.children;
  }
}
