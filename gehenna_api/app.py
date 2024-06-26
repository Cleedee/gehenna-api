from fastapi import FastAPI

from gehenna_api.routes import auth, cards, decks, slots, stocks, users

app = FastAPI()

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(stocks.router)
app.include_router(decks.router)
app.include_router(cards.router)
app.include_router(slots.router)


@app.get('/')
def read_root():
    return {'message': 'Olá Mundo!'}
