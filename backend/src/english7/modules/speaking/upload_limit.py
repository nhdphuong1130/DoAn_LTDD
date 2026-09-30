"""Bound recording bodies before the framework parses/spools multipart uploads."""
import asyncio
import re

from starlette.responses import JSONResponse

from english7.modules.speaking.service import MAX_AUDIO_BYTES


class SpeakingUploadLimit:
    def __init__(self, app, api_prefix='/api/v1', limit=MAX_AUDIO_BYTES + 65536):
        self.app, self.limit = app, limit
        self.path = re.compile(re.escape(api_prefix.rstrip('/')) + r'/speaking/attempts/[^/]+/?$')

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['method'] != 'POST' or not self.path.fullmatch(scope['path']):
            return await self.app(scope, receive, send)

        async def reject(status=413):
            return await JSONResponse(
                {'code': 'recording_too_large' if status == 413 else 'upload_timeout',
                 'message': 'Em hãy thu lại trong 15 giây rồi gửi.'}, status_code=status)(scope, receive, send)

        for key, value in scope.get('headers', []):
            if key.lower() == b'content-length':
                try:
                    if int(value) > self.limit:
                        return await reject()
                except ValueError:
                    return await reject()
        body = bytearray()
        try:
            async with asyncio.timeout(30):
                while True:
                    message = await receive()
                    if message['type'] == 'http.disconnect':
                        return
                    chunk = message.get('body', b'')
                    if len(body) + len(chunk) > self.limit:
                        return await reject()
                    body.extend(chunk)
                    if not message.get('more_body', False):
                        break
        except TimeoutError:
            return await reject(408)

        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {'type': 'http.request', 'body': bytes(body), 'more_body': False}

        await self.app(scope, bounded_receive, send)
