#!/usr/bin/env python3
"""Record until stdin receives a newline, then transcribe with Gemini."""
import base64
import json
import os
import select
import signal
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import wave


def main():
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(RuntimeError('Recording cancelled.')))
    key = os.environ.get('GEMINI_API_KEY', '')
    if not key:
        raise RuntimeError('Set your Gemini API key with /key while a Gemini model is selected.')
    with tempfile.TemporaryDirectory(prefix='end4-voice-') as directory:
        audio_path = os.path.join(directory, 'voice.wav')
        recorder = subprocess.Popen(['pw-record', '--rate', '16000', '--channels', '1', audio_path], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        stopped_by_user = False
        try:
            ready, _, _ = select.select([sys.stdin], [], [], 60)
            if ready:
                sys.stdin.readline()
        finally:
            if recorder.poll() is None:
                stopped_by_user = True
                recorder.send_signal(signal.SIGINT)
            try:
                _, error = recorder.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                recorder.kill()
                _, error = recorder.communicate()
        if not stopped_by_user and recorder.returncode != 0:
            raise RuntimeError('Microphone recording failed: ' + error.decode(errors='replace').strip()[:300])
        try:
            with wave.open(audio_path, 'rb') as recording:
                if recording.getnframes() == 0:
                    raise RuntimeError('No audio was recorded. Check the microphone and try again.')
        except (wave.Error, EOFError):
            raise RuntimeError('Microphone recording produced an invalid audio file.') from None
        with open(audio_path, 'rb') as audio:
            encoded = base64.b64encode(audio.read()).decode('ascii')
        body = {'contents': [{'parts': [{'text': 'Transcribe the speech verbatim. Return only the spoken words, without commentary. If there is no speech, return an empty response.'}, {'inline_data': {'mime_type': 'audio/wav', 'data': encoded}}]}]}
        req = urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', 'x-goog-api-key': key})
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                result = json.load(response)
        except urllib.error.HTTPError as error:
            try:
                message = json.load(error).get('error', {}).get('message', 'Request failed')
            except (ValueError, OSError):
                message = 'Request failed'
            raise RuntimeError(f'Gemini transcription failed (HTTP {error.code}): {message}') from None
        parts = result.get('candidates', [{}])[0].get('content', {}).get('parts', [])
        text = ''.join(part.get('text', '') for part in parts).strip()
        if not text:
            raise RuntimeError('No speech was recognized. Try again closer to the microphone.')
        print(json.dumps({'text': text}, ensure_ascii=False))

if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, IndexError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False))
        sys.exit(1)
