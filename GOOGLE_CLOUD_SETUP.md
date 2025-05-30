# Google Cloud Setup Guide for Paid Gemini API Access

## Step 1: Go to Google Cloud Console
1. Visit: https://console.cloud.google.com/
2. Make sure you're logged in with jamesBrady0813@gmail.com

## Step 2: Create or Select a Project
1. Click the project dropdown at the top
2. Click "New Project" or select an existing one
3. Give it a name like "Website-Eater"

## Step 3: Enable Billing for the Project
1. Go to: https://console.cloud.google.com/billing
2. Link your billing account to the project
3. Confirm billing is active

## Step 4: Enable the Generative Language API
1. Go to: https://console.cloud.google.com/apis/library
2. Search for "Generative Language API"
3. Click on it and press "ENABLE"

## Step 5: Create a New API Key
1. Go to: https://console.cloud.google.com/apis/credentials
2. Click "+ CREATE CREDENTIALS"
3. Select "API Key"
4. Copy the new key immediately!

## Step 6: (Optional) Restrict the API Key
1. Click on your new API key
2. Under "API restrictions", select "Restrict key"
3. Choose "Generative Language API"
4. Save

## Step 7: Update Your Website Eater
Replace your old API key with the new one from Google Cloud Console.

## Important Notes:
- Google AI Studio keys = Free tier only (limited quota)
- Google Cloud Console keys = Paid tier (much higher quotas)
- Billing must be enabled on the PROJECT, not just the account
- The API must be ENABLED in the project

## Pricing:
- Gemini 2.5 Pro: ~$1.25 per 1M input tokens
- Gemini 2.5 Flash: ~$0.075 per 1M input tokens
- No minimum charges, pay only for what you use
