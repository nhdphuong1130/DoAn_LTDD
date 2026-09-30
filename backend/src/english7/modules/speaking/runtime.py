import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4
from english7.api.errors import ApplicationError


class LocalSpeechRuntime:
    """Server-configured private endpoint only; no client-supplied URLs."""
    def __init__(self, url, timeout=120):
        self.url, self.timeout = url.rstrip('/'), timeout

    def _request(self, path, body=None, content_type='application/json', timeout=None):
        try:
            request = Request(self.url + path, data=body, headers={'Content-Type': content_type})
            with urlopen(request, timeout=timeout or self.timeout) as response:
                data = response.read(16 * 1024 * 1024 + 1)
                if len(data) > 16 * 1024 * 1024:
                    raise ApplicationError('speech_response_too_large', 'Speech response too large', 502)
                return data
        except HTTPError as error:
            if error.code in (400, 413, 415, 422):
                raise ApplicationError('invalid_recording', 'Không đọc được bản thu. Em hãy thu lại trong 15 giây.', 422) from error
            raise ApplicationError('speech_unavailable', 'Dịch vụ giọng nói chưa sẵn sàng. Vui lòng thử lại.', 503) from error
        except (URLError, OSError, TimeoutError) as error:
            raise ApplicationError('speech_unavailable', 'Dịch vụ giọng nói chưa sẵn sàng. Vui lòng thử lại.', 503) from error

    def voices(self):
        try:
            return json.loads(self._request('/voices', timeout=5))['items']
        except (ValueError, KeyError, TypeError) as error:
            raise ApplicationError('speech_invalid_response', 'Voice service returned invalid data', 502) from error

    def transcribe(self, audio):
        boundary = 'english7-' + uuid4().hex
        body = (f'--{boundary}\r\nContent-Disposition: form-data; name="audio"; filename="recording.m4a"\r\n'
                'Content-Type: application/octet-stream\r\n\r\n').encode() + audio + f'\r\n--{boundary}--\r\n'.encode()
        try:
            result = json.loads(self._request('/transcribe', body, f'multipart/form-data; boundary={boundary}'))
            if not isinstance(result.get('transcript'), str):
                raise ValueError('Missing transcript')
            return result
        except (ValueError, KeyError, TypeError) as error:
            raise ApplicationError('speech_invalid_response', 'Transcription returned invalid data', 502) from error

    def synthesize(self, text, voice_id):
        data = self._request('/synthesize', json.dumps({'text': text, 'voice_id': voice_id}).encode())
        if not data.startswith(b'RIFF'):
            raise ApplicationError('speech_invalid_audio', 'Speech service returned invalid audio', 502)
        return data
