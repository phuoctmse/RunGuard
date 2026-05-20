import type { Incident, AuditRecord, Runbook } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api';
const TOKEN_KEY = 'runguard_token';

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const headers = new Headers(init?.headers);
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    if (res.status === 401) {
      clearToken();
      window.location.href = '/login';
      throw new ApiError(401, 'Session expired');
    }
    const body = await res.text();
    throw new ApiError(res.status, body || `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// --- Incidents ---

export function fetchIncidents(): Promise<Incident[]> {
  return request<Incident[]>('/incidents');
}

export function fetchIncident(id: string): Promise<Incident> {
  return request<Incident>(`/incidents/${id}`);
}

export function createIncident(inc: Omit<Incident, 'id' | 'phase'>): Promise<{ id: string }> {
  return request<{ id: string }>('/incidents', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(inc),
  });
}

export function approveIncident(id: string): Promise<{ status: string }> {
  return request<{ status: string }>(`/incidents/${id}/approve`, { method: 'POST' });
}

export function rejectIncident(id: string): Promise<{ status: string }> {
  return request<{ status: string }>(`/incidents/${id}/reject`, { method: 'POST' });
}

// --- Audit ---

export function fetchAuditTrail(incidentId: string): Promise<AuditRecord[]> {
  return request<AuditRecord[]>(`/audit/${incidentId}`);
}

// --- Runbooks ---

export function fetchRunbooks(): Promise<Runbook[]> {
  return request<Runbook[]>('/runbooks');
}

export function createRunbook(runbook: Omit<Runbook, 'id'>): Promise<{ id: string }> {
  return request<{ id: string }>('/runbooks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(runbook),
  });
}

// --- Health ---

export function fetchHealth(): Promise<{ status: string }> {
  return request<{ status: string }>('/healthz');
}
