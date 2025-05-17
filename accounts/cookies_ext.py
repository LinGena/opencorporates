import os
import json
import shutil


def load_cookies(domain: str, cookies: dict, plugin_base_path: str) -> str:
    """
    Generate a Chrome extension that preloads the given cookies.

    :param cookies: List of dicts, each with keys:
        - url           (e.g. "https://example.com")
        - name
        - value
        - domain        (e.g. "www.facebook.com")
        - path          (optional, default "/")
        - expirationDate (optional, epoch seconds)
    :param plugin_base_path: base directory where to create plugin subdirs
    :return: full path to the generated extension directory
    """
    raw = [{"name": key, "value": str(value), "domain": domain} for key, value in cookies.items()]
    cookies = []
    for c in raw:
        cookies.append({
            "url": f"https://{c['domain']}/",
            "domain": c["domain"],
            "name": c["name"].strip(),
            "value": c["value"]
        })
    # Use a stable hash of the cookies list so same inputs reuse the folder
    plugin_path = os.path.join(plugin_base_path, 'cookies_ext')

    # Clear out any old data
    if os.path.isdir(plugin_path):
        shutil.rmtree(plugin_path)
    os.makedirs(plugin_path, exist_ok=True)

    # 1) manifest.json
    manifest = {
      "name": "Automated Cookie Loader",
      "version": "1.0.0",
      "manifest_version": 3,
      "permissions": ["cookies", "storage"],
      "host_permissions": ["<all_urls>"],
      "background": {"service_worker": "background.js"},
      "minimum_chrome_version": "88"
    }
    with open(os.path.join(plugin_path, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # 2) background.js: embed the cookies list and set them on install/startup
    #    We JSON.stringify the Python list for direct use in JS.
    cookies_json = json.dumps(cookies)
    background_js = f"""
    const PRELOAD_COOKIES = {cookies_json};

    async function setAllCookies() {{
      for (const c of PRELOAD_COOKIES) {{
        try {{
          await chrome.cookies.set({{
            url: c.url,
            name: c.name,
            value: c.value,
            domain: c.domain,
            path: "/",
          }});
        }} catch (e) {{
          console.error("Failed to set cookie", c, e);
        }}
      }}
      console.log(`🍪 Injected ${{PRELOAD_COOKIES.length}} cookies`);
    }}

    chrome.runtime.onInstalled.addListener(setAllCookies);
    chrome.runtime.onStartup.addListener(setAllCookies);
    """
    with open(os.path.join(plugin_path, "background.js"), "w", encoding="utf-8") as f:
        f.write(background_js.strip())

    return plugin_path
