import datetime
import ujson
import uuid


"""
# Create table statement (run once before ever calling this code)
TODO: move to SQLalchemy?

CREATE TABLE IF NOT EXISTS sessions
(
    created_at timestamp without time zone NOT NULL,
    expires_at timestamp without time zone,
    sid character varying,
    val character varying,
    CONSTRAINT sessions_pkey PRIMARY KEY (sid)
);
"""


class AsyncPG:  # pragma: no cover
    '''
        encoder & decoder:

            e.g. json, ujson, pickle, cpickle, bson, msgpack etc..
            Default ujson

        Requires postgres 9.5+ for UPSERT (ON CONFLICT DO UPDATE)
    '''
    def __init__(
        self,
        client,
        prefix='session:',
        encoder=ujson.dumps,
        decoder=ujson.loads,
        sid_factory=lambda: uuid.uuid4().hex
    ):
        self.client = client
        self.prefix = prefix
        self.encoder = encoder
        self.decoder = decoder
        self.sid_factory = sid_factory

    async def fetch(self, sid, **kwargs):
        print('-'*75)
        print('fetching...', sid)
        print('-'*75)
        val = await self.client.scalar(
            "SELECT val FROM sessions WHERE sid = $1 AND expires_at > NOW()",
            sid,
        )
        print('val', val)
        if val is not None:
            return self.decoder(val)

    async def store(self, sid, expiry, val, **kwargs):
        if val is not None:
            print('*'*75)
            val = self.encoder(val)
            print('storing...', sid, val, expiry)
            # FIXME: add expiry here!
            await self.client.scalar(
                # Upsert using postgres 9.5+
                'INSERT INTO sessions(created_at, sid, val, expires_at) VALUES(NOW(), $1, $2, $3) ON CONFLICT (sid) DO UPDATE SET val = EXCLUDED.val, expires_at = EXCLUDED.expires_at',  # noqa
                sid,
                val,
                datetime.datetime.utcnow() + datetime.timedelta(seconds=expiry)
            )

    async def delete(self, sid, **kwargs):
        await self.client.scalar(
            "DELETE FROM sessions WHERE sid = $1",
            sid,
        )
