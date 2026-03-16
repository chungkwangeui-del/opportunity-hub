"use client";

import Link from "next/link";
import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[50vh] flex-col items-center justify-center px-6 py-16">
          <div className="max-w-md rounded-xl border border-red-200 bg-red-50 p-8 text-center">
            <h2 className="text-xl font-bold text-red-800">Something went wrong</h2>
            <p className="mt-2 text-sm text-red-600">
              An unexpected error occurred. Please try again.
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <button
                onClick={() => this.setState({ hasError: false })}
                className="rounded-full bg-red-600 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-red-700"
              >
                Try again
              </button>
              <Link
                href="/"
                className="rounded-full border border-red-600 px-6 py-2.5 text-sm font-medium text-red-600 transition-colors hover:bg-red-100"
              >
                Go home
              </Link>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
