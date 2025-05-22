from typing import Dict

# Sample data for subadmin's investor activities
activities_data: Dict = {
    "subadmin_id": "123e4567-e89b-12d3-a456-426614174000",
    "subadmin_name": "Mudit Dua",
    "transaction_activities": [
        {
            "transaction_id": "a1b2c3d4-e5f6-7890-g1h2-3i4j5k6l7m8n",
            "investor": "Anjali Patel",
            "invested_in": "TechTrend Innovations",
            "amount": "150000",
            "transaction_date": "2025-05-20T10:00:00"
        },
        {
            "transaction_id": "b2c3d4e5-f6g7-8901-h2i3-4j5k6l7m8n9o",
            "investor": "Vikram Singh",
            "invested_in": "GreenLeaf Energy",
            "amount": "200000",
            "transaction_date": "2025-05-19T14:30:00"
        },
        {
            "transaction_id": "c3d4e5f6-g7h8-9012-i3j4-5k6l7m8n9o0p",
            "investor": "Priya Gupta",
            "invested_in": "HealthCare Solutions",
            "amount": "100000",
            "transaction_date": "2025-05-18T09:15:00"
        },
        {
            "transaction_id": "d4e5f6g7-h8i9-0123-j4k5-6l7m8n9o0p1q",
            "investor": "Arjun Mehta",
            "invested_in": "AI Dynamics",
            "amount": "300000",
            "transaction_date": "2025-05-17T11:45:00"
        },
        {
            "transaction_id": "e5f6g7h8-i9j0-1234-k5l6-7m8n9o0p1q2r",
            "investor": "Neha Sharma",
            "invested_in": "EduTech Ventures",
            "amount": "250000",
            "transaction_date": "2025-05-16T16:00:00"
        },
        {
            "transaction_id": "f6g7h8i9-j0k1-2345-l6m7-8n9o0p1q2r3s",
            "investor": "Rohit Verma",
            "invested_in": "FinTech Pioneers",
            "amount": "175000",
            "transaction_date": "2025-05-15T13:20:00"
        },
        {
            "transaction_id": "g7h8i9j0-k1l2-3456-m7n8-9o0p1q2r3s4t",
            "investor": "Kavita Desai",
            "invested_in": "AgriTech Solutions",
            "amount": "125000",
            "transaction_date": "2025-05-14T10:30:00"
        },
        {
            "transaction_id": "h8i9j0k1-l2m3-4567-n8o9-0p1q2r3s4t5u",
            "investor": "Sanjay Kumar",
            "invested_in": "SmartCity Tech",
            "amount": "200000",
            "transaction_date": "2025-05-13T15:00:00"
        },
        {
            "transaction_id": "i9j0k1l2-m3n4-5678-o9p0-1q2r3s4t5u6v",
            "investor": "Deepika Rao",
            "invested_in": "CleanEnergy Systems",
            "amount": "180000",
            "transaction_date": "2025-05-12T12:10:00"
        },
        {
            "transaction_id": "j0k1l2m3-n4o5-6789-p0q1-2r3s4t5u6v7w",
            "investor": "Amit Joshi",
            "invested_in": "BioTech Innovate",
            "amount": "220000",
            "transaction_date": "2025-05-11T09:50:00"
        }
    ],
    "onboarding_activities": [
        {
            "investor_id": "k1l2m3n4-o5p6-7890-q1r2-3s4t5u6v7w8x",
            "investor_name": "Anjali Patel",
            "joined_date": "2025-05-20T09:00:00"
        },
        {
            "investor_id": "l2m3n4o5-p6q7-8901-r2s3-4t5u6v7w8x9y",
            "investor_name": "Vikram Singh",
            "joined_date": "2025-05-19T10:30:00"
        },
        {
            "investor_id": "m3n4o5p6-q7r8-9012-s3t4-5u6v7w8x9y0z",
            "investor_name": "Priya Gupta",
            "joined_date": "2025-05-18T11:00:00"
        },
        {
            "investor_id": "n4o5p6q7-r8s9-0123-t4u5-6v7w8x9y0z1a",
            "investor_name": "Arjun Mehta",
            "joined_date": "2025-05-17T14:15:00"
        },
        {
            "investor_id": "o5p6q7r8-s9t0-1234-u5v6-7w8x9y0z1a2b",
            "investor_name": "Neha Sharma",
            "joined_date": "2025-05-16T08:45:00"
        },
        {
            "investor_id": "p6q7r8s9-t0u1-2345-v6w7-8x9y0z1a2b3c",
            "investor_name": "Rohit Verma",
            "joined_date": "2025-05-15T12:00:00"
        },
        {
            "investor_id": "q7r8s9t0-u1v2-3456-w7x8-9y0z1a2b3c4d",
            "investor_name": "Kavita Desai",
            "joined_date": "2025-05-14T13:30:00"
        },
        {
            "investor_id": "r8s9t0u1-v2w3-4567-x8y9-0z1a2b3c4d5e",
            "investor_name": "Sanjay Kumar",
            "joined_date": "2025-05-13T15:45:00"
        },
        {
            "investor_id": "s9t0u1v2-w3x4-5678-y9z0-1a2b3c4d5e6f",
            "investor_name": "Deepika Rao",
            "joined_date": "2025-05-12T10:20:00"
        },
        {
            "investor_id": "t0u1v2w3-x4y5-6789-z0a1-2b3c4d5e6f7g",
            "investor_name": "Amit Joshi",
            "joined_date": "2025-05-11T11:10:00"
        }
    ],
    "investor_kyc_activities": [
        {
            "investor_id": "k1l2m3n4-o5p6-7890-q1r2-3s4t5u6v7w8x",
            "investor_name": "Anjali Patel",
            "kyc_completed_date": "verified"
        },
        {
            "investor_id": "l2m3n4o5-p6q7-8901-r2s3-4t5u6v7w8x9y",
            "investor_name": "Vikram Singh",
            "kyc_completed_date": "verified"
        },
        {
            "investor_id": "m3n4o5p6-q7r8-9012-s3t4-5u6v7w8x9y0z",
            "investor_name": "Priya Gupta",
            "kyc_completed_date": "pending"
        },
        {
            "investor_id": "n4o5p6q7-r8s9-0123-t4u5-6v7w8x9y0z1a",
            "investor_name": "Arjun Mehta",
            "kyc_completed_date": "verified"
        },
        {
            "investor_id": "o5p6q7r8-s9t0-1234-u5v6-7w8x9y0z1a2b",
            "investor_name": "Neha Sharma",
            "kyc_completed_date": "pending"
        },
        {
            "investor_id": "p6q7r8s9-t0u1-2345-v6w7-8x9y0z1a2b3c",
            "investor_name": "Rohit Verma",
            "kyc_completed_date": "verified"
        },
        {
            "investor_id": "q7r8s9t0-u1v2-3456-w7x8-9y0z1a2b3c4d",
            "investor_name": "Kavita Desai",
            "kyc_completed_date": "pending"
        },
        {
            "investor_id": "r8s9t0u1-v2w3-4567-x8y9-0z1a2b3c4d5e",
            "investor_name": "Sanjay Kumar",
            "kyc_completed_date": "verified"
        },
        {
            "investor_id": "s9t0u1v2-w3x4-5678-y9z0-1a2b3c4d5e6f",
            "investor_name": "Deepika Rao",
            "kyc_completed_date": "pending"
        },
        {
            "investor_id": "t0u1v2w3-x4y5-6789-z0a1-2b3c4d5e6f7g",
            "investor_name": "Amit Joshi",
            "kyc_completed_date": "verified"
        }
    ],
    "success": True
} 

# dummy data for transactions

transaction_data: Dict = {
    "subadmin_id": "123e4567-e89b-12d3-a456-426614174000",
    "subadmin_name": "Mudit Dua",
    "transactions": [
        {
            "transaction_id": "a1b2c3d4-e5f6-7890-g1h2-3i4j5k6l7m8n",
            "investor": "Anjali Patel",
            "invested_in": "TechTrend Innovations",
            "amount": "150000",
            "transaction_date": "2025-05-20T10:00:00"
        },
        {
            "transaction_id": "b2c3d4e5-f6g7-8901-h2i3-4j5k6l7m8n9o",
            "investor": "Vikram Singh",
            "invested_in": "GreenLeaf Energy",
            "amount": "200000",
            "transaction_date": "2025-05-19T14:30:00"
        },
        {
            "transaction_id": "c3d4e5f6-g7h8-9012-i3j4-5k6l7m8n9o0p",
            "investor": "Priya Gupta",
            "invested_in": "HealthCare Solutions",
            "amount": "100000",
            "transaction_date": "2025-05-18T09:15:00"
        },
        {
            "transaction_id": "d4e5f6g7-h8i9-0123-j4k5-6l7m8n9o0p1q",
            "investor": "Arjun Mehta",
            "invested_in": "AI Dynamics",
            "amount": "300000",
            "transaction_date": "2025-05-17T11:45:00"
        },
        {
            "transaction_id": "e5f6g7h8-i9j0-1234-k5l6-7m8n9o0p1q2r",
            "investor": "Neha Sharma",
            "invested_in": "EduTech Ventures",
            "amount": "250000",
            "transaction_date": "2025-05-16T16:00:00"
        },
        {
            "transaction_id": "f6g7h8i9-j0k1-2345-l6m7-8n9o0p1q2r3s",
            "investor": "Rohit Verma",
            "invested_in": "FinTech Pioneers",
            "amount": "175000",
            "transaction_date": "2025-05-15T13:20:00"
        },
        {
            "transaction_id": "g7h8i9j0-k1l2-3456-m7n8-9o0p1q2r3s4t",
            "investor": "Kavita Desai",
            "invested_in": "AgriTech Solutions",
            "amount": "125000",
            "transaction_date": "2025-05-14T10:30:00"
        },
        {
            "transaction_id": "h8i9j0k1-l2m3-4567-n8o9-0p1q2r3s4t5u",
            "investor": "Sanjay Kumar",
            "invested_in": "SmartCity Tech",
            "amount": "200000",
            "transaction_date": "2025-05-13T15:00:00"
        },
        {
            "transaction_id": "i9j0k1l2-m3n4-5678-o9p0-1q2r3s4t5u6v",
            "investor": "Deepika Rao",
            "invested_in": "CleanEnergy Systems",
            "amount": "180000",
            "transaction_date": "2025-05-12T12:10:00"
        },
        {
            "transaction_id": "j0k1l2m3-n4o5-6789-p0q1-2r3s4t5u6v7w",
            "investor": "Amit Joshi",
            "invested_in": "BioTech Innovate",
            "amount": "220000",
            "transaction_date": "2025-05-11T09:50:00"
        }
    ],
    
    "success": True
}

