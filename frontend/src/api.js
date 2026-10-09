// src/api.js
const API_URL = 'http://localhost:8000/api';

export const validateDocument = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_URL}/validate`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
    }

    return await response.json();
};
