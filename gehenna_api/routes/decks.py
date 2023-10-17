from datetime import datetime, date
from fastapi.routing import APIRouter

from gehenna_api.schemas import DeckSchema


router = APIRouter(prefix='/decks', tags=['decks'])

@router.get('/')
def decks():
    dt = datetime.today()
    dt_str = dt.strftime('%Y-%m-%d')
    deck = DeckSchema(
        name='Meu deck', 
        description='Um bom deck',
        tipo='other',
        created=date.today(),
        owner_id=1
    )
    return {'decks': [deck]}
