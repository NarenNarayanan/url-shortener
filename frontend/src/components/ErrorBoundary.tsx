import { Component, type ErrorInfo, type ReactNode } from "react";
import { Button } from "@/components/ui/button";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
}

// React error boundaries must be class components — there's no hook
// equivalent (as of React 18/19) for catching render errors in children.
// Without this, any uncaught error anywhere in the tree unmounts the whole
// app, leaving a blank white page with nothing telling the user (or us)
// what happened.
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught render error:", error, errorInfo);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-3 px-4 text-center">
          <p className="text-lg font-medium">Something went wrong</p>
          <p className="max-w-md text-sm text-muted-foreground">{this.state.error.message}</p>
          <Button onClick={() => window.location.assign("/")}>Go home</Button>
        </div>
      );
    }

    return this.props.children;
  }
}
