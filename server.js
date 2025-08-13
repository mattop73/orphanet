#!/usr/bin/env node
/**
 * Orphanet API Server
 * Simple Express API to query Orphanet rare disease data from Supabase
 */

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import dotenv from 'dotenv';
import { createClient } from '@supabase/supabase-js';

// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize Supabase client
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
    console.error('❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables');
    console.error('Please check your .env file or environment configuration');
    process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

// Middleware
app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            scriptSrc: ["'self'", "'unsafe-inline'"],
            scriptSrcAttr: ["'unsafe-inline'"],
            styleSrc: ["'self'", "'unsafe-inline'"],
            imgSrc: ["'self'", "data:", "https:"],
            connectSrc: ["'self'"]
        }
    }
}));
app.use(compression());
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Request logging middleware
app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
    next();
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: '1.0.0'
    });
});

// API Info endpoint
app.get('/', (req, res) => {
    res.json({
        name: 'Orphanet API',
        description: 'API for querying rare disease data from Orphanet',
        version: '1.0.0',
        endpoints: {
            'GET /': 'API information',
            'GET /health': 'Health check',
            'GET /api/disorders': 'List all disorders (paginated)',
            'GET /api/disorders/:orpha_code': 'Get specific disorder by Orpha code',
            'GET /api/disorders/search/:query': 'Search disorders by name',
            'GET /api/genes': 'List all genes (paginated)',
            'GET /api/genes/:symbol': 'Get specific gene by symbol',
            'GET /api/hpo-terms': 'List HPO terms (paginated)',
            'GET /api/stats': 'Database statistics'
        },
        documentation: 'https://github.com/your-repo/orphanet-api'
    });
});

// Database statistics endpoint
app.get('/api/stats', async (req, res) => {
    try {
        const tables = [
            'disorders', 'disorder_synonyms', 'age_of_onset', 'inheritance_types',
            'genes', 'gene_external_refs', 'disorder_gene_associations',
            'hpo_terms', 'disorder_hpo_associations', 'prevalence_data',
            'disorder_classifications', 'external_references', 'disorder_texts',
            'disabilities', 'disorder_disability_associations'
        ];

        const stats = {};
        
        for (const table of tables) {
            try {
                const { count, error } = await supabase
                    .from(table)
                    .select('id', { count: 'exact', head: true });
                
                if (error) throw error;
                stats[table] = count;
            } catch (err) {
                stats[table] = `Error: ${err.message}`;
            }
        }

        res.json({
            success: true,
            data: stats,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        console.error('Stats error:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to retrieve database statistics',
            message: error.message
        });
    }
});

// Get all disorders (paginated)
app.get('/api/disorders', async (req, res) => {
    try {
        const page = parseInt(req.query.page) || 1;
        const limit = Math.min(parseInt(req.query.limit) || 20, 100); // Max 100 per page
        const offset = (page - 1) * limit;

        const { data, error, count } = await supabase
            .from('disorders')
            .select(`
                id,
                orpha_code,
                name,
                disorder_type,
                disorder_group,
                expert_link,
                created_at
            `, { count: 'exact' })
            .order('orpha_code')
            .range(offset, offset + limit - 1);

        if (error) throw error;

        res.json({
            success: true,
            data: data || [],
            pagination: {
                page,
                limit,
                total: count,
                totalPages: Math.ceil(count / limit)
            }
        });
    } catch (error) {
        console.error('Disorders error:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to retrieve disorders',
            message: error.message
        });
    }
});

// Get specific disorder by Orpha code
app.get('/api/disorders/:orpha_code', async (req, res) => {
    try {
        const { orpha_code } = req.params;

        // Get main disorder info
        const { data: disorder, error: disorderError } = await supabase
            .from('disorders')
            .select(`
                id,
                orpha_code,
                name,
                disorder_type,
                disorder_group,
                expert_link,
                created_at,
                updated_at
            `)
            .eq('orpha_code', orpha_code)
            .single();

        if (disorderError) throw disorderError;
        if (!disorder) {
            return res.status(404).json({
                success: false,
                error: 'Disorder not found',
                orpha_code
            });
        }

        // Get related data
        const [synonyms, genes, hpoTerms, prevalence, classifications] = await Promise.all([
            // Synonyms
            supabase
                .from('disorder_synonyms')
                .select('synonym')
                .eq('disorder_id', disorder.id),
            
            // Associated genes
            supabase
                .from('disorder_gene_associations')
                .select(`
                    association_type,
                    association_status,
                    source_of_validation,
                    genes (
                        gene_symbol,
                        gene_name,
                        gene_type,
                        chromosomal_location
                    )
                `)
                .eq('disorder_id', disorder.id),
            
            // HPO terms (clinical signs)
            supabase
                .from('disorder_hpo_associations')
                .select(`
                    frequency,
                    frequency_category,
                    diagnostic_criteria,
                    hpo_terms (
                        hpo_id,
                        term
                    )
                `)
                .eq('disorder_id', disorder.id),
            
            // Prevalence data
            supabase
                .from('prevalence_data')
                .select(`
                    prevalence_type,
                    prevalence_qualification,
                    prevalence_class,
                    val_moy,
                    geographic_area,
                    validation_status,
                    source
                `)
                .eq('disorder_id', disorder.id),
            
            // Classifications
            supabase
                .from('disorder_classifications')
                .select(`
                    parent_disorder_orpha_code,
                    parent_disorder_name,
                    association_type
                `)
                .eq('disorder_id', disorder.id)
        ]);

        res.json({
            success: true,
            data: {
                ...disorder,
                synonyms: synonyms.data?.map(s => s.synonym) || [],
                genes: genes.data || [],
                clinical_signs: hpoTerms.data || [],
                prevalence: prevalence.data || [],
                classifications: classifications.data || []
            }
        });
    } catch (error) {
        console.error('Disorder detail error:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to retrieve disorder details',
            message: error.message
        });
    }
});

// Search disorders by name
app.get('/api/disorders/search/:query', async (req, res) => {
    try {
        const { query } = req.params;
        const page = parseInt(req.query.page) || 1;
        const limit = Math.min(parseInt(req.query.limit) || 20, 100);
        const offset = (page - 1) * limit;

        const { data, error, count } = await supabase
            .from('disorders')
            .select(`
                id,
                orpha_code,
                name,
                disorder_type,
                disorder_group,
                expert_link
            `, { count: 'exact' })
            .ilike('name', `%${query}%`)
            .order('name')
            .range(offset, offset + limit - 1);

        if (error) throw error;

        res.json({
            success: true,
            data: data || [],
            query,
            pagination: {
                page,
                limit,
                total: count,
                totalPages: Math.ceil(count / limit)
            }
        });
    } catch (error) {
        console.error('Search error:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to search disorders',
            message: error.message
        });
    }
});

// Get all genes (paginated)
app.get('/api/genes', async (req, res) => {
    try {
        const page = parseInt(req.query.page) || 1;
        const limit = Math.min(parseInt(req.query.limit) || 20, 100);
        const offset = (page - 1) * limit;

        const { data, error, count } = await supabase
            .from('genes')
            .select(`
                id,
                gene_symbol,
                gene_name,
                gene_type,
                chromosomal_location,
                created_at
            `, { count: 'exact' })
            .order('gene_symbol')
            .range(offset, offset + limit - 1);

        if (error) throw error;

        res.json({
            success: true,
            data: data || [],
            pagination: {
                page,
                limit,
                total: count,
                totalPages: Math.ceil(count / limit)
            }
        });
    } catch (error) {
        console.error('Genes error:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to retrieve genes',
            message: error.message
        });
    }
});

// Get specific gene by symbol
app.get('/api/genes/:symbol', async (req, res) => {
    try {
        const { symbol } = req.params;

        // Get gene info
        const { data: gene, error: geneError } = await supabase
            .from('genes')
            .select(`
                id,
                gene_symbol,
                gene_name,
                gene_type,
                chromosomal_location,
                created_at,
                updated_at
            `)
            .eq('gene_symbol', symbol)
            .single();

        if (geneError) throw geneError;
        if (!gene) {
            return res.status(404).json({
                success: false,
                error: 'Gene not found',
                symbol
            });
        }

        // Get associated disorders
        const { data: disorders, error: disordersError } = await supabase
            .from('disorder_gene_associations')
            .select(`
                association_type,
                association_status,
                source_of_validation,
                disorders (
                    orpha_code,
                    name,
                    disorder_type
                )
            `)
            .eq('gene_id', gene.id);

        if (disordersError) throw disordersError;

        res.json({
            success: true,
            data: {
                ...gene,
                associated_disorders: disorders || []
            }
        });
    } catch (error) {
        console.error('Gene detail error:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to retrieve gene details',
            message: error.message
        });
    }
});

// Get HPO terms (paginated)
app.get('/api/hpo-terms', async (req, res) => {
    try {
        const page = parseInt(req.query.page) || 1;
        const limit = Math.min(parseInt(req.query.limit) || 20, 100);
        const offset = (page - 1) * limit;

        const { data, error, count } = await supabase
            .from('hpo_terms')
            .select(`
                id,
                hpo_id,
                term,
                created_at
            `, { count: 'exact' })
            .order('hpo_id')
            .range(offset, offset + limit - 1);

        if (error) throw error;

        res.json({
            success: true,
            data: data || [],
            pagination: {
                page,
                limit,
                total: count,
                totalPages: Math.ceil(count / limit)
            }
        });
    } catch (error) {
        console.error('HPO terms error:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to retrieve HPO terms',
            message: error.message
        });
    }
});

// Get disease-symptom associations with frequencies
app.get('/api/disorder-symptoms/:orpha_code', async (req, res) => {
    try {
        const { orpha_code } = req.params;

        // Get disorder first
        const { data: disorder, error: disorderError } = await supabase
            .from('disorders')
            .select('id, name, orpha_code')
            .eq('orpha_code', orpha_code)
            .single();

        if (disorderError) throw disorderError;
        if (!disorder) {
            return res.status(404).json({
                success: false,
                error: 'Disorder not found',
                orpha_code
            });
        }

        // Get HPO associations with frequencies
        const { data: associations, error: assocError } = await supabase
            .from('disorder_hpo_associations')
            .select(`
                frequency,
                frequency_category,
                diagnostic_criteria,
                hpo_terms (
                    hpo_id,
                    term
                )
            `)
            .eq('disorder_id', disorder.id);

        if (assocError) throw assocError;

        res.json({
            success: true,
            data: {
                disorder: disorder,
                symptoms: associations || [],
                total_symptoms: associations ? associations.length : 0
            }
        });
    } catch (error) {
        console.error('Disorder symptoms error:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to retrieve disorder symptoms',
            message: error.message
        });
    }
});

// Get database schema information
app.get('/api/schema', async (req, res) => {
    try {
        // Get table information from Supabase
        const tables = [
            'disorders', 'disorder_synonyms', 'hpo_terms', 'disorder_hpo_associations',
            'genes', 'disorder_gene_associations', 'prevalence_data',
            'disorder_classifications', 'external_references', 'disorder_texts',
            'disabilities', 'disorder_disability_associations',
            'age_of_onset', 'inheritance_types', 'gene_external_refs'
        ];

        const schema = {};
        
        for (const table of tables) {
            try {
                // Get a sample row to understand the structure
                const { data, error } = await supabase
                    .from(table)
                    .select('*')
                    .limit(1);
                
                if (!error && data && data.length > 0) {
                    schema[table] = {
                        columns: Object.keys(data[0]),
                        sample: data[0]
                    };
                } else {
                    schema[table] = {
                        columns: [],
                        sample: null,
                        error: error ? error.message : 'No data'
                    };
                }
            } catch (err) {
                schema[table] = {
                    columns: [],
                    sample: null,
                    error: err.message
                };
            }
        }

        res.json({
            success: true,
            data: schema
        });
    } catch (error) {
        console.error('Schema error:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to retrieve schema',
            message: error.message
        });
    }
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error('Unhandled error:', err);
    res.status(500).json({
        success: false,
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'development' ? err.message : 'Something went wrong'
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({
        success: false,
        error: 'Endpoint not found',
        path: req.path,
        method: req.method
    });
});

// Start server
app.listen(PORT, () => {
    console.log(`🚀 Orphanet API server running on port ${PORT}`);
    console.log(`📊 Health check: http://localhost:${PORT}/health`);
    console.log(`📖 API docs: http://localhost:${PORT}/`);
    console.log(`📈 Stats: http://localhost:${PORT}/api/stats`);
    console.log(`🔍 Example: http://localhost:${PORT}/api/disorders?limit=5`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('👋 SIGTERM received, shutting down gracefully');
    process.exit(0);
});

process.on('SIGINT', () => {
    console.log('👋 SIGINT received, shutting down gracefully');
    process.exit(0);
});