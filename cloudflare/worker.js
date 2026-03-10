addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      }
    })
  }

  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), { status: 405 })
  }

  const { videoId } = await request.json()

  try {
    const transcript = await getTranscript(videoId)
    return new Response(JSON.stringify({ transcript }), {
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      }
    })
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), {
      status: 400,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      }
    })
  }
}

async function getTranscript(videoId) {
  const response = await fetch(`https://www.youtube.com/watch?v=${videoId}`, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Accept-Language': 'ja,en;q=0.9',
    }
  })

  const html = await response.text()

  const match = html.match(/ytInitialPlayerResponse\s*=\s*(\{.+?\})\s*;/)
  if (!match) throw new Error('動画情報を取得できませんでした')

  const playerResponse = JSON.parse(match[1])
  const captions = playerResponse?.captions?.playerCaptionsTracklistRenderer?.captionTracks

  if (!captions || captions.length === 0) throw new Error('この動画には字幕がありません')

  const track = captions.find(t => t.languageCode === 'ja') ||
                captions.find(t => t.languageCode === 'en') ||
                captions[0]

  const captionResponse = await fetch(track.baseUrl)
  const xml = await captionResponse.text()

  const texts = [...xml.matchAll(/<text[^>]*>([^<]*)<\/text>/g)]
    .map(m => m[1]
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&#39;/g, "'")
      .replace(/&quot;/g, '"')
    )
    .join(' ')

  return texts
}
