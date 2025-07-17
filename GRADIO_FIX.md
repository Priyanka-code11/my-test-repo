# 🔧 Gradio Version Fix Guide

## Problem
You're getting this error:
```
TypeError: EventListener._setup.<locals>.event_trigger() got an unexpected keyword argument 'every'
```

## Cause
This error occurs when you have an older version of Gradio that doesn't support the `every` parameter in `app.load()`.

## 🚀 Solutions

### Solution 1: Upgrade Gradio (Recommended)

```bash
cd frontend
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade gradio
```

### Solution 2: Use Compatible Version

Use the compatible version I've created:

```bash
cd frontend
python app_compatible.py
```

### Solution 3: Fix Current app.py

The original `app.py` has been updated with a try-catch block that handles both versions:

```bash
cd frontend
python app.py
```

## 🔍 Check Your Gradio Version

```bash
python -c "import gradio; print(gradio.__version__)"
```

- **Gradio 4.0+**: Use `app.py` (with auto-refresh)
- **Gradio < 4.0**: Use `app_compatible.py` (with manual refresh)

## 📋 Step-by-Step Fix

1. **Check Backend is Running**:
   ```bash
   # Terminal 1 - Start backend
   export AZURE_SPEECH_KEY="your_key"
   export AZURE_SPEECH_REGION="your_region"
   cd backend
   python main.py
   ```

2. **Choose Your Frontend**:
   
   **Option A - Try upgraded version**:
   ```bash
   # Terminal 2
   cd frontend
   pip install --upgrade gradio
   python app.py
   ```
   
   **Option B - Use compatible version**:
   ```bash
   # Terminal 2
   cd frontend
   python app_compatible.py
   ```

## ✅ Expected Behavior

After fixing:
- Frontend should start without errors
- You'll see "Azure Speech Audio Transcription" interface
- Backend status should show Azure configuration
- Recording and transcription should work normally

## 🔄 Differences Between Versions

| Feature | app.py (Gradio 4.0+) | app_compatible.py (All versions) |
|---------|---------------------|-----------------------------------|
| Auto-refresh | ✅ Every 2 seconds | ❌ Manual refresh button |
| Real-time updates | ✅ Automatic | 🔄 Click "🔄 Refresh Status" |
| Compatibility | Gradio 4.0+ | All Gradio versions |
| Features | Full features | Same features, manual refresh |

## 💡 Tips

1. **For Development**: Use `app_compatible.py` for maximum compatibility
2. **For Production**: Upgrade to Gradio 4.0+ and use `app.py`
3. **Real-time Updates**: In compatible version, click "🔄 Refresh Status" to see live transcriptions

## 🆘 Still Having Issues?

If you still get errors:

1. **Check Python Version**: Ensure Python 3.8+
2. **Virtual Environment**: Make sure you're using a clean virtual environment
3. **Dependencies**: Reinstall all dependencies:
   ```bash
   cd frontend
   pip uninstall gradio
   pip install gradio>=4.0.0
   ```

## 🎯 Quick Test

Once fixed, test by:
1. Starting backend with Azure credentials
2. Starting frontend (either version)
3. Checking that backend status shows "✅ Azure Speech Backend Online"
4. Testing recording functionality