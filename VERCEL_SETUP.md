# Website Eater on Vercel + Railway

## 🚀 Quick Setup (10 minutes)

### Step 1: Deploy Backend to Railway (5 min)

1. **Sign up** at [railway.app](https://railway.app)

2. **New Project → Deploy from GitHub**

3. **Select** your `website-eater` repository

4. **Add Variables** in Railway dashboard:
   ```
   GOOGLE_API_KEY = AIzaSyCKtex06bqi1wZoChfznuc5ruTXUif1KYQ
   GEMINI_MODEL = gemini-2.5-pro-preview-03-25
   ```

5. **Wait for deployment** (2-3 minutes)

6. **Copy your Railway URL** (looks like: `website-eater-production.up.railway.app`)

### Step 2: Deploy Frontend to Vercel (5 min)

1. **Sign up** at [vercel.com](https://vercel.com)

2. **Import Git Repository** → Select `website-eater`

3. **Configure Project:**
   - Framework Preset: `Other`
   - Root Directory: `./`
   - Build Command: `echo "No build needed"`
   - Output Directory: `frontend`

4. **Add Environment Variable:**
   - Name: `BACKEND_URL`
   - Value: Your Railway URL from Step 1

5. **Update** `vercel.json`:
   ```json
   {
     "routes": [
       {
         "src": "/api/(.*)",
         "dest": "https://YOUR-APP.up.railway.app/api/$1"
       }
     ]
   }
   ```

6. **Deploy!**

## 🎯 Result

- **Frontend**: `your-app.vercel.app` (Fast, global CDN)
- **Backend**: `your-app.railway.app` (Always running Python)
- **Full functionality** with memory storage!

## 💡 Why This Works Better

1. **Vercel**: Optimized for frontend, amazing DX, instant deploys
2. **Railway**: Perfect for Python backends, generous free tier
3. **Split architecture**: Best performance and scalability

## 🔧 Alternative: All on Railway

If you prefer simplicity:
```bash
# Just use Railway for everything!
railway up
```

Railway can host both frontend + backend together.
