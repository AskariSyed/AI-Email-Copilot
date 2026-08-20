import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';
import * as api from './services/api';

// Mock the API module
vi.mock('./services/api', () => ({
  fetchEmails: vi.fn(),
  fetchEmailDetail: vi.fn(),
  generateDraft: vi.fn(),
  syncGmail: vi.fn(),
  getAuthUrl: vi.fn(),
  fetchDrafts: vi.fn(),
  fetchSettings: vi.fn(),
  saveSettings: vi.fn(),
  saveDraft: vi.fn(),
  sendEmailReply: vi.fn(),
  chatWithInbox: vi.fn(),
  fetchAccounts: vi.fn(),
  analyzeStyle: vi.fn(),
}));

describe('App Component', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    
    // Default mocks
    (api.fetchAccounts as any).mockResolvedValue([
      { id: 1, email_address: 'test@example.com', name: 'Test User' }
    ]);
    
    (api.fetchEmails as any).mockResolvedValue([
      { id: 1, sender: 'Alice', subject: 'Hello', timestamp: '2023-01-01', snippet: 'Hi there', direction: 'incoming' },
      { id: 2, sender: 'Bob', subject: 'Invoice', timestamp: '2023-01-02', snippet: 'Attached', direction: 'incoming' }
    ]);
    
    (api.fetchSettings as any).mockResolvedValue({
      profile_data: { manual: {}, inferred: {} }
    });
  });

  it('renders the application and shows the inbox by default', async () => {
    render(<App />);
    
    // Wait for accounts and emails to load
    await waitFor(() => {
      expect(screen.getByText('Email Copilot')).toBeInTheDocument();
      expect(screen.getByText('Alice')).toBeInTheDocument();
      expect(screen.getByText('Bob')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Inbox')).toBeInTheDocument();
  });

  it('switches to the settings tab and loads data', async () => {
    render(<App />);
    
    // Click Settings tab
    const settingsTab = screen.getByText('settings', { selector: 'button' });
    fireEvent.click(settingsTab);
    
    await waitFor(() => {
      expect(screen.getByText('Preferences')).toBeInTheDocument();
      expect(api.fetchSettings).toHaveBeenCalled();
    });
  });

  it('loads email details when an email is clicked', async () => {
    (api.fetchEmailDetail as any).mockResolvedValue({
      id: 1, sender: 'Alice', subject: 'Hello', timestamp: '2023-01-01', 
      snippet: 'Hi there', direction: 'incoming', cleaned_body: 'This is the full email body.'
    });
    
    render(<App />);
    
    // Wait for emails to load
    await waitFor(() => {
      expect(screen.getByText('Alice')).toBeInTheDocument();
    });
    
    // Click the email
    const emailItem = screen.getByText('Alice');
    fireEvent.click(emailItem);
    
    await waitFor(() => {
      expect(api.fetchEmailDetail).toHaveBeenCalledWith(1);
      expect(screen.getByText('This is the full email body.')).toBeInTheDocument();
    });
  });

  it('triggers draft generation with correct instructions', async () => {
    (api.fetchEmailDetail as any).mockResolvedValue({
      id: 1, sender: 'Alice', subject: 'Hello', timestamp: '2023-01-01', 
      snippet: 'Hi there', direction: 'incoming', cleaned_body: 'This is the full email body.'
    });
    
    (api.generateDraft as any).mockResolvedValue({
      generated_body: 'This is a mocked generated draft reply.'
    });
    
    render(<App />);
    
    // Wait for emails to load and click one
    await waitFor(() => expect(screen.getByText('Alice')).toBeInTheDocument());
    fireEvent.click(screen.getByText('Alice'));
    
    await waitFor(() => expect(screen.getByText('This is the full email body.')).toBeInTheDocument());
    
    // Find the instructions input and generate button
    const instructionInput = screen.getByPlaceholderText("Instruct the AI (e.g. 'say yes politely')");
    fireEvent.change(instructionInput, { target: { value: 'say yes' } });
    
    const genButton = screen.getByText('GEN', { selector: 'button' });
    fireEvent.click(genButton);
    
    await waitFor(() => {
      expect(api.generateDraft).toHaveBeenCalledWith(1, 'say yes');
      expect(screen.getByDisplayValue('This is a mocked generated draft reply.')).toBeInTheDocument();
    });
  });
});
