// src/api.js
const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export const validateDocument = async (file, domainMode = 'expense') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('domain_mode', domainMode);
    formData.append('prompt', '');

    const response = await fetch(`${API_URL}/validate`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        let detail = response.statusText;
        try {
            const body = await response.json();
            detail = body.detail || detail;
        } catch {
            // Keep the HTTP status when the server does not return JSON.
        }
        throw new Error(detail);
    }

    return await response.json();
};
