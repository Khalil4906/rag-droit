import asyncio, asyncpg, os 
from dotenv import load_dotenv 
load_dotenv() 


async def test(): 
    conn = await asyncpg.connect(os.getenv('DATABASE_URL').replace('postgres://', 'postgresql://')) 
    v = await conn.fetchval("SELECT extname FROM pg_extension WHERE extname = 'vector'") 
    await conn.close() 
    print(f'pgvector actif : {v}') 
asyncio.run(test()) 
