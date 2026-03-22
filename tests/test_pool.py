import asyncio
from app.db.session import connect_db, disconnect_db, get_pool


async def test():
    await connect_db()
    p = get_pool()
    print(f'OK — pool créé, connexions min: {p.get_size()}')
    await disconnect_db()
    print('OK — pool fermé proprement')

asyncio.run(test())