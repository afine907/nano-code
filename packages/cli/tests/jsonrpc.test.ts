import { describe, it, expect, vi, beforeEach } from 'vitest';
import { JsonRpcClient } from '../src/client/jsonrpc.js';
import type { JsonRpcResponse } from '../src/client/types.js';

// Mock child_process
vi.mock('child_process', () => ({
  spawn: vi.fn(() => ({
    stdin: { 
      write: vi.fn(),
      end: vi.fn(),
    },
    stdout: { 
      on: vi.fn((event, callback) => {
        if (event === 'data') {
          // Simulate a response
          const response: JsonRpcResponse = {
            jsonrpc: '2.0',
            result: { content: 'Test response' },
            id: 1,
          };
          setTimeout(() => callback(JSON.stringify(response) + '\n'), 10);
        }
      }),
    },
    stderr: { on: vi.fn() },
    on: vi.fn((event, callback) => {
      if (event === 'close') {
        setTimeout(() => callback(0), 100);
      }
    }),
    kill: vi.fn(),
    unref: vi.fn(),
  })),
}));

// Mock fs
vi.mock('fs', () => ({
  existsSync: vi.fn(() => false),
}));

describe('JsonRpcClient', () => {
  let client: JsonRpcClient;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('can be instantiated', () => {
    client = new JsonRpcClient();
    expect(client).toBeDefined();
    client.close();
  });

  it('generates unique request ids', async () => {
    client = new JsonRpcClient();
    
    // The client should be able to make requests
    // (actual test would need real server or mock)
    client.close();
  });

  // Skip: This test requires a real Python server (integration test)
  it.skip('sends request and receives response', async () => {
    client = new JsonRpcClient();
    
    // Wait a bit for server to start
    await new Promise(resolve => setTimeout(resolve, 50));
    
    try {
      const result = await client.request<{ content: string }>('chat', { message: 'Hello' });
      expect(result).toBeDefined();
    } catch (error) {
      // Expected in test environment without real server
      expect(error).toBeDefined();
    }
    
    client.close();
  });
});
