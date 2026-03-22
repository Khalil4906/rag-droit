import fastapi, langchain, asyncpg, pgvector 
from rank_bm25 import BM25Okapi 
from sentence_transformers import SentenceTransformer, CrossEncoder 
print('OK - tous les imports passent') 
