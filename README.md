# Orphanet API

A simple Node.js API to query rare disease data from the Orphanet database stored in Supabase.

## Features

- 🏥 **Comprehensive Data**: Access to disorders, genes, HPO terms, and clinical data
- 🔍 **Search Functionality**: Search disorders by name
- 📊 **Pagination**: Efficient data retrieval with pagination
- 🚀 **Fast Performance**: Built with Express.js and Supabase
- 🔐 **Secure**: Uses Supabase Row Level Security
- 📖 **Well Documented**: Clear API documentation and examples

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Environment Setup

Copy the example environment file and configure your Supabase credentials:

```bash
cp env.example .env
```

Edit `.env` with your Supabase configuration:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anonymous-key-here
PORT=3000
NODE_ENV=development
```

### 3. Start the Server

```bash
# Production mode
npm start

# Development mode (with auto-reload)
npm run dev
```

### 4. Test the API

```bash
# Run test suite
npm test

# Or test manually
curl http://localhost:3000/health
```

## API Endpoints

### General

- `GET /` - API information and documentation
- `GET /health` - Health check endpoint
- `GET /api/stats` - Database statistics

### Disorders

- `GET /api/disorders` - List all disorders (paginated)
- `GET /api/disorders/:orpha_code` - Get specific disorder by Orpha code
- `GET /api/disorders/search/:query` - Search disorders by name

### Genes

- `GET /api/genes` - List all genes (paginated)
- `GET /api/genes/:symbol` - Get specific gene by symbol

### HPO Terms

- `GET /api/hpo-terms` - List HPO terms (paginated)

## Query Parameters

### Pagination

All list endpoints support pagination:

- `page` - Page number (default: 1)
- `limit` - Items per page (default: 20, max: 100)

**Example:**
```
GET /api/disorders?page=2&limit=50
```

## Response Format

All API responses follow this structure:

```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1000,
    "totalPages": 50
  }
}
```

## Examples

### Get Disorder Details

```bash
curl "http://localhost:3000/api/disorders/58"
```

Response includes:
- Basic disorder information
- Synonyms
- Associated genes
- Clinical signs (HPO terms)
- Prevalence data
- Classifications

### Search Disorders

```bash
curl "http://localhost:3000/api/disorders/search/alexander"
```

### Get Gene Information

```bash
curl "http://localhost:3000/api/genes/GFAP"
```

### Database Statistics

```bash
curl "http://localhost:3000/api/stats"
```

## Data Sources

This API queries data from:

- **Disorders**: Main rare disease information from Orphanet
- **Genes**: Gene associations and external references
- **HPO Terms**: Human Phenotype Ontology clinical signs
- **Prevalence**: Epidemiological data
- **Classifications**: Disease hierarchies and relationships

## Error Handling

The API returns appropriate HTTP status codes:

- `200` - Success
- `404` - Resource not found
- `500` - Server error

Error responses include:
```json
{
  "success": false,
  "error": "Error description",
  "message": "Detailed error message"
}
```

## Development

### Project Structure

```
orphanet-api/
├── server.js          # Main API server
├── test.js            # Test script
├── package.json       # Dependencies and scripts
├── .env              # Environment variables (create from .env.example)
└── README.md         # This file
```

### Adding New Endpoints

1. Add the route in `server.js`
2. Follow the existing error handling pattern
3. Update this README with the new endpoint
4. Add tests in `test.js`

### Database Schema

The API expects these Supabase tables:
- `disorders`
- `disorder_synonyms`
- `genes`
- `disorder_gene_associations`
- `hpo_terms`
- `disorder_hpo_associations`
- `prevalence_data`
- `disorder_classifications`
- And more...

## Production Deployment

### Environment Variables

Set these in production:

```env
NODE_ENV=production
PORT=3000
SUPABASE_URL=your-production-supabase-url
SUPABASE_ANON_KEY=your-production-anon-key
```

### Docker (Optional)

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

### Performance Tips

- Use pagination for large datasets
- Implement caching for frequently accessed data
- Monitor Supabase usage and optimize queries
- Use connection pooling for high traffic

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Check the API documentation at `GET /`
- Review the test script in `test.js`
- Check Supabase logs for database issues