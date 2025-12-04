export default function handler(req, res) {
  // CDN caches for 60 seconds
  res.setHeader('Cache-Control', 'public, s-maxage=60, max-age=10, stale-while-revalidate=300')
  
  res.json({
    posts: [
      { id: 1, title: 'Understanding ISR', views: Math.floor(Math.random() * 1000) },
      { id: 2, title: 'CDN Caching Explained', views: Math.floor(Math.random() * 1000) },
      { id: 3, title: 'Next.js Performance', views: Math.floor(Math.random() * 1000) },
    ],
    generatedAt: new Date().toISOString(),
    cacheInfo: 's-maxage=60 (CDN caches 60s), max-age=10 (browser caches 10s)'
  })
}

