import { useState, useCallback } from 'react'
import { CacheManager, fetchFromAPI } from './utils/CacheManager'

const cache = new CacheManager('demo')

function App() {
  const [stats, setStats] = useState({ hits: 0, misses: 0, total: 0 })
  const [cachedItems, setCachedItems] = useState([])
  const [lastResult, setLastResult] = useState(null)
  const [offlineMode, setOfflineMode] = useState(false)

  const updateCacheView = useCallback(() => {
    setCachedItems(cache.getAll())
  }, [])

  // Strategy 1: Cache-First
  const fetchCacheFirst = async (endpoint, ttl = 30) => {
    const startTime = performance.now()
    
    // 1. Try cache first
    const cached = cache.get(endpoint)
    
    if (cached.hit) {
      const duration = (performance.now() - startTime).toFixed(0)
      console.log(`✅ CACHE HIT: ${endpoint} (${duration}ms)`)
      console.log(`   Age: ${cached.age}s | TTL remaining: ${cached.remainingTtl}s`)
      console.log('   Data:', cached.value)
      
      setStats(prev => ({ ...prev, hits: prev.hits + 1, total: prev.total + 1 }))
      setLastResult({ type: 'hit', endpoint, duration, data: cached.value })
      updateCacheView()
      return cached.value
    }
    
    // 2. Cache miss - fetch from API
    console.log(`❌ CACHE MISS: ${endpoint} - Fetching from API...`)
    
    const data = await fetchFromAPI(endpoint)
    const duration = (performance.now() - startTime).toFixed(0)
    
    // 3. Store in cache
    cache.set(endpoint, data, ttl)
    
    console.log(`📥 API RESPONSE: ${endpoint} (${duration}ms)`)
    console.log(`   Cached for ${ttl}s`)
    console.log('   Data:', data)
    
    setStats(prev => ({ ...prev, misses: prev.misses + 1, total: prev.total + 1 }))
    setLastResult({ type: 'miss', endpoint, duration, data })
    updateCacheView()
    
    return data
  }

  // Strategy 2: Network-First
  const fetchNetworkFirst = async (endpoint, ttl = 30) => {
    const startTime = performance.now()
    
    console.log(`🌐 NETWORK-FIRST: ${endpoint} - Fetching fresh data...`)
    try {
      // Simulate network failure if offline mode is enabled
      if (offlineMode) {
        throw new Error('Simulated network failure (offline mode)')
      }
      
      const data = await fetchFromAPI(endpoint)
      const duration = (performance.now() - startTime).toFixed(0)
      
      // Update cache
      cache.set(endpoint, data, ttl)
      
      console.log(`📥 NETWORK SUCCESS: ${endpoint} (${duration}ms)`)
      console.log('   Data:', data)
      
      setStats(prev => ({ ...prev, misses: prev.misses + 1, total: prev.total + 1 }))
      setLastResult({ type: 'network', endpoint, duration, data })
      updateCacheView()
      
      return data
    } catch (error) {
      console.log(`❌ NETWORK FAILED: ${error.message}`)
      
      // Fallback to cache
      const cached = cache.get(endpoint)
      
      if (cached.hit) {
        const duration = (performance.now() - startTime).toFixed(0)
        console.log(`⚠️ FALLBACK TO CACHE: ${endpoint} (${duration}ms)`)
        console.log('   Serving stale data from cache')
        console.log('   Data:', cached.value)
        
        setStats(prev => ({ ...prev, hits: prev.hits + 1, total: prev.total + 1 }))
        setLastResult({ type: 'fallback', endpoint, duration, data: cached.value })
        return cached.value
      }
      
      console.log(`💥 NO CACHE AVAILABLE - Request failed completely`)
      setLastResult({ type: 'error', endpoint, error: error.message })
      throw error
    }
  }

  // Strategy 3: Stale-While-Revalidate
  const fetchSWR = async (endpoint, ttl = 30) => {
    const startTime = performance.now()
    
    // 1. Get cached data
    const cached = cache.get(endpoint)
    
    if (cached.hit) {
      const duration = (performance.now() - startTime).toFixed(0)
      console.log(`✅ SWR CACHE HIT: ${endpoint} (${duration}ms)`)
      console.log('   Serving cached data immediately...')
      console.log('   Data:', cached.value)
      
      setStats(prev => ({ ...prev, hits: prev.hits + 1, total: prev.total + 1 }))
      setLastResult({ type: 'swr-hit', endpoint, duration, data: cached.value })
      
      // 2. Revalidate in background
      console.log(`🔄 SWR: Starting background revalidation...`)
      fetchFromAPI(endpoint).then(freshData => {
        cache.set(endpoint, freshData, ttl)
        console.log(`✅ SWR: Background revalidation complete for ${endpoint}`)
        console.log('   Fresh data:', freshData)
        updateCacheView()
      })
      
      updateCacheView()
      return cached.value
    }
    
    // 3. No cache - fetch normally
    console.log(`❌ SWR CACHE MISS: ${endpoint} - No cache, fetching...`)
    
    const data = await fetchFromAPI(endpoint)
    const duration = (performance.now() - startTime).toFixed(0)
    
    cache.set(endpoint, data, ttl)
    
    console.log(`📥 SWR INITIAL FETCH: ${endpoint} (${duration}ms)`)
    console.log('   Data:', data)
    
    setStats(prev => ({ ...prev, misses: prev.misses + 1, total: prev.total + 1 }))
    setLastResult({ type: 'swr-miss', endpoint, duration, data })
    updateCacheView()
    
    return data
  }

  const clearCache = () => {
    const result = cache.clear()
    console.log(`🗑️ CACHE CLEARED: Removed ${result.cleared} items`)
    setStats({ hits: 0, misses: 0, total: 0 })
    setLastResult(null)
    updateCacheView()
  }

  const hitRate = stats.total > 0 ? ((stats.hits / stats.total) * 100).toFixed(0) : 0

  return (
    <div className="app">
      <h1>🗄️ Client-Side Storage Caching Demo</h1>
      <p className="subtitle">Open DevTools Console (F12) to see cache behavior!</p>
      
      <div className="container">
        <div className="left-panel">
          
          <div className="info-box">
            <h3>💡 How to Use</h3>
            <ol>
              <li>Open DevTools → <strong>Console</strong> tab</li>
              <li>Click buttons to fetch data</li>
              <li>Watch for ✅ CACHE HIT vs ❌ CACHE MISS</li>
              <li>Check <strong>Network</strong> tab - no request on cache hit!</li>
              <li>Check <strong>Application</strong> → localStorage</li>
            </ol>
          </div>

          <div className="section">
            <h2>1️⃣ Cache-First Strategy</h2>
            <p>Check cache first → If miss, fetch from API → Store in cache</p>
            <div className="buttons">
              <button onClick={() => fetchCacheFirst('/api/user', 30)}>
                Fetch User (30s TTL)
              </button>
              <button onClick={() => fetchCacheFirst('/api/posts', 15)}>
                Fetch Posts (15s TTL)
              </button>
            </div>
          </div>

          <div className="section">
            <h2>2️⃣ Network-First Strategy</h2>
            <p>Always fetch fresh → Store in cache → Use cache if offline</p>
            <div className="buttons">
              <button onClick={() => fetchNetworkFirst('/api/settings', 60)}>
                Fetch Settings (60s TTL)
              </button>
              <button 
                className={offlineMode ? 'danger' : 'secondary'}
                onClick={() => {
                  setOfflineMode(!offlineMode)
                  console.log(offlineMode ? '🌐 ONLINE MODE' : '📴 OFFLINE MODE - Network will fail')
                }}
              >
                {offlineMode ? '📴 Offline Mode ON' : '🌐 Online Mode'}
              </button>
            </div>
            <p style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>
              💡 Test: Fetch first (online) → Toggle offline → Fetch again → See cache fallback!
            </p>
          </div>

          <div className="section">
            <h2>3️⃣ Stale-While-Revalidate (SWR)</h2>
            <p>Serve cached instantly → Revalidate in background</p>
            <div className="buttons">
              <button className="success" onClick={() => fetchSWR('/api/posts', 30)}>
                Fetch Posts (SWR)
              </button>
            </div>
          </div>

          <div className="section">
            <h2>🧹 Cache Management</h2>
            <div className="buttons">
              <button className="danger" onClick={clearCache}>
                Clear All Cache
              </button>
              <button className="secondary" onClick={updateCacheView}>
                Refresh View
              </button>
            </div>
          </div>

        </div>

        <div className="right-panel">
          <h3>📊 Stats</h3>
          
          <div className="stats">
            <div className="stat-card">
              <div className="value" style={{ color: '#28a745' }}>{stats.hits}</div>
              <div className="label">Cache Hits</div>
            </div>
            <div className="stat-card">
              <div className="value" style={{ color: '#dc3545' }}>{stats.misses}</div>
              <div className="label">Cache Misses</div>
            </div>
            <div className="stat-card">
              <div className="value">{hitRate}%</div>
              <div className="label">Hit Rate</div>
            </div>
          </div>

          <h3 style={{ marginTop: '20px' }}>📦 localStorage Contents</h3>
          <div className="storage-view">
            {cachedItems.length === 0 ? (
              <div style={{ color: '#888' }}>No cached items</div>
            ) : (
              cachedItems.map(item => (
                <div key={item.key} style={{ marginBottom: '12px' }}>
                  <div>
                    <span className="key">{item.key}</span>
                  </div>
                  <div style={{ fontSize: '11px', color: item.expired ? '#f44336' : '#4caf50', marginTop: '4px' }}>
                    {item.expired 
                      ? `⚠️ EXPIRED`
                      : `✅ TTL: ${item.remainingTtl}s remaining`
                    }
                  </div>
                </div>
              ))
            )}
          </div>

          {lastResult && (
            <>
              <h3 style={{ marginTop: '20px' }}>📋 Last Result</h3>
              <div className="storage-view">
                <div style={{ color: lastResult.type.includes('hit') ? '#4caf50' : '#f44336' }}>
                  {lastResult.type.toUpperCase()} - {lastResult.endpoint}
                </div>
                <div style={{ color: '#888', marginTop: '4px' }}>
                  Duration: {lastResult.duration}ms
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
