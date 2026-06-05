# Gemini 2.0 Flash — Audio Analysis Notes

## Model
gemini-2.0-flash

## Endpoint
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent
Header: x-goog-api-key: YOUR_KEY

## Audio Input Pattern (Python)
import google.generativeai as genai
import base64

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash")

# For files < ~10MB: inline base64
with open("call.mp3", "rb") as f:
    audio_data = base64.b64encode(f.read()).decode()

response = model.generate_content([
    {"inline_data": {"mime_type": "audio/mpeg", "data": audio_data}},
    ANALYSIS_PROMPT
])

# For files > 10MB: use File API
import google.generativeai as genai
audio_file = genai.upload_file("call.mp3", mime_type="audio/mpeg")
response = model.generate_content([audio_file, ANALYSIS_PROMPT])

## Supported Languages (confirmed)
Hindi, Kannada, Telugu, Tamil, Malayalam, Marathi, English, Hinglish (code-switching)

## Pricing (approximate)
Audio input: ~$0.001 per minute
Output tokens: ~$0.0006 per 1K tokens
Typical call analysis (5 min call): ~$0.01–0.03 total

## Key Limitation
Max inline audio: ~20MB
Max via File API: 2GB
File API uploaded files expire after 48 hours
