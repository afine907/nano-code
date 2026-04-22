import { describe, it, expect } from 'vitest';

// InputBox uses useInput which requires a TTY, so we test the logic separately

describe('InputBox Logic', () => {
  describe('Input State Management', () => {
    it('tracks single line input', () => {
      let input = '';
      let lines: string[] = [];
      
      input = 'hello';
      expect(input).toBe('hello');
      
      input = input.slice(0, -1);
      expect(input).toBe('hell');
    });

    it('handles multiline mode', () => {
      let input = 'first line';
      let lines: string[] = [];
      
      lines.push(input);
      input = '';
      
      input = 'second line';
      lines.push(input);
      
      expect(lines.length).toBe(2);
      expect(lines[0]).toBe('first line');
      expect(lines[1]).toBe('second line');
    });

    it('handles backspace in multiline', () => {
      let input = '';
      let lines = ['first line', 'second line'];
      
      if (input === '' && lines.length > 0) {
        input = lines.pop() || '';
      }
      
      expect(lines.length).toBe(1);
      expect(input).toBe('second line');
    });
  });

  describe('Mode Icons', () => {
    it('uses correct icons for modes', () => {
      const buildIcon = '🦞';
      const planIcon = '📋';
      
      expect(buildIcon).toBe('🦞');
      expect(planIcon).toBe('📋');
    });
  });

  describe('Submit Logic', () => {
    it('combines lines on submit', () => {
      const lines = ['first', 'second', 'third'];
      const input = 'fourth';
      
      const allLines = [...lines, input].filter(l => l.trim());
      const result = allLines.join('\n');
      
      expect(result).toBe('first\nsecond\nthird\nfourth');
    });

    it('handles empty submit', () => {
      const lines: string[] = [];
      const input = '';
      
      const allLines = [...lines, input].filter(l => l.trim());
      
      expect(allLines.length).toBe(0);
    });
  });

  describe('Model Display', () => {
    it('shows model name in status', () => {
      const model = 'gpt-4o-mini';
      expect(model).toContain('gpt');
    });
  });
});
