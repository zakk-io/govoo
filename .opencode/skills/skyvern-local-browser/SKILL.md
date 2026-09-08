---
name: skyvern-local-browser
description: Lessons learned using Skyvern MCP with localhost - avoids common pitfalls and provides proven workarounds
license: MIT
compatibility: opencode
metadata:
  audience: developers
  type: lessons-learned
---

## Critical Lessons from Real Experience

This skill captures hard-won knowledge from实际使用Skyvern MCP与本地浏览器的 experience. **Read this before attempting any Skyvern + localhost automation.**

---

## Lesson 1: Skyvern Cloud BLOCKS localhost

**What I learned:** `skyvern_navigate(url="http://localhost:8069")` returns error:
```
"The host in your url is blocked: localhost"
```

**Why:** Security restriction - Skyvern Cloud cannot access your local machine directly.

**Solution:** Use JavaScript evaluation to navigate:
```python
# ❌ THIS FAILS
skyvern_navigate(url="http://localhost:8069")

# ✅ THIS WORKS
skyvern_evaluate(expression="window.location.href = 'http://localhost:8069'")
```

**Important:** Always use `skyvern_evaluate` for localhost navigation, never `skyvern_navigate`.

---

## Lesson 2: Skyvern BLOCKS Password Typing

**What I learned:** `skyvern_type(selector="#password", text="admin")` returns error:
```
"Cannot type into password fields — credentials must not be passed through tool calls"
```

**Why:** Security policy - passwords should never pass through tool calls.

**Solution:** Use JavaScript evaluation for password fields:
```python
# ❌ THIS FAILS
skyvern_type(selector="#password", text="admin")

# ✅ THIS WORKS
skyvern_evaluate(expression="document.getElementById('password').value = 'admin'")
```

**Important:** ALL password fields must use JavaScript, even if the field isn't type="password".

---

## Lesson 3: Refs are Stateless in HTTP Mode

**What I learned:** After calling `skyvern_observe`, the refs (e.g., `e33`) become invalid on next call:
```
"Unknown ref 'e33' — call observe first or check ref exists"
```

**Why:** Hosted stateless HTTP mode doesn't persist refs between calls.

**Solution:** Use CSS selectors or intent instead of refs:
```python
# ❌ THIS FAILS (refs are stale)
skyvern_execute(steps=[{"tool": "click", "params": {"ref": "e33"}}])

# ✅ THIS WORKS (use selectors)
skyvern_click(selector="button:has-text('Use another user')")

# ✅ OR THIS (use intent)
skyvern_act(prompt="click the 'Use another user' button")
```

**Important:** Never rely on refs across multiple calls in HTTP mode. Always re-observe or use selectors.

---

## Lesson 4: Screenshots May Timeout

**What I learned:** `skyvern_screenshot()` sometimes hangs with:
```
"Page.screenshot: Timeout 30000ms exceeded"
```

**Why:** Font loading or page rendering delays.

**Solution:** Use alternative verification methods:
```python
# Instead of screenshot, verify via:
skyvern_evaluate(expression="document.title")  # Check page title
skyvern_evaluate(expression="window.location.href")  # Check URL
skyvern_evaluate(expression="document.body.innerText.substring(0, 100)")  # Check content

# If you need visual verification, try with shorter timeout or use Playwright MCP
```

**Important:** Don't rely solely on screenshots for verification. Use multiple signals.

---

## Lesson 5: CDP Connection Requires Active Tunnel

**What I learned:** `skyvern_browser_session_connect(cdp_url=...)` fails with:
```
"Browser session connection failed"
```

**Why:** The tunnel must be active and the CDP URL must be current.

**Solution:** Ensure tunnel is running and capture fresh CDP URL:
```bash
# Start tunnel (keep terminal open)
skyvern browser serve --tunnel --use-local-profile

# Output includes:
# CDP WebSocket URL: wss://YOUR_TUNNEL_URL/devtools/browser/BROWSER_ID
```

Then in your automation:
```python
# Wait for tunnel to be ready
time.sleep(5)

# Use the CDP URL from terminal output
cdp_url = "wss://YOUR_TUNNEL_URL/devtools/browser/BROWSER_ID"
skyvern_browser_session_connect(cdp_url=cdp_url)
```

**Important:** CDP URLs are temporary. If connection fails, restart tunnel.

---

## Lesson 6: Local Profile Clone is Safe

**What I learned:** `--use-local-profile` flag clones your Chrome profile safely.

**Why:** It copies auth-relevant data (cookies, passwords) without modifying original.

**Solution:** Always use this flag for development:
```bash
skyvern browser serve --tunnel --use-local-profile
```

**Benefits:**
- Pre-authenticated sessions (no need to login again)
- Existing cookies and localStorage available
- Safe - original profile never modified

---

## Lesson 7: Page Load Requires Wait

**What I learned:** After navigation, elements may not be immediately available.

**Why:** JavaScript execution and DOM rendering take time.

**Solution:** Always wait after navigation:
```python
# Navigate
skyvern_evaluate(expression="window.location.href = 'http://localhost:8069/web/login'")

# Wait for page to load
skyvern_wait(time_ms=3000)

# Or wait for specific element
skyvern_wait(selector="#login", state="visible")

# Or wait for text
skyvern_wait(text="Login")
```

**Important:** Different pages load at different speeds. Use appropriate wait strategy.

---

## Lesson 8: Odoo Login Form Structure

**What I learned:** Odoo login has a user switcher that must be dismissed first.

**Why:** Default view shows "Choose a user" buttons, not the login form.

**Solution:** Click "Use another user" first:
```python
# 1. Click "Use another user" to show login form
skyvern_click(selector="button:has-text('Use another user')")

# 2. Wait for form to appear
skyvern_wait(selector="#login", state="visible")

# 3. Now fill credentials
skyvern_evaluate(expression="document.getElementById('login').value = 'admin'")
skyvern_evaluate(expression="document.getElementById('password').value = 'admin'")

# 4. Click login
skyvern_click(selector="button[type='submit']")
```

---

## Lesson 9: Login Success Indicators

**What I learned:** Login success can be verified multiple ways.

**Why:** Different Odoo versions/configs may show different indicators.

**Solution:** Check multiple signals:
```python
# 1. Check URL changed from /web/login
url = skyvern_evaluate(expression="window.location.href")
# Should show /odoo/discuss or /odoo

# 2. Check page title changed
title = skyvern_evaluate(expression="document.title")
# Should show "Secretary, OdooBot" or "Administrator, OdooBot"

# 3. Check for backend elements
has_backend = skyvern_evaluate(expression="document.querySelector('.o_main_nav') !== null")
```

**Important:** Don't rely on single indicator. Use multiple checks.

---

## Lesson 10: Tunnel Cleanup is Important

**What I learned:** Leaving tunnels running wastes resources and may cause port conflicts.

**Why:** Each tunnel uses port 9222 and ngrok connection.

**Solution:** Always stop tunnel when done:
```python
# In your automation, cleanup when done
import subprocess
subprocess.run(["pkill", "-f", "skyvern browser serve"])
```

Or manually:
```bash
# Find and kill tunnel process
ps aux | grep "skyvern browser serve"
kill <PID>
```

---

## Complete Workflow Example

```python
import time

def skyvern_odoo_login(username="admin", password="admin"):
    """Login to Odoo using Skyvern MCP with all lessons applied."""
    
    # 1. Start tunnel (run in separate terminal)
    # skyvern browser serve --tunnel --use-local-profile
    
    # 2. Wait for tunnel to be ready
    time.sleep(5)
    
    # 3. Connect to tunnel (get CDP URL from terminal)
    cdp_url = "wss://YOUR_TUNNEL_URL/devtools/browser/BROWSER_ID"
    skyvern_browser_session_connect(cdp_url=cdp_url)
    
    # 4. Navigate via JavaScript (Lesson 1)
    skyvern_evaluate(expression="window.location.href = 'http://localhost:8069/web/login'")
    
    # 5. Wait for page load (Lesson 7)
    skyvern_wait(time_ms=3000)
    
    # 6. Dismiss user switcher (Lesson 8)
    skyvern_click(selector="button:has-text('Use another user')")
    skyvern_wait(selector="#login", state="visible")
    
    # 7. Fill credentials via JavaScript (Lesson 2)
    skyvern_evaluate(expression=f"document.getElementById('login').value = '{username}'")
    skyvern_evaluate(expression=f"document.getElementById('password').value = '{password}'")
    
    # 8. Click login
    skyvern_click(selector="button[type='submit']")
    
    # 9. Verify success (Lesson 9)
    skyvern_wait(time_ms=3000)
    url = skyvern_evaluate(expression="window.location.href")
    
    if "/odoo" in url:
        print("Login successful!")
        return True
    else:
        print("Login failed!")
        return False
```

---

## Quick Reference: What Works vs What Fails

| Action | ❌ Fails | ✅ Works |
|--------|---------|---------|
| Navigate localhost | `skyvern_navigate(url="http://localhost:...")` | `skyvern_evaluate(expression="window.location.href = '...'")` |
| Fill password | `skyvern_type(selector="#password", text="...")` | `skyvern_evaluate(expression="...value = '...'")` |
| Use refs across calls | `skyvern_execute(steps=[{ref: "e33"}])` | `skyvern_click(selector="...")` |
| Verify page | Only screenshot | Title + URL + element checks |

---

## Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| "host is blocked: localhost" | Using skyvern_navigate | Use skyvern_evaluate |
| "Cannot type into password" | Using skyvern_type for password | Use skyvern_evaluate |
| "Unknown ref" | Refs are stale | Use selectors instead |
| "Screenshot timeout" | Font loading delays | Use title/URL checks |
| "Connection failed" | Tunnel not active | Restart tunnel |

---

## Files in This Skill

- `SKILL.md`: This file - lessons learned and workarounds
- `example.py`: Python implementation of these patterns
- `README.md`: Quick reference guide