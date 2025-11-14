# Gemini AI Chatbot Setup Guide

## Getting Your Gemini API Key

1. **Visit Google AI Studio** (Free Tier Available):
   - Go to: https://aistudio.google.com/app/apikey
   - Sign in with your Google account (create one if needed)
   - Click "Create API Key"
   - Select a project (or create a new one)
   - Copy the API key

2. **Add to Environment**:
   - Option A: Create a `.env` file in your project root with:
     ```
     GEMINI_API_KEY="AIzaSyCZd8F9XBxDQe5CkLcqidG8wZxbfq8MzXc"
     ```
   - Option B: Set as environment variable on your system
   
   **On Windows PowerShell:**
   ```powershell
   $env:GEMINI_API_KEY="AIzaSyCZd8F9XBxDQe5CkLcqidG8wZxbfq8MzXc"
   ```

   **On Windows Command Prompt:**
   ```cmd
   set GEMINI_API_KEY=your-api-key-here
   ```

3. **Install python-dotenv (Optional but Recommended)**:
   ```powershell
   pip install python-dotenv
   ```

   Then modify `ecommerce/settings.py` to add:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

4. **Restart Django**:
   ```powershell
   python manage.py runserver
   ```

## Features

- ✅ AI-powered customer support chatbot
- ✅ Context-aware responses about products and store
- ✅ Real-time responses using Google Gemini API
- ✅ Safety filters to prevent harmful content
- ✅ Product recommendations
- ✅ Order and checkout assistance

## Testing

1. Visit your store at http://127.0.0.1:8000/
2. Click the 💬 chatbot button in the bottom-right
3. Ask questions like:
   - "What products do you have?"
   - "How do I place an order?"
   - "Tell me about your delivery"
   - "What's the price of [product name]?"

## Troubleshooting

**Error: "Invalid API Key"**
- Verify your API key is correct in `.env` or environment variables
- Check that the key hasn't expired

**Error: "API not enabled"**
- Ensure you have Google AI Studio API enabled
- Create a new API key at https://aistudio.google.com/app/apikey

**No response from chatbot**
- Check browser console for errors (F12)
- Verify Django is running and the `/chatbot/` endpoint is accessible
- Check server logs for detailed error messages

**Slow responses**
- This is normal - the first request may take 2-3 seconds
- Gemini API response time improves with faster internet

## Cost

The Gemini API is **FREE** with generous usage limits (up to 60 requests per minute).
