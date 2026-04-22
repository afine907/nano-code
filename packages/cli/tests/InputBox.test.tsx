import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import React from 'react';
import { render } from 'ink-testing-library';
import { InputBox } from '../src/components/InputBox.js';
import type { Mode } from '../src/app.js';

// Mock useInput to test interaction
vi.mock('ink', async () => {
  const actual = await vi.importActual('ink');
  return {
    ...actual,
    useInput: vi.fn(),
  };
});

import { useInput } from 'ink';

describe('InputBox', () => {
  let inputHandler: ((char: string, key: any) => void) | null = null;
  let mockExit: ReturnType<typeof vi.fn>;
  
  beforeEach(() => {
    vi.clearAllMocks();
    mockExit = vi.fn();
    
    // 捕获 useInput 的回调
    (useInput as any).mockImplementation((handler, options) => {
      inputHandler = handler;
    });
  });
  
  afterEach(() => {
    inputHandler = null;
  });

  describe('Rendering', () => {
    it('renders prompt icon', () => {
      const onSubmit = vi.fn();
      const onToggleMode = vi.fn();
      
      const { lastFrame } = render(
        <InputBox 
          onSubmit={onSubmit}
          disabled={false}
          mode="build"
          onToggleMode={onToggleMode}
          model="gpt-4o-mini"
        />
      );
      
      expect(lastFrame()).toContain('🦞');
    });

    it('renders plan mode icon', () => {
      const onSubmit = vi.fn();
      const onToggleMode = vi.fn();
      
      const { lastFrame } = render(
        <InputBox 
          onSubmit={onSubmit}
          disabled={false}
          mode="plan"
          onToggleMode={onToggleMode}
          model="gpt-4o-mini"
        />
      );
      
      expect(lastFrame()).toContain('📋');
    });

    it('shows help hint when empty', () => {
      const onSubmit = vi.fn();
      const onToggleMode = vi.fn();
      
      const { lastFrame } = render(
        <InputBox 
          onSubmit={onSubmit}
          disabled={false}
          mode="build"
          onToggleMode={onToggleMode}
          model="gpt-4o-mini"
        />
      );
      
      expect(lastFrame()).toContain('/help');
    });

    it('shows model name', () => {
      const onSubmit = vi.fn();
      const onToggleMode = vi.fn();
      
      const { lastFrame } = render(
        <InputBox 
          onSubmit={onSubmit}
          disabled={false}
          mode="build"
          onToggleMode={onToggleMode}
          model="gpt-4o-mini"
        />
      );
      
      expect(lastFrame()).toContain('gpt-4o-mini');
    });

    it('shows loading state when disabled', () => {
      const onSubmit = vi.fn();
      const onToggleMode = vi.fn();
      
      const { lastFrame } = render(
        <InputBox 
          onSubmit={onSubmit}
          disabled={true}
          mode="build"
          onToggleMode={onToggleMode}
          model="gpt-4o-mini"
        />
      );
      
      expect(lastFrame()).toContain('...');
    });
  });

  describe('Input Handling', () => {
    it('handles character input', () => {
      const onSubmit = vi.fn();
      const onToggleMode = vi.fn();
      
      render(
        <InputBox 
          onSubmit={onSubmit}
          disabled={false}
          mode="build"
          onToggleMode={onToggleMode}
          model="gpt-4o-mini"
        />
      );
      
      // 模拟用户输入
      if (inputHandler) {
        inputHandler('h', { ctrl: false, meta: false, shift: false });
        inputHandler('i', { ctrl: false, meta: false, shift: false });
      }
    });

    it('ignores input when disabled', () => {
      const onSubmit = vi.fn();
      const onToggleMode = vi.fn();
      
      render(
        <InputBox 
          onSubmit={onSubmit}
          disabled={true}
          mode="build"
          onToggleMode={onToggleMode}
          model="gpt-4o-mini"
        />
      );
      
      // 当 disabled 时，输入应该被忽略
      if (inputHandler) {
        inputHandler('a', { ctrl: false, meta: false, shift: false });
        // 不应该调用 onSubmit
        expect(onSubmit).not.toHaveBeenCalled();
      }
    });

    it('handles Enter to submit', () => {
      const onSubmit = vi.fn();
      const onToggleMode = vi.fn();
      
      render(
        <InputBox 
          onSubmit={onSubmit}
          disabled={false}
          mode="build"
          onToggleMode={onToggleMode}
          model="gpt-4o-mini"
        />
      );
      
      // 先输入一些字符
      if (inputHandler) {
        inputHandler('h', { ctrl: false, meta: false, shift: false });
        inputHandler('i', { ctrl: false, meta: false, shift: false });
        
        // 按 Enter 提交
        inputHandler('', { 
          ctrl: false, 
          meta: false, 
          shift: false, 
          return: true 
        });
        
        expect(onSubmit).toHaveBeenCalledWith('hi');
      }
    });

    it('handles Backspace', () => {
      const onSubmit = vi.fn();
      const onToggleMode = vi.fn();
      
      render(
        <InputBox 
          onSubmit={onSubmit}
          disabled={false}
          mode="build"
          onToggleMode={onToggleMode}
          model="gpt-4o-mini"
        />
      );
      
      if (inputHandler) {
        inputHandler('a', { ctrl: false, meta: false, shift: false });
        inputHandler('b', { ctrl: false, meta: false, shift: false });
        
        // Backspace 删除最后一个字符
        inputHandler('', { 
          ctrl: false, 
          meta: false, 
          shift: false, 
          backspace: true 
        });
        
        // 再提交，应该只有 'a'
        inputHandler('', { 
          ctrl: false, 
          meta: false, 
          shift: false, 
          return: true 
        });
        
        expect(onSubmit).toHaveBeenCalledWith('a');
      }
    });

    it('handles Tab for multiline', () => {
      const onSubmit = vi.fn();
      const onToggleMode = vi.fn();
      
      const { lastFrame } = render(
        <InputBox 
          onSubmit={onSubmit}
          disabled={false}
          mode="build"
          onToggleMode={onToggleMode}
          model="gpt-4o-mini"
        />
      );
      
      if (inputHandler) {
        inputHandler('l', { ctrl: false, meta: false, shift: false });
        inputHandler('1', { ctrl: false, meta: false, shift: false });
        
        // Tab 换行
        inputHandler('', { 
          ctrl: false, 
          meta: false, 
          shift: false, 
          tab: true 
        });
        
        inputHandler('l', { ctrl: false, meta: false, shift: false });
        inputHandler('2', { ctrl: false, meta: false, shift: false });
        
        // Enter 提交
        inputHandler('', { 
          ctrl: false, 
          meta: false, 
          shift: false, 
          return: true 
        });
        
        expect(onSubmit).toHaveBeenCalledWith('l1\nl2');
      }
    });

    it('handles Escape to cancel', () => {
      const onSubmit = vi.fn();
      const onToggleMode = vi.fn();
      
      render(
        <InputBox 
          onSubmit={onSubmit}
          disabled={false}
          mode="build"
          onToggleMode={onToggleMode}
          model="gpt-4o-mini"
        />
      );
      
      if (inputHandler) {
        inputHandler('t', { ctrl: false, meta: false, shift: false });
        inputHandler('e', { ctrl: false, meta: false, shift: false });
        inputHandler('s', { ctrl: false, meta: false, shift: false });
        inputHandler('t', { ctrl: false, meta: false, shift: false });
        
        // Escape 取消
        inputHandler('', { 
          ctrl: false, 
          meta: false, 
          shift: false, 
          escape: true 
        });
        
        // 再按 Enter，不应该提交（因为已被清空）
        inputHandler('', { 
          ctrl: false, 
          meta: false, 
          shift: false, 
          return: true 
        });
        
        expect(onSubmit).not.toHaveBeenCalled();
      }
    });
  });

  describe('Mode Display', () => {
    it('shows BUILD mode', () => {
      const onSubmit = vi.fn();
      const onToggleMode = vi.fn();
      
      const { lastFrame } = render(
        <InputBox 
          onSubmit={onSubmit}
          disabled={false}
          mode="build"
          onToggleMode={onToggleMode}
          model="gpt-4o-mini"
        />
      );
      
      expect(lastFrame()).toContain('BUILD');
    });

    it('shows PLAN mode', () => {
      const onSubmit = vi.fn();
      const onToggleMode = vi.fn();
      
      const { lastFrame } = render(
        <InputBox 
          onSubmit={onSubmit}
          disabled={false}
          mode="plan"
          onToggleMode={onToggleMode}
          model="gpt-4o-mini"
        />
      );
      
      expect(lastFrame()).toContain('PLAN');
    });
  });
});
