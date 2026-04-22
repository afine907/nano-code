import { describe, it, expect } from 'vitest';
import React from 'react';
import { render } from 'ink-testing-library';
import { ChatView } from '../src/components/ChatView.js';
import type { Message } from '../src/app.js';

describe('ChatView', () => {
  it('shows empty state', () => {
    const { lastFrame } = render(<ChatView messages={[]} isLoading={false} />);
    expect(lastFrame()).toContain('输入问题开始对话');
  });

  it('shows loading state', () => {
    const { lastFrame } = render(<ChatView messages={[]} isLoading={true} />);
    expect(lastFrame()).toContain('○');
  });

  it('shows messages', () => {
    const messages: Message[] = [
      {
        id: '1',
        role: 'user',
        content: 'Hello',
        timestamp: new Date(),
      },
    ];
    
    const { lastFrame } = render(<ChatView messages={messages} isLoading={false} />);
    expect(lastFrame()).toContain('Hello');
  });

  it('shows assistant messages', () => {
    const messages: Message[] = [
      {
        id: '2',
        role: 'assistant',
        content: 'Hi there!',
        timestamp: new Date(),
      },
    ];
    
    const { lastFrame } = render(<ChatView messages={messages} isLoading={false} />);
    expect(lastFrame()).toContain('Hi there!');
  });
});
