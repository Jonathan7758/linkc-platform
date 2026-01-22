import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock WebSocket
class MockWebSocket {
  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: ((error: Event) => void) | null = null;

  constructor(public url: string) {
    setTimeout(() => this.onopen?.(), 0);
  }

  send(_data: string) {
    // Mock send
  }

  close() {
    this.onclose?.();
  }
}

vi.stubGlobal('WebSocket', MockWebSocket);

// Mock fetch
globalThis.fetch = vi.fn();

// Mock import.meta.env
vi.stubGlobal('import.meta', {
  env: {
    VITE_API_URL: '/api/v1',
  },
});
