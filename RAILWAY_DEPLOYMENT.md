# Railway Deployment Guide for Inner Joy Studio Bot

## Prerequisites
- Railway account (sign up at https://railway.app)
- GitHub account
- Your code pushed to a GitHub repository

## Step 1: Prepare Environment Variables

You'll need to set these environment variables in Railway. Get them ready:

### Required Variables:
```
RESPOND_API_KEY=your_respond_io_api_key
RESPOND_SPACE_ID=your_space_id
ZOOM_PREVIEW_LINK=your_zoom_link
GOOGLE_SHEETS_ID=your_google_sheet_id
```

### Google Service Account Credentials:
You need to convert your `service-account-credentials.json` to a base64 string:

```bash
# Run this command in your project directory:
cat service-account-credentials.json | base64
```

Copy the output and save it as:
```
GOOGLE_SERVICE_ACCOUNT_JSON=<base64_encoded_credentials>
```

## Step 2: Push Code to GitHub

1. Initialize git (if not already done):
   ```bash
   cd /Users/apple/Desktop/Ineke
   git init
   git add .
   git commit -m "Initial commit for Railway deployment"
   ```

2. Create a new repository on GitHub

3. Push your code:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git branch -M main
   git push -u origin main
   ```

## Step 3: Deploy to Railway

1. **Go to Railway Dashboard**
   - Visit https://railway.app
   - Click "New Project"

2. **Deploy from GitHub**
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Click "Deploy Now"

3. **Add Environment Variables**
   - Go to your project
   - Click on the service
   - Go to "Variables" tab
   - Click "RAW Editor"
   - Paste all your environment variables:

   ```
   RESPOND_API_KEY=your_actual_api_key_here
   RESPOND_SPACE_ID=your_actual_space_id_here
   ZOOM_PREVIEW_LINK=https://us02web.zoom.us/j/YOUR_MEETING_ID
   GOOGLE_SHEETS_ID=your_google_sheet_id_here
   GOOGLE_SERVICE_ACCOUNT_JSON=<paste_base64_encoded_json_here>
   PORT=9000
   FLASK_ENV=production
   ```

4. **Generate Domain**
   - Go to "Settings" tab
   - Scroll to "Networking"
   - Click "Generate Domain"
   - Copy the domain (e.g., `your-app.up.railway.app`)

## Step 4: Update Respond.io Webhook

1. Go to Respond.io Settings
2. Navigate to Integrations → Webhooks
3. Update webhook URL to: `https://your-app.up.railway.app/webhook`
4. Test the webhook

## Step 5: Update Code for Railway (if needed)

The code should work as-is, but verify `app.py` has proper port handling:

```python
if __name__ == '__main__':
    port = int(os.getenv('PORT', 9000))
    app.run(host='0.0.0.0', port=port, debug=False)
```

## Step 6: Monitor Deployment

1. **Check Logs**
   - In Railway dashboard, click on your service
   - Go to "Deployments" tab
   - Click on latest deployment
   - View build and runtime logs

2. **Verify App is Running**
   - Visit: `https://your-app.up.railway.app/`
   - You should see: "Inner Joy Studio WhatsApp Automation is running!"

3. **Test Webhook**
   - Send a test message to your WhatsApp number
   - Check Railway logs for incoming webhooks

## Troubleshooting

### Build Fails
- Check logs in Railway dashboard
- Verify all dependencies in `requirements.txt`
- Make sure `railway.json` is present

### Runtime Errors
- Check environment variables are set correctly
- Verify Google Service Account JSON is base64 encoded properly
- Check logs for specific error messages

### Webhook Not Working
- Verify webhook URL in Respond.io is correct
- Check Railway logs for incoming requests
- Test webhook using Railway URL

### Google Sheets Not Working
- Verify Service Account has access to the sheet
- Check that base64 encoding is correct
- Verify GOOGLE_SHEETS_ID is correct

## Important Notes

1. **Don't commit secrets**: `.env` and `service-account-credentials.json` are in `.gitignore`
2. **Railway gives you 500 hours/month free**: Monitor usage
3. **Logs are important**: Always check logs when debugging
4. **Environment variables**: Can be updated anytime in Railway dashboard

## Commands for Reference

### Check if service-account-credentials.json is in .gitignore:
```bash
cat .gitignore | grep service-account
```

### Convert credentials to base64 (macOS/Linux):
```bash
cat service-account-credentials.json | base64
```

### Convert credentials to base64 (Windows PowerShell):
```powershell
[Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Content service-account-credentials.json -Raw)))
```

### Test Railway deployment locally:
```bash
# Set environment variables
export PORT=9000
export FLASK_ENV=production
# ... set other variables ...

# Run with gunicorn (same as Railway)
gunicorn app:app
```

## Success Checklist

- [ ] Code pushed to GitHub
- [ ] Railway project created
- [ ] All environment variables set
- [ ] Domain generated
- [ ] Respond.io webhook updated
- [ ] Test message sent and received
- [ ] Reminders scheduled correctly
- [ ] Google Sheets updating properly

## Support

If you encounter issues:
1. Check Railway logs first
2. Verify all environment variables
3. Test webhook endpoint manually
4. Check Google Sheets permissions

Your app is now live on Railway! 🚀
