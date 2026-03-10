from flask import Flask, request, jsonify, send_from_directory
from youtube_transcript_api import YouTubeTranscriptApi
import os, re, requests

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/transcript', methods=['POST'])
def transcript():
    data = request.json
    video_id = data.get('videoId')

    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=['ja', 'en', 'ja-JP', 'en-US'])
        text = ' '.join([e.text for e in fetched])
        return jsonify({'transcript': text})

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/summarize', methods=['POST'])
def summarize():
    data = request.json
    transcript = data.get('transcript', '')
    api_key = data.get('apiKey', '')
    mode = data.get('mode', 'simple')

    mode_instructions = {
        'simple': '知識がゼロの中学生に説明するつもりで要約してください。専門用語は使わず、難しい概念はかみ砕いて、「つまりどういうこと？」が分かるように書いてください。見出しと箇条書きを使って読みやすく整理してください。',
        'action': 'この動画の内容を、実際にビジネスや日常で今すぐ実践できる形に整理してください。「何をすべきか」「どうやるか」「なぜ効果があるか」の観点でまとめ、すぐに行動に移せるよう具体的なステップや使えるポイントを箇条書きで書いてください。',
        'tldr': 'この動画の内容を、その分野の知識がまったくない社会人が読んでも一発で理解できるように、5〜10文でまとめてください。専門用語は使わず、「で、結局何の話？」「それって要するに？」がすぐわかる言葉で書いてください。',
    }

    prompt = f"""以下はYouTube動画の字幕テキストです。{mode_instructions[mode]}

【字幕テキスト】
{transcript[:8000]}

【要約】"""

    try:
        url = 'https://api.groq.com/openai/v1/chat/completions'
        res = requests.post(url, headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }, json={
            'model': 'llama-3.3-70b-versatile',
            'messages': [
                {'role': 'system', 'content': 'あなたは優秀な日本語ライターです。自然で読みやすい日本語で回答してください。翻訳調や不自然な表現は使わず、日本人が普段使うような言葉で書いてください。'},
                {'role': 'user', 'content': prompt},
            ],
            'temperature': 0.5,
            'max_tokens': 1024,
        })
        res.raise_for_status()
        summary = res.json()['choices'][0]['message']['content']
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    print('✅ サーバー起動中... ブラウザで http://localhost:8080 を開いてください')
    app.run(port=8080, debug=False)
