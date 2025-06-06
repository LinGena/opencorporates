import os


def load_proxy(proxy: str, plugin_path: str) -> None:
    proxy = proxy.replace('https://', '').replace('http://', '')
    auth_part, proxy_part = proxy.split('@')
    PROXY_USER, PROXY_PASS = auth_part.split(':')
    PROXY_HOST, PROXY_PORT = proxy_part.split(':')

    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 3,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "webRequest",
            "webRequestBlocking",
            "webRequestAuthProvider"
        ],
        "host_permissions": [
            "<all_urls>"
        ],
        "background": {
            "service_worker": "background.js"
        },
        "minimum_chrome_version": "88"
    }
    """

    background_js = """
    var config = {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                scheme: "http",
                host: "%s",
                port: parseInt(%s)
            },
            bypassList: ["localhost"]
        }
    };

    chrome.proxy.settings.set({value: config, scope: "regular"}, () => {});

    chrome.webRequest.onAuthRequired.addListener(
        (details) => ({
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        }),
        { urls: ["<all_urls>"] },
        ["blocking"]
    );
    """ % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)
    
    os.makedirs(plugin_path, exist_ok=True)

    with open(os.path.join(plugin_path, "manifest.json"), "w") as manifest_file:
        manifest_file.write(manifest_json)

    with open(os.path.join(plugin_path, "background.js"), "w") as background_file:
        background_file.write(background_js)