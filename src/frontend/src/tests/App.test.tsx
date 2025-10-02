import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { test, expect } from 'vitest';

import App from '../App';

test('renders react app', () => {
  render(<App />);
  expect(
    screen.getByText(/Click on the Vite and React logos to learn more/i),
  ).toBeInTheDocument();
});

test('increments counter on click', async () => {
  const user = userEvent.setup();
  render(<App />);
  const button = await screen.findByRole('button', { name: /count is 0/i });
  await user.click(button);
  expect(button).toHaveTextContent(/count is 1/i);
});
