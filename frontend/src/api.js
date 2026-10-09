// src/api.js
const API_URL = 'http://localhost:8000/api';

export const processDocument = async (file) => {
    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_URL}/process`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        return await response.json();
    } catch (err) {
        console.warn("Backend not available, using MOCK DATA for Person B development:", err);
        
        // Mock data to allow B1 to proceed
        return new Promise(resolve => setTimeout(() => resolve({
            "metadata": { "model_used": "gemini-2.5-flash-mock", "is_fallback_mock": true },
            "perception": {
                "structured_data": {
                "vendor_name": "Starbucks Mock", "date_extracted": "2026-10-09", "currency": "USD",
                "items": [ 
                    {"description": "Iced Vanilla Latte", "amount": 6.50},
                    {"description": "Butter Croissant", "amount": 3.25}
                ],
                "total_extracted": 9.75, "confidence_score": 0.98
                }
            },
            "verification": {
                "is_valid": true, "final_amount_inr": 814.12,
                "results": [
                { "rule_name": "Fraud Detection", "passed": true, "message": "Receipt hash is unique." },
                { "rule_name": "Math Verification", "passed": true, "message": "Line items sum perfectly to 9.75." }
                ]
            }
        }), 1500));
    }
};
