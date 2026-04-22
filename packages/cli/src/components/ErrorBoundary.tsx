import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Box, Text } from 'ink';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('CLI Error:', error);
    console.error('Component stack:', errorInfo.componentStack);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <Box flexDirection="column" padding={1}>
          <Text color="red" bold>
            ❌ CLI 遇到错误
          </Text>
          <Text color="red">
            {this.state.error?.message || 'Unknown error'}
          </Text>
          <Text dimColor>
            请尝试重新启动 CLI
          </Text>
        </Box>
      );
    }

    return this.props.children;
  }
}
