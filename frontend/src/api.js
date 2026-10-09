// src/api.js
const API_URL = 'http://localhost:8000/api';

export const validateDocument = async (file, domainMode) => {
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('domain_mode', domainMode);

        const response = await fetch(`${API_URL}/validate`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        return await response.json();
    } catch (err) {
        console.warn("Backend not available, using MOCK DATA for Person B development:", err);
        
        return new Promise(resolve => setTimeout(() => resolve(
            domainMode === 'health_insurance' 
            ? {
                "claim_id": 999,
                "metadata": { "model_used": "gemini-2.5-flash-mock", "domain": "health_insurance", "is_fallback_mock": true },
                "perception": {
                    "structured_data": {
                    "provider_name": "Apollo Hospitals Mock", "patient_or_employee_name": "Rahul Sharma",
                    "currency": "INR",
                    "items": [ 
                        {"description": "ICU", "amount": 20000, "category": "room_rent"},
                        {"description": "Syringes", "amount": 500, "category": "consumables"}
                    ],
                    "total_extracted": 20500, "confidence_score": 0.95
                    }
                },
                "validation": {
                    "is_valid": false, "final_amount_inr": 20500,
                    "results": [
                    { "rule_name": "Fraud Detection", "passed": true, "message": "Hash unique." },
                    { "rule_name": "Room Rent Cap", "passed": false, "message": "Room rent exceeds standard cap of ₹10,000." },
                    { "rule_name": "Consumables Excluded", "passed": false, "message": "Non-medical consumables are not covered." }
                    ]
                }
            }
            : {
                "claim_id": 998,
                "metadata": { "model_used": "gemini-2.5-flash-mock", "domain": "expense", "is_fallback_mock": true },
                "perception": {
                    "structured_data": {
                    "provider_name": "Starbucks Mock", "patient_or_employee_name": "Employee", "currency": "USD",
                    "items": [ 
                        {"description": "Iced Vanilla Latte", "amount": 6.50, "category": "meals"},
                        {"description": "Butter Croissant", "amount": 3.25, "category": "meals"}
                    ],
                    "total_extracted": 9.75, "confidence_score": 0.98
                    }
                },
                "validation": {
                    "is_valid": true, "final_amount_inr": 814.12,
                    "results": [
                    { "rule_name": "Fraud Detection", "passed": true, "message": "Receipt hash is unique." },
                    { "rule_name": "Math Verification", "passed": true, "message": "Line items sum perfectly." }
                    ]
                }
            }
        ), 1500));
    }
};

export const fetchClaims = async () => {
    try {
        const response = await fetch(`${API_URL}/claims`);
        if (!response.ok) throw new Error("Failed to fetch claims");
        return await response.json();
    } catch (err) {
        console.warn("Backend not available, using MOCK HISTORY:", err);
        return [
            {
                "id": 1,
                "domain": "expense",
                "total_inr": 417.5,
                "is_valid": true,
                "status": "Approved",
                "timestamp": "2026-10-09 10:00:00"
            },
            {
                "id": 2,
                "domain": "health_insurance",
                "total_inr": 20500,
                "is_valid": false,
                "status": "Rejected",
                "timestamp": "2026-10-09 11:30:00"
            }
        ];
    }
};

export const submitDecision = async (claimId, decision) => {
    try {
        const response = await fetch(`${API_URL}/claims/${claimId}/decision`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ decision })
        });
        if (!response.ok) throw new Error("Failed to submit decision");
        return await response.json();
    } catch (err) {
        console.warn("Backend not available, MOCK DECISION:", err);
        return { status: "success", claim_id: claimId, decision };
    }
};

export const getExportUrl = () => {
    return `${API_URL}/export.csv`;
};
