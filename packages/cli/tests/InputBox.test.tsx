import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { render } from 'ink-testing-library';
import { InputBox } from '../src/components/InputBox.js';
import type { Mode } from '../src/app.js';

// Mock useInput - 测试环境没有真实 TTY
vi.mock('ink', async () => {
  const actual = await vi.importActual('ink');
  return {
    ...actual,
    useInput: vi.fn(),
    useApp: () => ({ exit: vi.fn() }),
  };
});

import { useInput } from 'ink';

describe('InputBox', () => {
  let inputHandler: ((char: string, key: any) => void) | null = null;
  
  beforeEach(() => {
    vi.clearAllMocks();
    
    (useInput as any).mockImplementation((handler: any) => {
      inputHandler = handler;
    });
  });

  describe('渲染测试', () => {
    it('显示 build 模式图标', () => {
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

    it('显示 plan 模式图标', () => {
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

    it('显示帮助提示', () => {
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

    it('显示模型名称', () => {
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

    it('disabled 时显示加载状态', () => {
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

  describe('输入交互测试', () => {
    it('输入字符', () => {
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
      
      expect(inputHandler).not.toBeNull();
    });

    it('Enter 提交消息', () => {
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
        inputHandler('h', { ctrl: false, meta: false, shift: false });
        inputHandler('i', { ctrl: false, meta: false, shift: false });
        inputHandler('', { ctrl: false, meta: false, shift: false, return: true });
        
        expect(onSubmit).toHaveBeenCalledWith('hi');
      }
    });

    it('disabled 时不响应输入', () => {
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
      
      if (inputHandler) {
        inputHandler('a', { ctrl: false, meta: false, shift: false });
        inputHandler('', { ctrl: false, meta: false, shift: false, return: true });
        
        expect(onSubmit).not.toHaveBeenCalled();
      }
    });

    it('Backspace 删除字符', () => {
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
        inputHandler('', { ctrl: false, meta: false, shift: false, backspace: true });
        inputHandler('', { ctrl: false, meta: false, shift: false, return: true });
        
        expect(onSubmit).toHaveBeenCalledWith('a');
      }
    });

    it('Tab 换行', () => {
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
        inputHandler('l', { ctrl: false, meta: false, shift: false });
        inputHandler('1', { ctrl: false, meta: false, shift: false });
        inputHandler('', { ctrl: false, meta: false, shift: false, tab: true });
        inputHandler('l', { ctrl: false, meta: false, shift: false });
        inputHandler('2', { ctrl: false, meta: false, shift: false });
        inputHandler('', { ctrl: false, meta: false, shift: false, return: true });
        
        expect(onSubmit).toHaveBeenCalledWith('l1\nl2');
      }
    });

    it('Escape 取消输入', () => {
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
        inputHandler('', { ctrl: false, meta: false, shift: false, escape: true });
        inputHandler('', { ctrl: false, meta: false, shift: false, return: true });
        
        expect(onSubmit).not.toHaveBeenCalled();
      }
    });
  });

  describe('模式显示', () => {
    it('显示 BUILD 模式', () => {
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

    it('显示 PLAN 模式', () => {
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
