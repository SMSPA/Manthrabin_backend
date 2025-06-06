import re
import json
import requests
from typing import List, Dict, Any


JINA_API_TOKEN = "jina_ee21df2e2d974094a5b729cdaa6224cbC8mfJB9q19JEv_ly3iOTkN863UiP"


def fetch_links_content(text: str) -> List[Dict[str, Any]]:
    """Extracts URLs from input text and fetches their content using Jina Reader API.

    If the response is JSON → it's considered an error.
    If the response is plain text → it's considered valid page content.

    Args:
        text: A string that may contain one or more HTTP/HTTPS URLs.

    Returns:
        A list of dictionaries containing:
            - 'link': The original extracted URL.
            - 'content': The text content (if valid), or None.
            - 'error': Error message if any.
    """
    urls = re.findall(r'https?://[^\s)>\]\'"]+', text)
    headers = {
        "Authorization": f"Bearer {JINA_API_TOKEN}"
    }

    results = []

    for url in urls:
        proxy_url = f"https://r.jina.ai/{url}"
        try:
            response = requests.get(proxy_url, headers=headers, timeout=10)

            # Try to parse as JSON (likely an error response)
            try:
                error_data = response.json()
                if isinstance(error_data, dict) and "message" in error_data:
                    results.append({
                        "Link": url,
                        "Content": None,
                        "error": error_data.get("readableMessage", "Unknown error")
                    })
                    continue
            except json.JSONDecodeError:
                # Not JSON → treat as valid content
                pass

            # If it's not JSON, assume it's the content
            results.append({
                "Link": url,
                "Content": response.text.strip()
            })

        except requests.exceptions.RequestException as e:
            results.append({
                "Link": url,
                "Content": None,
                "error": str(e)
            })

    return results

if __name__ == "__main__":
    text = "محتوای این لینک رو بخون: https://laravel-livewire.com/ و این یکی: https://invalid-url.com"
    output = fetch_links_content(text)
    print(json.dumps(output, indent=2, ensure_ascii=False))
