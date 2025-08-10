# Car Image API

A FastAPI service that returns car image URLs from Cloudinary based on brand, model, and year.

## 🚀 Live API

**Base URL**: `https://your-deployment-url.vercel.app`

**Endpoint**: `/image?brand=<brand>&model=<model>&year=<year>`

## 📖 Example Usage

```bash
# Get Ford Focus 2020 images
curl "https://your-deployment-url.vercel.app/image?brand=ford&model=focus&year=2020"
```

**Response**:
```json
{
  "url": "https://res.cloudinary.com/dsg6pa4hp/image/upload/v1754812073/izmostock/Ford_Ford_Focus_Titanium_Business_Hatchback_2020.jpg",
  "public_id": "izmostock/Ford_Ford_Focus_Titanium_Business_Hatchback_2020",
  "tags": ["brand:ford", "model:focus-titanium-business-hatchback", "year:2020"],
  "count": 8,
  "query": {
    "brand": "ford",
    "model": "focus", 
    "year": "2020"
  }
}
```

## 🔧 Environment Variables Required

Set these in your Vercel project settings:

- `CLOUDINARY_CLOUD_NAME`: Your Cloudinary cloud name
- `CLOUDINARY_API_KEY`: Your Cloudinary API key  
- `CLOUDINARY_API_SECRET`: Your Cloudinary API secret

## 🏗️ Tech Stack

- **FastAPI**: Python web framework
- **Cloudinary**: Image storage and management
- **Vercel**: Serverless deployment platform

## 📁 Project Structure

```
.
├── api/
│   └── main.py              # FastAPI application
├── vercel.json              # Vercel configuration
├── requirements-vercel.txt  # Python dependencies
└── package.json             # Node.js metadata
```

## 🚀 Deploy Your Own

1. Fork this repository
2. Connect to Vercel via GitHub
3. Set environment variables in Vercel dashboard
4. Deploy automatically on every push

## 📊 Data Source

Images scraped from [izmostock.com](https://www.izmostock.com/) covering 76+ car brands and thousands of models.
