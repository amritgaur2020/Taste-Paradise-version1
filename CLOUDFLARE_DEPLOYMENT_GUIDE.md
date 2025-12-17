# Cloudflare Workers Deployment Guide for Taste Paradise Backend

## Prerequisites
- Cloudflare Account
- Wrangler CLI installed (`npm install -g @cloudflare/wrangler`)
- Git and GitHub account
- Python 3.9+ installed locally

## Step 1: Install Wrangler CLI

```bash
npm install -g @cloudflare/wrangler
# or
curl -fsSL https://cli.cloudflare.com | /bin/bash
```

## Step 2: Authenticate with Cloudflare

```bash
wrangler login
```
This will open your browser and authenticate your Cloudflare account.

## Step 3: Clone and Setup Repository

```bash
git clone https://github.com/amritgaur2020/Taste-Paradise-version1.git
cd Taste-Paradise-version1
pip install -r requirements.txt
```

## Step 4: Configure Environment Variables

Create a `.env.local` file in the root directory with your MongoDB URI:

```
MONGODB_URI=your_mongodb_atlas_connection_string
```

## Step 5: Deploy to Cloudflare Workers

```bash
wrangler deploy
```

This command will:
1. Build your Python FastAPI application
2. Deploy it to Cloudflare Workers globally
3. Provide you with a deployment URL

## Step 6: Verify Deployment

Your API will be available at:
```
https://taste-paradise-backend.yourdomain.workers.dev
```

Test it with:
```bash
curl https://taste-paradise-backend.yourdomain.workers.dev/
```

## Step 7: Connect Frontend

Update your frontend API base URL to:
```javascript
const API_BASE_URL = 'https://taste-paradise-backend.yourdomain.workers.dev';
```

## Troubleshooting

### Module Not Found Errors
Ensure all dependencies in `requirements.txt` are compatible with Cloudflare Workers

### Database Connection Issues
Verify MongoDB Atlas IP whitelist includes Cloudflare Worker IPs:
- Add `0.0.0.0/0` or specific Cloudflare IPs to IP Access List

### Deployment Fails
```bash
wrangler tail  # View logs
wrangler deployments list  # Check deployment history
```

## Monitoring

```bash
# View real-time logs
wrangler tail

# Check deployment status
wrangler deployments list

# Rollback to previous version
wrangler rollback
```

## Production Deployment

For production, update `wrangler.toml`:

```toml
[env.production]
name = "taste-paradise-backend-prod"
vars = { ENVIRONMENT = "production" }
routes = [{pattern = "api.yourdomain.com/*", zone_name = "yourdomain.com"}]
```

Deploy to production:
```bash
wrangler deploy --env production
```

## Costs

- First 100,000 requests/day: FREE
- Additional requests: $0.50 per million
- No charges for CPU time

## Next Steps

1. Connect custom domain
2. Set up monitoring and alerts
3. Configure CI/CD pipeline
4. Scale as needed
