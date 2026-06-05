import requests

urls = [
    "https://docs.smartflo.tatatelebusiness.com/reference/generate-a-token.md",
    "https://docs.smartflo.tatatelebusiness.com/reference/v1callrecords.md",
    "https://docs.smartflo.tatatelebusiness.com/reference/v1authrefresh.md",
    "https://docs.smartflo.tatatelebusiness.com/reference/v1live_calls.md",
    "https://docs.smartflo.tatatelebusiness.com/reference/fetch-multiple-users.md",
]

combined = "# SmartFlo API Reference — Relevant Endpoints\n\n"
for url in urls:
    r = requests.get(url)
    combined += f"\n\n---\n\n{r.text}"

with open("docs/tts_api_reference.md", "w") as f:
    f.write(combined)

print("Done — docs/tts_api_reference.md created")