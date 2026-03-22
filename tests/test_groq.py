from dotenv import load_dotenv
import os
load_dotenv()
k = os.getenv('GROQ_API_KEY')
print(f'OK — {k[:8]}...' if k and not k.startswith('gsk_xxx') else 'ERREUR — remplis GROQ_API_KEY')