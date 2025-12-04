export default function handler(req, res) {
  // CDN caches for 10 seconds, browser caches for 1 second
  res.setHeader('Cache-Control', 'public, s-maxage=10, max-age=1, stale-while-revalidate=59')
  
  res.json({
    time: new Date().toISOString(),
    cached: false, // When CDN serves cached, this stays as original value
    message: 'This response is cached by CDN for 10 seconds'
  })
}

