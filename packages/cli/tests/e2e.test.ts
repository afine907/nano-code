import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { spawn, ChildProcess } from 'child_process';
import { resolve } from 'path';

describe('CLI E2E Tests', () => {
  let cliProcess: ChildProcess | null = null;
  const cliPath = resolve(__dirname, '../src/index.tsx');
  const timeout = 10000; // 10 seconds

  afterAll(() => {
    if (cliProcess) {
      cliProcess.kill();
    }
  });

  it.skip('should start CLI and show welcome message', async () => {
    // Skip in CI - requires interactive terminal
    return new Promise<void>((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        if (cliProcess) cliProcess.kill();
        reject(new Error('Timeout waiting for welcome message'));
      }, timeout);

      cliProcess = spawn('npx', ['tsx', cliPath], {
        cwd: resolve(__dirname, '../../..'),
        env: { ...process.env, NODE_ENV: 'test' },
      });

      let output = '';
      cliProcess.stdout?.on('data', (data) => {
        output += data.toString();
        if (output.includes('Welcome') || output.includes('jojo')) {
          clearTimeout(timeoutId);
          expect(output).toBeTruthy();
          resolve();
        }
      });

      cliProcess.stderr?.on('data', (data) => {
        console.error('STDERR:', data.toString());
      });

      cliProcess.on('error', (error) => {
        clearTimeout(timeoutId);
        reject(error);
      });
    });
  });

  it.skip('should handle /help command', async () => {
    // Skip in CI - requires interactive terminal
    return new Promise<void>((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        if (cliProcess) cliProcess.kill();
        reject(new Error('Timeout'));
      }, timeout);

      cliProcess = spawn('npx', ['tsx', cliPath], {
        cwd: resolve(__dirname, '../../..'),
        env: { ...process.env, NODE_ENV: 'test' },
      });

      let output = '';
      cliProcess.stdout?.on('data', (data) => {
        output += data.toString();
        if (output.includes('help') || output.includes('命令')) {
          clearTimeout(timeoutId);
          resolve();
        }
      });

      cliProcess.on('error', (error) => {
        clearTimeout(timeoutId);
        reject(error);
      });
    });
  });
});
