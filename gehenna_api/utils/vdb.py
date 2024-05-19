from typing import Dict, List

mapa_disciplinas = {
    'Abombwe': {1: 'abo', 2: 'ABO'},
    'Animalism': {1: 'ani', 2: 'ANI'},
    'Auspex': {1: 'aus', 2: 'AUS'},
    'Blood Sorcery': {1: 'blo', 2: 'BLO'},
    'Celerity': {1: 'cel', 2: 'CEL'},
    'Chimerstry': {1: 'chi', 2: 'CHI'},
    'Daimonon': {1: 'dai', 2: 'DAI'},
    'Defense': {1: 'def', 2: 'DEF'},
    'Dementation': {1: 'dem', 2: 'DEM'},
    'Dominate': {1: 'dom', 2: 'DOM'},
    'Fortitude': {1: 'for', 2: 'FOR'},
    'Innocence': {1: 'inn', 2: 'INO'},
    'Judgment': {1: 'jud', 2: 'JUD'},
    'Maleficia': {1: 'mal', 2: 'MAL'},
    'Martyrdom': {1: 'mar', 2: 'MAR'},
    'Melpominee': {1: 'mel', 2: 'MEL'},
    'Mytherceria': {1: 'myt', 2: 'MYT'},
    'Necromancy': {1: 'nec', 2: 'NEC'},
    'Obeah': {1: 'obe', 2: 'OBE'},
    'Obfuscate': {1: 'obf', 2: 'OBF'},
    'Obtenebration': {1: 'obt', 2: 'OBT'},
    'Potence': {1: 'pot', 2: 'POT'},
    'Presence': {1: 'pre', 2: 'PRE'},
    'Protean': {1: 'pro', 2: 'PRO'},
    'Quietus': {1: 'qui', 2: 'QUI'},
    'Redemption': {1: 'red', 2: 'RED'},
    'Sanguinus': {1: 'san', 2: 'SAN'},
    'Serpentis': {1: 'ser', 2: 'SER'},
    'Spiritus': {1: 'spi', 2: 'SPI'},
    'Striga': {1: 'str', 2: 'STR'},
    'Temporis': {1: 'tem', 2: 'TEM'},
    'Thanatosis': {1: 'thn', 2: 'THN'},
    'Thaumaturgy': {1: 'tha', 2: 'THA'},
    'Valeren': {1: 'val', 2: 'VAL'},
    'Vengeance': {1: 'ven', 2: 'VEN'},
    'Vicissitude': {1: 'vic', 2: 'VIC'},
    'Visceratika': {1: 'vis', 2: 'VIS'},
    'Vision': {1: 'vin', 2: 'VIN'},
}


def converte_disciplinas_cripta(disciplinas: Dict[str, str]) -> str:
    texto = '|'
    for chave in disciplinas.keys():
        valor = mapa_disciplinas[chave][disciplinas[chave]]
        texto += f'{valor}|'
    if texto == '|':
        texto = '||'
    return texto


def converte_disciplinas_biblioteca(disciplinas: str) -> str:
    if not disciplinas:
        return '||'
    texto = '|'
    lista_disciplinas: List[str] = []
    if '/' in disciplinas:
        disciplinas = disciplinas.replace(' ', '')
        lista_disciplinas = disciplinas.split('/')
    if '&' in disciplinas:
        disciplinas = disciplinas.replace(' ', '')
        lista_disciplinas = disciplinas.split('&')
    for d in lista_disciplinas:
        texto += mapa_disciplinas[d][1]
        texto += '|'
    if texto == '|':
        texto = '||'
    return texto
