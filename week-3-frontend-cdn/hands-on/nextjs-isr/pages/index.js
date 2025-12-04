import useSWR from 'swr'

const fetcher = (url) => fetch(url).then(r => r.json())

export default function Home({ serverTime, buildTime }) {
  // SWR - fetches once, caches in memory, revalidates on focus/click
  const { data: timeData, mutate: refreshTime } = useSWR('/api/time', fetcher)
  const { data: postsData, mutate: refreshPosts } = useSWR('/api/posts', fetcher)

  return (
    <div style={{ fontFamily: 'Arial', padding: '40px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>🌐 Next.js ISR + CDN Caching Demo</h1>
      
      <div style={{ background: '#e3f2fd', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
        <h2>📋 How to Test</h2>
        <ol style={{ lineHeight: '1.8' }}>
          <li><strong>Dev mode:</strong> <code>npm run dev</code> - ISR doesn't work (always fresh)</li>
          <li><strong>Production:</strong> <code>npm run build && npm start</code> - ISR works!</li>
          <li><strong>Deploy to Vercel:</strong> Real CDN caching at edge locations</li>
        </ol>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        
        <div style={{ background: '#fff', padding: '20px', borderRadius: '8px', border: '2px solid #4caf50' }}>
          <h2>🏗️ ISR (Server-Side)</h2>
          <p style={{ color: '#666', fontSize: '14px' }}>
            Generated at build time, revalidated every 10 seconds
          </p>
          <div style={{ background: '#f5f5f5', padding: '15px', borderRadius: '6px', marginTop: '10px' }}>
            <div><strong>Build Time:</strong></div>
            <div style={{ fontFamily: 'monospace', color: '#1976d2' }}>{buildTime}</div>
            <div style={{ marginTop: '10px' }}><strong>Server Time:</strong></div>
            <div style={{ fontFamily: 'monospace', color: '#4caf50' }}>{serverTime}</div>
          </div>
          <p style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>
            ⏱️ Refresh page - time updates every 10s (ISR revalidate)
          </p>
        </div>

        <div style={{ background: '#fff', padding: '20px', borderRadius: '8px', border: '2px solid #ff9800' }}>
          <h2>🔄 SWR (Client-Side)</h2>
          <p style={{ color: '#666', fontSize: '14px' }}>
            Fetches /api/time (s-maxage=10)
          </p>
          <div style={{ background: '#f5f5f5', padding: '15px', borderRadius: '6px', marginTop: '10px' }}>
            <div><strong>Time:</strong></div>
            <div style={{ fontFamily: 'monospace', color: '#ff9800' }}>
              {timeData?.time || 'Loading...'}
            </div>
          </div>
          <button 
            onClick={() => refreshTime()}
            style={{ marginTop: '10px', padding: '8px 16px', cursor: 'pointer' }}
          >
            🔄 Refresh
          </button>
          <p style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>
            Click refresh - same time for 10s (CDN cached)
          </p>
        </div>

      </div>

      <div style={{ background: '#fff', padding: '20px', borderRadius: '8px', marginTop: '20px', border: '2px solid #9c27b0' }}>
        <h2>📝 Posts</h2>
        <p style={{ color: '#666', fontSize: '14px' }}>
          <code>max-age=10</code> (browser) | <code>s-maxage=60</code> (CDN)
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px', marginTop: '15px' }}>
          {postsData?.posts?.map(post => (
            <div key={post.id} style={{ background: '#f5f5f5', padding: '15px', borderRadius: '6px' }}>
              <div style={{ fontWeight: 'bold', fontSize: '14px' }}>{post.title}</div>
              <div style={{ color: '#9c27b0', marginTop: '5px' }}>👁 {post.views} views</div>
            </div>
          )) || <div>Loading posts...</div>}
        </div>
        <div style={{ marginTop: '15px', display: 'flex', alignItems: 'center', gap: '15px' }}>
          <button 
            onClick={() => refreshPosts()}
            style={{ padding: '8px 16px', cursor: 'pointer' }}
          >
            🔄 Refresh Posts
          </button>
          <span style={{ fontSize: '12px', color: '#666' }}>
            Generated: {postsData?.generatedAt || '...'}
          </span>
        </div>
        <p style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>
          <strong>Browser:</strong> Caches 10s (no network request)<br/>
          <strong>CDN:</strong> Caches 60s (same response for all users)<br/>
          Views only change after CDN cache expires
        </p>
      </div>

      <div style={{ background: '#fff3cd', padding: '20px', borderRadius: '8px', marginTop: '20px' }}>
        <h2>🔑 Key Concepts</h2>
        <ul style={{ lineHeight: '2' }}>
          <li><strong>ISR (revalidate: 10)</strong> - Page regenerated in background every 10s</li>
          <li><strong>s-maxage</strong> - CDN caches for specified duration</li>
          <li><strong>stale-while-revalidate</strong> - Serve stale, refresh in background</li>
          <li><strong>SWR hook</strong> - Client-side caching + auto-refresh</li>
        </ul>
      </div>

      <div style={{ marginTop: '20px', padding: '20px', background: '#f5f5f5', borderRadius: '8px' }}>
        <h2>🧪 Test the API directly</h2>
        <p>Open these URLs and check the response headers:</p>
        <ul style={{ fontFamily: 'monospace', lineHeight: '2' }}>
          <li><a href="/api/time">/api/time</a> - Cache-Control: s-maxage=10</li>
          <li><a href="/api/posts">/api/posts</a> - Cache-Control: s-maxage=60</li>
        </ul>
      </div>
    </div>
  )
}

// ISR: Generate at build time, revalidate every 10 seconds
export async function getStaticProps() {
  return {
    props: {
      serverTime: new Date().toISOString(),
      buildTime: new Date().toISOString(),
    },
    revalidate: 10, // Regenerate page every 10 seconds
  }
}

