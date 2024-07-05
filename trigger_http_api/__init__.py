import logging
import azure.functions as func
import nest_asyncio
from app.main import app
nest_asyncio.apply()

async def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    logging.info('HTTP trigger function processed a request.')
    """Each request is redirected to the ASGI handler."""
    try:
        return await func.AsgiMiddleware(app).handle_async(req, context)
    
    except Exception as ex:
        print('Unable to connect!')
        print('Exception:')
        print(ex)
        logging.error(ex)