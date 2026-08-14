import { Component } from "react";

// If the FBX fails to load (bad path, corrupt file, WebGL unavailable),
// this stops the failure from taking down the rest of the dashboard/chat —
// R3F/drei throw inside Suspense, which needs a real error boundary to
// catch, not just a try/catch. Scoped to the avatar only, on purpose.
export default class AvatarErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    // Developer-facing only — the farmer never sees this, just the fallback UI.
    console.error("[Avatar3D] failed to render:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? null;
    }
    return this.props.children;
  }
}
