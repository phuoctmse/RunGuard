import type { Incident, AuditRecord } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

export async function fetchIncidents(): Promise<Incident[]> {
  const res = await fetch(`${API_BASE}/incidents`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchIncident(id: string): Promise<Incident> {
  const res = await fetch(`${API_BASE}/incidents/${id}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function approveIncident(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/incidents/${id}/approve`, { method: 'POST' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
}

export async function rejectIncident(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/incidents/${id}/reject`, { method: 'POST' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
}

export async function fetchAuditTrail(id: string): Promise<AuditRecord[]> {
  const res = await fetch(`${API_BASE}/audit/${id}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
