import { render, screen } from '@testing-library/react';
import { test, expect } from 'vitest';

import App from '../App';

test('renders react app', () => {
  render(<App />);
  expect(
    screen.getByText(/Click on the Vite and React logos to learn more/i),
  ).toBeInTheDocument();
});
