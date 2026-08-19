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

export const fetchEmails = async (): Promise<Email[]> => {
  const response = await fetch(`${API_URL}/emails`);
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
