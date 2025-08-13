#!/usr/bin/env node
/**
 * Simple test script for the Orphanet API
 */

const BASE_URL = 'http://localhost:3000';

async function testEndpoint(endpoint, description) {
    try {
        console.log(`\n🔍 Testing: ${description}`);
        console.log(`📡 GET ${endpoint}`);
        
        const response = await fetch(`${BASE_URL}${endpoint}`);
        const data = await response.json();
        
        if (response.ok) {
            console.log(`✅ Status: ${response.status}`);
            if (data.data && Array.isArray(data.data)) {
                console.log(`📊 Results: ${data.data.length} items`);
                if (data.pagination) {
                    console.log(`📄 Page ${data.pagination.page} of ${data.pagination.totalPages} (Total: ${data.pagination.total})`);
                }
                if (data.data.length > 0) {
                    console.log(`🔍 Sample:`, JSON.stringify(data.data[0], null, 2));
                }
            } else if (data.data) {
                console.log(`📋 Data:`, JSON.stringify(data.data, null, 2));
            } else {
                console.log(`📋 Response:`, JSON.stringify(data, null, 2));
            }
        } else {
            console.log(`❌ Status: ${response.status}`);
            console.log(`❌ Error:`, data);
        }
    } catch (error) {
        console.log(`💥 Request failed:`, error.message);
    }
}

async function runTests() {
    console.log('🚀 Starting Orphanet API Tests');
    console.log('=' * 50);
    
    // Test basic endpoints
    await testEndpoint('/', 'API Information');
    await testEndpoint('/health', 'Health Check');
    await testEndpoint('/api/stats', 'Database Statistics');
    
    // Test data endpoints
    await testEndpoint('/api/disorders?limit=3', 'List Disorders (Limited)');
    await testEndpoint('/api/genes?limit=3', 'List Genes (Limited)');
    await testEndpoint('/api/hpo-terms?limit=3', 'List HPO Terms (Limited)');
    
    // Test search
    await testEndpoint('/api/disorders/search/alexander', 'Search Disorders');
    
    // Test specific disorder (using a common Orpha code)
    await testEndpoint('/api/disorders/58', 'Get Specific Disorder (Alexander disease)');
    
    // Test specific gene
    await testEndpoint('/api/genes/GFAP', 'Get Specific Gene (if exists)');
    
    console.log('\n🏁 Tests completed!');
    console.log('\n💡 Try these URLs in your browser:');
    console.log(`   ${BASE_URL}/`);
    console.log(`   ${BASE_URL}/api/stats`);
    console.log(`   ${BASE_URL}/api/disorders?limit=5`);
    console.log(`   ${BASE_URL}/api/disorders/search/syndrome`);
}

// Check if server is running
async function checkServer() {
    try {
        const response = await fetch(`${BASE_URL}/health`);
        if (response.ok) {
            return true;
        }
    } catch (error) {
        return false;
    }
    return false;
}

// Main execution
async function main() {
    const serverRunning = await checkServer();
    
    if (!serverRunning) {
        console.log('❌ Server not running on port 3000');
        console.log('🚀 Start the server first with: npm start');
        console.log('📝 Or in development mode: npm run dev');
        process.exit(1);
    }
    
    await runTests();
}

main().catch(console.error);