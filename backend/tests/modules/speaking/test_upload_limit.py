import asyncio

from english7.modules.speaking.upload_limit import SpeakingUploadLimit


def test_chunked_upload_stops_before_parser_and_does_not_drain_body():
    async def check():
        messages, reads = [], []

        async def receive():
            reads.append(True)
            return {'type': 'http.request', 'body': b'x' * 20, 'more_body': True}

        async def parser(*args):
            raise AssertionError('Must reject before parsing')

        async def send(message):
            messages.append(message)

        app = SpeakingUploadLimit(parser, api_prefix='/custom', limit=32)
        scope = {'type': 'http', 'method': 'POST', 'path': '/custom/speaking/attempts/id',
                 'headers': [(b'authorization', b'Bearer arbitrary'), (b'content-length', b'1')]}
        await app(scope, receive, send)
        assert messages[0]['status'] == 413
        assert len(reads) == 2

    asyncio.run(check())


def test_small_body_replayed_exactly_once():
    async def check():
        chunks = iter([b'abc', b'def'])

        async def receive():
            chunk = next(chunks)
            return {'type': 'http.request', 'body': chunk, 'more_body': chunk == b'abc'}

        async def parser(scope, receive, send):
            assert await receive() == {'type': 'http.request', 'body': b'abcdef', 'more_body': False}

        await SpeakingUploadLimit(parser, limit=32)(
            {'type': 'http', 'method': 'POST', 'path': '/api/v1/speaking/attempts/id', 'headers': []}, receive, None)

    asyncio.run(check())
