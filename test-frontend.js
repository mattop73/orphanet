#!/usr/bin/env node
/**
 * Frontend functionality test script
 * Tests all the API endpoints that the web interface uses
 */

const BASE_URL = 'http://localhost:3000';

async function testFrontendEndpoints() {
    console.log('🧪 Testing Frontend API Endpoints');
    console.log('=' * 50);
    
    const tests = [
        {
            name: '🏥 Health Check',
            url: '/health',
            test: (data) => data.status === 'healthy'
        },
        {
            name: '📊 Database Statistics',
            url: '/api/stats',
            test: (data) => data.success && data.data.disorders > 0
        },
        {
            name: '📋 List Disorders',
            url: '/api/disorders?limit=5',
            test: (data) => data.success && Array.isArray(data.data) && data.data.length > 0
        },
        {
            name: '🔍 Search Functionality',
            url: '/api/disorders/search/syndrome?limit=3',
            test: (data) => data.success && Array.isArray(data.data)
        },
        {
            name: '🧬 Gene Data',
            url: '/api/genes?limit=3',
            test: (data) => data.success && Array.isArray(data.data)
        },
        {
            name: '🔬 HPO Terms',
            url: '/api/hpo-terms?limit=3',
            test: (data) => data.success && Array.isArray(data.data)
        }
    ];
    
    let passed = 0;
    let total = tests.length;
    
    for (const test of tests) {
        try {
            console.log(`\n${test.name}`);
            console.log(`🔗 GET ${test.url}`);
            
            const response = await fetch(`${BASE_URL}${test.url}`);
            const data = await response.json();
            
            if (response.ok && test.test(data)) {
                console.log('✅ PASS');
                if (data.data && Array.isArray(data.data) && data.data.length > 0) {
                    console.log(`   📊 Found ${data.data.length} items`);
                    if (data.pagination) {
                        console.log(`   📄 Total: ${data.pagination.total}`);
                    }
                }
                passed++;
            } else {
                console.log('❌ FAIL');
                console.log(`   Error: ${JSON.stringify(data, null, 2)}`);
            }
        } catch (error) {
            console.log('💥 ERROR');
            console.log(`   ${error.message}`);
        }
    }
    
    console.log('\n' + '=' * 50);
    console.log(`🎯 Results: ${passed}/${total} tests passed`);
    
    if (passed === total) {
        console.log('🎉 All frontend endpoints are working perfectly!');
        console.log('\n🌐 Open your browser to:');
        console.log('   http://localhost:3000/index.html');
        console.log('\n💡 Features available in the web interface:');
        console.log('   • Interactive API testing');
        console.log('   • Real-time disorder search');
        console.log('   • Gene and HPO term browsing');
        console.log('   • Database statistics dashboard');
        console.log('   • Beautiful responsive design');
    } else {
        console.log('⚠️  Some endpoints need attention');
    }
}

// Check if server is running first
async function checkServer() {
    try {
        const response = await fetch(`${BASE_URL}/health`);
        return response.ok;
    } catch (error) {
        return false;
    }
}

async function main() {
    const serverRunning = await checkServer();
    
    if (!serverRunning) {
        console.log('❌ Server not running on port 3000');
        console.log('🚀 Start the server first with: npm start');
        console.log('📝 Or run: ./start-frontend.sh');
        process.exit(1);
    }
    
    await testFrontendEndpoints();
}

main().catch(console.error);