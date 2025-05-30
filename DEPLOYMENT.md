# Deployment Guide for Website Eater

This guide explains how to deploy Website Eater's backend to various cloud platforms.

## 🎯 Overview

Website Eater consists of:
- **Frontend**: Static HTML/JS (can be hosted on Netlify, Vercel, GitHub Pages)
- **Backend**: Python Flask API (needs a Python hosting service)

## 🚀 Quick Deploy Options

### Option 1: Heroku (Recommended for beginners)

1. **Create a Heroku account** at https://heroku.com

2. **Install Heroku CLI**: https://devcenter.heroku.com/articles/heroku-cli

3. **Deploy the backend**:
```bash
# From the project root
heroku create your-app-name
heroku config:set GOOGLE_API_KEY=your-api-key-here
git push heroku main
```

4. **Update frontend to use your backend**:
   - Edit `netlify.toml` and replace `your-backend-url.herokuapp.com` with your Heroku app URL

### Option 2: Railway (Modern & Simple)

1. **Fork the repository** on GitHub

2. **Go to Railway**: https://railway.app

3. **New Project → Deploy from GitHub repo**

4. **Add environment variables**:
   - `GOOGLE_API_KEY`: Your API key

5. **Railway will auto-deploy!**

### Option 3: Render (Free tier available)

1. **Create account** at https://render.com

2. **New → Web Service**

3. **Connect GitHub repo**

4. **Configure**:
   - Build Command: `cd backend && pip install -r requirements.txt`
   - Start Command: `cd backend && gunicorn app_url_digestion:app`
   - Add environment variable: `GOOGLE_API_KEY`

### Option 4: PythonAnywhere

1. **Sign up** at https://www.pythonanywhere.com

2. **Upload your code**

3. **Set up Flask app** in Web tab

4. **Configure environment variables**

## 📝 Environment Variables

All platforms need these environment variables:

```
GOOGLE_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-pro-preview-03-25
```

## 🔧 Local Development

To run both frontend and backend locally:

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python app_url_digestion.py

# Terminal 2: Frontend (optional)
cd frontend
python -m http.server 8000
```

## 🌐 Frontend Configuration

After deploying your backend, update the frontend API URL:

### For Netlify:
Edit `netlify.toml`:
```toml
[[redirects]]
  from = "/api/*"
  to = "https://your-backend.herokuapp.com/api/:splat"
  status = 200
```

### For standalone frontend:
Update the API_BASE in your frontend code to point to your backend URL.

## 🔒 Security Notes

- Never commit `.env` files
- Use environment variables for sensitive data
- Enable CORS only for your frontend domain in production
- Consider adding rate limiting for public deployments

## 💡 Tips

1. **Start with local testing** before deploying
2. **Use the free tiers** to test your deployment
3. **Monitor your API usage** to avoid unexpected charges
4. **Set up GitHub Actions** for automatic deployments

## 🆘 Troubleshooting

### "Module not found" errors
- Make sure all dependencies are in `requirements.txt`
- Check Python version compatibility

### "API key not working"
- Verify environment variables are set correctly
- Check if Generative Language API is enabled

### CORS errors
- Ensure your backend allows requests from your frontend domain
- Check the Flask-CORS configuration

## 📚 Resources

- [Flask Deployment Options](https://flask.palletsprojects.com/en/3.0.x/deploying/)
- [Google Cloud API Setup](https://console.cloud.google.com)
- [Heroku Python Guide](https://devcenter.heroku.com/articles/getting-started-with-python)
- [Railway Docs](https://docs.railway.app/)

---

Need help? Open an issue on GitHub!
