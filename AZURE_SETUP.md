# 🎯 Azure Speech Services Setup Guide

This guide will help you set up Azure Speech Services for the Audio Transcription Application.

## 📋 Prerequisites

- Azure subscription (free tier available)
- Azure Portal access

## 🚀 Step-by-Step Setup

### 1. Create Azure Speech Service

1. **Go to Azure Portal**
   - Navigate to [https://portal.azure.com](https://portal.azure.com)
   - Sign in with your Azure account

2. **Create Speech Resource**
   - Click "Create a resource"
   - Search for "Speech"
   - Select "Speech" from Microsoft
   - Click "Create"

3. **Configure Speech Service**
   - **Subscription**: Select your Azure subscription
   - **Resource Group**: Create new or select existing
   - **Region**: Choose a region close to you (e.g., `eastus`, `westus2`, `northeurope`)
   - **Name**: Give your resource a unique name
   - **Pricing Tier**: 
     - **Free (F0)**: 5 hours of audio per month
     - **Standard (S0)**: Pay-as-you-go pricing

4. **Review and Create**
   - Review your settings
   - Click "Create"
   - Wait for deployment to complete

### 2. Get Your Credentials

1. **Navigate to Your Speech Resource**
   - Go to "All resources" in Azure Portal
   - Find and click on your Speech service

2. **Get Keys and Endpoint**
   - In the left menu, click "Keys and Endpoint"
   - Copy **Key 1** (this is your `AZURE_SPEECH_KEY`)
   - Copy **Region** (this is your `AZURE_SPEECH_REGION`)

### 3. Configure Application

1. **Copy Environment Template**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env File**
   ```bash
   # Replace with your actual values
   AZURE_SPEECH_KEY=your_actual_key_here
   AZURE_SPEECH_REGION=your_actual_region_here
   ```

3. **Set Environment Variables**
   
   **Linux/Mac:**
   ```bash
   export AZURE_SPEECH_KEY="your_actual_key_here"
   export AZURE_SPEECH_REGION="your_actual_region"
   ```
   
   **Windows (Command Prompt):**
   ```cmd
   set AZURE_SPEECH_KEY=your_actual_key_here
   set AZURE_SPEECH_REGION=your_actual_region
   ```
   
   **Windows (PowerShell):**
   ```powershell
   $env:AZURE_SPEECH_KEY="your_actual_key_here"
   $env:AZURE_SPEECH_REGION="your_actual_region"
   ```

## 🌍 Available Regions

Common Azure Speech Service regions:

| Region Name | Region Code | Location |
|-------------|-------------|----------|
| East US | `eastus` | Virginia |
| East US 2 | `eastus2` | Virginia |
| West US | `westus` | California |
| West US 2 | `westus2` | Washington |
| Central US | `centralus` | Iowa |
| North Europe | `northeurope` | Ireland |
| West Europe | `westeurope` | Netherlands |
| Southeast Asia | `southeastasia` | Singapore |
| Japan East | `japaneast` | Tokyo |
| Australia East | `australiaeast` | New South Wales |

## 💰 Pricing Information

### Free Tier (F0)
- **Real-time Speech Recognition**: 5 hours per month
- **Batch Speech Recognition**: 5 hours per month
- **Perfect for testing and development**

### Standard Tier (S0)
- **Real-time Speech Recognition**: $1.00 per hour
- **Batch Speech Recognition**: $0.80 per hour
- **Pay only for what you use**

## 🔍 Testing Your Setup

1. **Test Backend Health**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Expected Response**
   ```json
   {
     "status": "healthy",
     "timestamp": "2024-01-XX...",
     "azure_speech_configured": true,
     "azure_speech_region": "eastus"
   }
   ```

## ❗ Troubleshooting

### Common Issues

1. **"azure_speech_configured": false**
   - Check if environment variables are set correctly
   - Restart the backend after setting variables

2. **Authentication Error**
   - Verify your Azure Speech key is correct
   - Ensure the key hasn't expired
   - Check if the region matches your resource

3. **Region Error**
   - Verify the region code matches exactly
   - Common mistake: using display name instead of code
   - Example: Use `eastus` not `East US`

4. **Service Unavailable**
   - Check if Azure Speech service is available in your region
   - Verify your Azure subscription is active
   - Check Azure service status

### Debug Commands

```bash
# Check environment variables
echo $AZURE_SPEECH_KEY
echo $AZURE_SPEECH_REGION

# Test Azure Speech service directly
curl -X POST "https://$AZURE_SPEECH_REGION.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=en-US" \
  -H "Ocp-Apim-Subscription-Key: $AZURE_SPEECH_KEY" \
  -H "Content-Type: audio/wav"
```

## 🔒 Security Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** for credentials
3. **Rotate keys regularly** in Azure Portal
4. **Use managed identities** in production
5. **Monitor usage** to avoid unexpected charges

## 📚 Additional Resources

- [Azure Speech Service Documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/)
- [Azure Speech SDK for Python](https://docs.microsoft.com/en-us/python/api/azure-cognitiveservices-speech/)
- [Azure Pricing Calculator](https://azure.microsoft.com/en-us/pricing/calculator/)
- [Azure Free Account](https://azure.microsoft.com/en-us/free/)

## 🎯 Next Steps

After completing this setup:

1. Start the backend: `./start_backend.sh`
2. Start the frontend: `./start_frontend.sh`
3. Test the application at `http://localhost:7860`
4. Begin recording and transcribing audio!