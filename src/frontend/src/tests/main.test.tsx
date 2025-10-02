import { describe, expect, test } from 'vitest';

// Ensure main imports and mounts without throwing
describe('main.tsx', () => {
  test('mounts app into root element', async () => {
    // Create a root container for React
    const root = document.createElement('div');
    root.id = 'root';
    document.body.appendChild(root);

    // Dynamic import triggers ReactDOM.createRoot(...).render(...)
    const mod = await import('../main.tsx');
    expect(mod).toBeTruthy();

    // Clean up
    document.body.removeChild(root);
  });
});
