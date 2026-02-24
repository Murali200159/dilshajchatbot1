// MongoDB init script — seeds sample payment data on first startup
db = db.getSiblingDB('company_app');

// Create payments collection with index
db.createCollection('payments');
db.payments.createIndex({ transaction_id: 1 }, { unique: true });
db.payments.createIndex({ user_id: 1 });
db.payments.createIndex({ email: 1 });

// Insert sample payment data
db.payments.insertMany([
    {
        transaction_id: 'TXN001',
        user_id: 'user_001',
        email: 'john@example.com',
        name: 'John Doe',
        amount: 2999,
        currency: 'INR',
        status: 'success',
        service: 'Web Development Course',
        date: '2024-01-15'
    },
    {
        transaction_id: 'TXN002',
        user_id: 'user_002',
        email: 'priya@example.com',
        name: 'Priya Sharma',
        amount: 4999,
        currency: 'INR',
        status: 'success',
        service: 'Full Stack Training',
        date: '2024-02-10'
    },
    {
        transaction_id: 'TXN003',
        user_id: 'user_003',
        email: 'ravi@example.com',
        name: 'Ravi Kumar',
        amount: 1500,
        currency: 'INR',
        status: 'pending',
        service: 'UI/UX Design',
        date: '2024-03-05'
    },
    {
        transaction_id: 'TXN004',
        user_id: 'user_001',
        email: 'john@example.com',
        name: 'John Doe',
        amount: 999,
        currency: 'INR',
        status: 'failed',
        service: 'Python Basics',
        date: '2024-03-20'
    }
]);

print('✅ MongoDB initialized with sample payment data');
