# Deploy Car Image API to Vercel

## 🚀 Quick Deployment Steps

### 1. **Install Vercel CLI**
```bash
npm i -g vercel
```

### 2. **Login to Vercel**
```bash
vercel login
```

### 3. **Deploy**
```bash
vercel --prod
```

### 4. **Set Environment Variables**
In your Vercel dashboard or via CLI:
```bash
vercel env add CLOUDINARY_CLOUD_NAME
vercel env add CLOUDINARY_API_KEY  
vercel env add CLOUDINARY_API_SECRET
```

Use these values:
- `CLOUDINARY_CLOUD_NAME`: `dsg6pa4hp`
- `CLOUDINARY_API_KEY`: `573184522222431`
- `CLOUDINARY_API_SECRET`: `EoEztHoWoi3aksb8m4kT3uoxQ4Q`

## 📁 File Structure for Vercel

```
car image scraper/
├── api/
│   └── main.py              # FastAPI app (serverless function)
├── vercel.json              # Vercel configuration
├── requirements-vercel.txt  # Python dependencies
├── package.json             # Node.js metadata
└── env.example              # Environment variables template
```

## 🔗 API Endpoints

Once deployed, your API will be available at:
- **Base URL**: `https://your-project.vercel.app`
- **Car Images**: `https://your-project.vercel.app/image?brand=ford&model=focus&year=2020`

## 🧪 Test After Deployment

```bash
# Replace with your actual Vercel URL
curl "https://your-project.vercel.app/image?brand=ford&model=focus&year=2020"
```

## 📝 Notes

- Vercel automatically detects Python and installs dependencies from `requirements-vercel.txt`
- The API runs as serverless functions (cold starts ~1-2s)
- All routes are handled by `/api/main.py`
- Environment variables must be set in Vercel dashboard for production

