const API_URL = 'http://localhost:8000/api/v1';

export interface Email {
  id: number;
  subject: string;
  sender: string;
  timestamp: string;
  snippet: string;
  direction: string;
}

export interface EmailDetail extends Email {
  body: string;
  cleaned_body: string;
  thread_id: string;
}

export const fetchEmails = async (skip: number = 0, limit: number = 20): Promise<Email[]> => {
  const response = await fetch(`${API_URL}/emails?skip=${skip}&limit=${limit}`);
  if (!response.ok) throw new Error('Failed to fetch emails');
  return response.json();
};

export const fetchEmailDetail = async (id: number): Promise<EmailDetail> => {
  const response = await fetch(`${API_URL}/emails/${id}`);
  if (!response.ok) throw new Error('Failed to fetch email details');
  return response.json();
};

export const generateDraft = async (id: number, instructions: string) => {
  const response = await fetch(`${API_URL}/emails/${id}/generate-reply`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ instructions })
  });
  if (!response.ok) throw new Error('Failed to generate draft');
  return response.json();
};

export const syncGmail = async () => {
  // Assuming user 1 for MVP
  const response = await fetch(`${API_URL}/gmail/sync`, { method: 'POST' });
  if (!response.ok) throw new Error('Sync failed');
  return response.json();
};

export const getAuthUrl = async (): Promise<{ url: string }> => {
  const response = await fetch(`${API_URL}/auth/google`);
  if (!response.ok) throw new Error('Failed to fetch auth url');
  return response.json();
};

export const fetchAuthStatus = async () => {
  const response = await fetch(`${API_URL}/auth/me`);
  if (!response.ok) throw new Error('Failed to fetch auth status');
  return response.json();
};

export const fetchDrafts = async () => {
  const response = await fetch(`${API_URL}/drafts`);
  if (!response.ok) throw new Error('Failed to fetch drafts');
  return response.json();
};

export const saveDraft = async (draftData: any) => {
  const response = await fetch(`${API_URL}/drafts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(draftData)
  });
  if (!response.ok) throw new Error('Failed to save draft');
  return response.json();
};

export const fetchSettings = async () => {
  const response = await fetch(`${API_URL}/settings`);
  if (!response.ok) throw new Error('Failed to fetch settings');
  return response.json();
};

export const saveSettings = async (settingsData: any) => {
  const response = await fetch(`${API_URL}/settings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settingsData)
  });
  if (!response.ok) throw new Error('Failed to save settings');
  return response.json();
};
