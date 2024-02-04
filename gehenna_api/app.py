from fastapi import Depends, FastAPI, HTTPException

from gehenna_api.routes import auth, decks, stocks, users, cards

app = FastAPI()

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(stocks.router)
app.include_router(decks.router)
app.include_router(cards.router)


@app.get('/')
def read_root():
    return {'message': 'Olá Mundo!'}



