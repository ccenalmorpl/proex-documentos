# lambda_handler.py
from mangum import Mangum
from main import app

# Mangum adapta FastAPI para AWS Lambda
handler = Mangum(app, lifespan="off")
