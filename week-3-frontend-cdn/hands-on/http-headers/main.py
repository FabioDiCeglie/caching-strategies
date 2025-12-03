"""
HTTP Caching Headers Demo

Demonstrates different caching strategies:
- Cache-Control (max-age, no-cache, public/private)
- ETag validation
- Last-Modified validation
"""

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, HTMLResponse
from datetime import datetime
import hashlib
import json
import time

app = FastAPI(title="HTTP Caching Headers Demo")

# In-memory data store
posts = [
    {"id": 1, "title": "Understanding Cache-Control", "content": "Cache-Control is the primary HTTP caching mechanism...", "updated_at": "2024-01-01T10:00:00Z"},
    {"id": 2, "title": "ETag Deep Dive", "content": "ETags provide efficient cache validation...", "updated_at": "2024-01-02T10:00:00Z"},
    {"id": 3, "title": "CDN Caching Strategies", "content": "CDNs cache content at edge locations...", "updated_at": "2024-01-03T10:00:00Z"},
]

user_data = {"name": "John Doe", "email": "john@example.com", "preferences": {"theme": "dark"}}


def generate_etag(data: dict) -> str:
    """Generate ETag from data hash"""
    content = json.dumps(data, sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()


@app.get("/")
async def root():
    """Root endpoint with links to demos"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>HTTP Caching Headers Demo</title>
        <style>
            body { 
                font-family: Arial; 
                margin: 0; 
                padding: 20px; 
                background: #f5f5f5;
            }
            h1 { 
                color: #333; 
                margin-bottom: 10px;
            }
            .subtitle {
                color: #666;
                margin-bottom: 20px;
            }
            .container {
                display: flex;
                gap: 20px;
                height: calc(100vh - 120px);
            }
            .left-panel {
                flex: 1;
                overflow-y: auto;
                padding-right: 10px;
            }
            .right-panel {
                flex: 1;
                background: #fff;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                overflow-y: auto;
            }
            .endpoint { 
                background: #fff; 
                padding: 15px; 
                margin: 10px 0; 
                border-radius: 8px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            .endpoint h3 { 
                margin-top: 0; 
                color: #0066cc; 
                font-size: 16px;
            }
            .endpoint p {
                margin: 8px 0;
                color: #666;
                font-size: 14px;
            }
            code { 
                background: #ffe6e6; 
                padding: 2px 6px; 
                border-radius: 3px; 
                font-size: 12px;
            }
            button { 
                background: #0066cc; 
                color: white; 
                padding: 8px 16px; 
                border: none; 
                border-radius: 4px; 
                cursor: pointer; 
                margin: 5px 5px 5px 0;
                font-size: 14px;
            }
            button:hover { 
                background: #0052a3; 
            }
            #result { 
                font-family: 'Courier New', monospace; 
                font-size: 13px;
                color: #333;
                line-height: 1.8;
            }
            #result.empty {
                color: #999;
                text-align: center;
                padding-top: 50px;
                font-family: Arial;
            }
            #result strong {
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <h1>🚀 HTTP Caching Headers Demo</h1>
        <p class="subtitle">Open DevTools → Network tab to inspect cache headers!</p>
        
        <div class="container">
            <div class="left-panel">
        
        <div class="endpoint">
            <h3>1️⃣ Max-Age Caching (60 seconds)</h3>
            <p>Browser caches for 60 seconds - no network request during this time</p>
            <button onclick="fetchData('/api/max-age')">Fetch Data</button>
            <code>Cache-Control: public, max-age=60</code>
        </div>
        
        <div class="endpoint">
            <h3>2️⃣ ETag Validation</h3>
            <p>Always validates with server - returns 304 if unchanged</p>
            <button onclick="fetchData('/api/etag')">Fetch Data</button>
            <button onclick="addPost()" style="background: #ff9800;">Add Post (Change Data)</button>
            <code>ETag: "abc123"</code>
            <p style="font-size: 12px; color: #666; margin-top: 10px;">
                💡 Test: Fetch → 304 → Add Post → Fetch → 200 (ETag changed!)
            </p>
        </div>
        
        <div class="endpoint">
            <h3>3️⃣ Last-Modified Validation</h3>
            <p>Timestamp-based validation - returns 304 if not modified</p>
            <button onclick="fetchData('/api/last-modified')">Fetch Data</button>
            <code>Last-Modified: [timestamp]</code>
        </div>
        
        <div class="endpoint">
            <h3>4️⃣ Private User Data</h3>
            <p>Only browser caches (not CDN) - user-specific data</p>
            <button onclick="fetchData('/api/private')">Fetch Data</button>
            <code>Cache-Control: private, max-age=300</code>
        </div>
        
        <div class="endpoint">
            <h3>5️⃣ No Cache (Real-time)</h3>
            <p>Always fetches fresh data - must validate every time</p>
            <button onclick="fetchData('/api/no-cache')">Fetch Data</button>
            <code>Cache-Control: no-cache, must-revalidate</code>
        </div>
        
        <div class="endpoint">
            <h3>6️⃣ Static Asset (1 year)</h3>
            <p>Long-lived cache for immutable content</p>
            <button onclick="fetchData('/api/static')">Fetch Data</button>
            <code>Cache-Control: public, max-age=31536000, immutable</code>
        </div>
        
            </div>
            
            <div class="right-panel">
                <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 2px solid #ffc107;">
                    <h3 style="margin: 0 0 10px 0; color: #f57c00;">🔍 How to Use This Demo</h3>
                    <ol style="margin: 0; padding-left: 20px; line-height: 1.8;">
                        <li>Open <strong>DevTools</strong> (F12 or Right-click → Inspect)</li>
                        <li>Go to <strong>Network</strong> tab</li>
                        <li>Make sure <strong>"Disable cache"</strong> is <u>unchecked</u></li>
                        <li>Click any button on the left</li>
                        <li>Watch the <strong>Status</strong>, <strong>Size</strong>, and <strong>Headers</strong> in Network tab!</li>
                    </ol>
                </div>
                
                <h2 style="margin-top: 0; color: #0066cc;">📋 Key Headers to Watch</h2>
                <div id="result" class="empty">
                    👈 Click any button to see cache headers
                </div>
            </div>
        </div>
        
        <script>
            async function fetchData(url) {
                const resultDiv = document.getElementById('result');
                resultDiv.className = ''; // Remove empty class
                resultDiv.textContent = '⏳ Loading...';
                
                const response = await fetch(url, { cache: 'no-cache' });
                
                // Consume the body if present
                if (response.status !== 304) {
                    await response.json();
                }
                
                // Get key cache headers
                const cacheControl = response.headers.get('cache-control') || 'Not set';
                const etag = response.headers.get('etag') || 'Not set';
                const lastModified = response.headers.get('last-modified') || 'Not set';
                
                let output = '';
                output += '📊 Status: ' + response.status + ' ' + response.statusText + '\\n\\n';
                
                if (response.status === 304) {
                    output += '✅ <strong style="color: #2e7d32;">304 NOT MODIFIED</strong>\\n';
                    output += '   → Server said: "Nothing changed"\\n';
                    output += '   → Browser uses cached version\\n';
                    output += '   → Bandwidth saved: ~90%\\n\\n';
                } else if (response.status === 200) {
                    output += '✅ <strong style="color: #1976d2;">200 OK</strong>\\n';
                    output += '   → Full response with body\\n';
                    output += '   → Data downloaded from server\\n\\n';
                }
                
                output += '📋 <strong>KEY CACHE HEADERS:</strong>\\n';
                output += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n';
                
                output += '<strong>Cache-Control:</strong>\\n';
                output += '  ' + cacheControl + '\\n\\n';
                
                if (etag !== 'Not set') {
                    output += '<strong>ETag:</strong>\\n';
                    output += '  ' + etag + '\\n\\n';
                }
                
                if (lastModified !== 'Not set') {
                    output += '<strong>Last-Modified:</strong>\\n';
                    output += '  ' + lastModified + '\\n\\n';
                }
                
                output += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n';
                output += '💡 <strong>Check Network tab for:</strong>\\n';
                output += '   • Status column\\n';
                output += '   • Size column (memory cache, disk cache, or bytes)\\n';
                output += '   • Headers tab (Request + Response headers)';
                
                resultDiv.innerHTML = output.replace(/\\n/g, '<br>');
            }
            
            async function addPost() {
                const resultDiv = document.getElementById('result');
                resultDiv.className = ''; // Remove empty class
                resultDiv.textContent = '⏳ Adding new post...';
                
                try {
                    const response = await fetch('/api/posts?title=Test Post&content=Testing ETag changes', {
                        method: 'POST'
                    });
                    await response.json();
                    
                    let output = '';
                    output += '✅ <strong style="color: #2e7d32;">POST SUCCESSFUL</strong>\\n\\n';
                    output += '📝 <strong>What happened:</strong>\\n';
                    output += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n';
                    output += '  1. New post added to server\\n';
                    output += '  2. Server data changed\\n';
                    output += '  3. ETag hash recalculated\\n';
                    output += '  4. Next request will return 200 (not 304)\\n\\n';
                    output += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n';
                    output += '💡 <strong>Try this now:</strong>\\n';
                    output += '   Click "Fetch Data" in ETag section again\\n';
                    output += '   → You\\'ll get <strong>200</strong> instead of <strong>304</strong>\\n';
                    output += '   → Because ETag changed!';
                    
                    resultDiv.innerHTML = output.replace(/\\n/g, '<br>');
                } catch (error) {
                    resultDiv.innerHTML = '❌ <strong>ERROR</strong><br>' + error.message;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/api/max-age")
async def max_age_cache():
    """
    Cache-Control: max-age - Browser caches for specified duration
    """
    response_data = {
        "strategy": "max-age",
        "posts": posts,
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Cached for 60 seconds - no network request during this time"
    }
    
    return JSONResponse(
        content=response_data,
        headers={
            "Cache-Control": "public, max-age=60",
        }
    )


@app.get("/api/etag")
async def etag_validation(request: Request):
    """
    ETag validation - Returns 304 if content hasn't changed
    """
    # Generate ETag from current data
    current_etag = generate_etag(posts)
    
    # Check if client sent If-None-Match header
    client_etag = request.headers.get("If-None-Match")
    
    if client_etag and client_etag.strip('"') == current_etag:
        # Content hasn't changed - return 304
        return Response(
            status_code=304,
            headers={
                "ETag": f'"{current_etag}"',
                "Cache-Control": "no-cache",
            }
        )
    
    # Content changed or first request - return 200 with data
    response_data = {
        "strategy": "etag",
        "posts": posts,
        "timestamp": datetime.utcnow().isoformat(),
        "message": "ETag validation - server returns 304 if unchanged"
    }
    
    return JSONResponse(
        content=response_data,
        headers={
            "ETag": f'"{current_etag}"',
            "Cache-Control": "no-cache",
        }
    )


@app.get("/api/last-modified")
async def last_modified_validation(request: Request):
    """
    Last-Modified validation - Returns 304 if not modified since timestamp
    """
    # Get latest update timestamp from posts
    latest_update = max(posts, key=lambda p: p["updated_at"])["updated_at"]
    last_modified = datetime.fromisoformat(latest_update.replace("Z", "+00:00"))
    
    # Check if client sent If-Modified-Since header
    if_modified_since = request.headers.get("If-Modified-Since")
    
    if if_modified_since:
        # Parse client timestamp
        client_time = datetime.strptime(if_modified_since, "%a, %d %b %Y %H:%M:%S GMT")
        
        if last_modified.timestamp() <= client_time.timestamp():
            # Not modified - return 304
            return Response(
                status_code=304,
                headers={
                    "Last-Modified": last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT"),
                    "Cache-Control": "no-cache",
                }
            )
    
    # Modified or first request - return 200 with data
    response_data = {
        "strategy": "last-modified",
        "posts": posts,
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Last-Modified validation - server returns 304 if not modified"
    }
    
    return JSONResponse(
        content=response_data,
        headers={
            "Last-Modified": last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "Cache-Control": "no-cache",
        }
    )


@app.get("/api/private")
async def private_cache():
    """
    Private cache - Only browser can cache (not CDN)
    Used for user-specific data
    """
    response_data = {
        "strategy": "private",
        "user": user_data,
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Private cache - only browser caches, not CDN"
    }
    
    return JSONResponse(
        content=response_data,
        headers={
            "Cache-Control": "private, max-age=300",
        }
    )


@app.get("/api/no-cache")
async def no_cache():
    """
    No cache - Always validates with server
    Used for real-time data
    """
    response_data = {
        "strategy": "no-cache",
        "current_time": datetime.utcnow().isoformat(),
        "random_value": int(time.time() * 1000) % 10000,
        "message": "No cache - always fetches fresh data"
    }
    
    return JSONResponse(
        content=response_data,
        headers={
            "Cache-Control": "no-cache, must-revalidate",
        }
    )


@app.get("/api/static")
async def static_asset():
    """
    Static asset cache - Long-lived cache for immutable content
    In production, use with fingerprinted filenames (app.abc123.js)
    """
    response_data = {
        "strategy": "static",
        "version": "v1.0.0",
        "content": "This represents a static asset like CSS/JS",
        "message": "Cached for 1 year - use fingerprinted filenames in production"
    }
    
    return JSONResponse(
        content=response_data,
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
        }
    )


@app.post("/api/posts")
async def create_post(title: str, content: str):
    """
    Create new post - demonstrates cache invalidation
    In production, you'd invalidate related caches here
    """
    new_post = {
        "id": len(posts) + 1,
        "title": title,
        "content": content,
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }
    posts.append(new_post)
    
    return JSONResponse(
        content={
            "message": "Post created - cache invalidated",
            "post": new_post
        },
        headers={
            "Cache-Control": "no-store",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

