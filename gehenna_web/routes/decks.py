from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional

from gehenna_web.routes.auth import login_required
from gehenna_web.services import api_client

bp = Blueprint("decks", __name__, url_prefix="/decks")

DISCIPLINE_ICON = {
    "ABI": "abombwe",
    "ANI": "animalism",
    "AUS": "auspex",
    "CEL": "celerity",
    "CHI": "chimerstry",
    "DAI": "dementation",
    "DOM": "dominate",
    "FOR": "fortitude",
    "MEL": "melpominee",
    "MYT": "mytherceria",
    "NEC": "necromancy",
    "OBF": "obfuscate",
    "OBT": "obtenebration",
    "POT": "potence",
    "PRE": "presence",
    "PRO": "protean",
    "QUI": "quietus",
    "SER": "serpentis",
    "SPI": "spiritus",
    "STR": "striga",
    "THA": "thanatosis",
    "VIC": "vicissitude",
    "VIS": "visceratika",
}

CLAN_ICON = {
    "Baali": "baali",
    "Brujah": "brujah",
    "Brujah antitribu": "brujahantitribu",
    "Followers of Set": "followerset",
    "Gangrel": "gangrel",
    "Gangrel antitribu": "gangrelantitribu",
    "Giovanni": "giovanni",
    "Lasombra": "lasombra",
    "Malkavian": "malkavian",
    "Malkavian antitribu": "malkavianantitribu",
    "Nosferatu": "nosferatu",
    "Nosferatu antitribu": "nosferatuantitribu",
    "Ravnos": "ravnos",
    "Salubri": "salubri",
    "Toreador": "toreador",
    "Toreador antitribu": "toreadorantitribu",
    "Tremere": "tremere",
    "Tremere antitribu": "tremereantitribu",
    "Tzimisce": "tzimisce",
    "Ventrue": "ventrue",
    "Ventrue antitribu": "ventrueantitribu",
    "Abomination": "abomination",
    "Ahrimane": "ahrimane",
    "Akunanse": "akunanse",
    "Blood Brother": "bloodbrother",
    "Daughter of Cacophony": "daughterofcacophony",
    "Gargoyle": "gargoyle",
    "Harbinger of Skulls": "harbingerofskulls",
    "Ishtarri": "ishtarri",
    "Kiasyd": "kiasyd",
    "Lhiannon": "lhiannon",
    "Nagaraja": "nagaraja",
    "Osebo": "osebo",
    "Pander": "pander",
    "Samedi": "samedi",
    "True Brujah": "truebrujah",
    "Wraith": "wraith",
    "Xaviar": "xaviar",
    "Anarch": "anarch",
    "Camarilla": "camarilla",
    "Sabbat": "sabbat",
    "Laibon": "laibon",
    "Independent": "independent",
    "Imbued": "imbued",
    "Judge": "imbued",
    "Avenger": "imbued",
    "Defender": "imbued",
    "Innocent": "imbued",
    "Martyr": "imbued",
    "Redeemer": "imbued",
    "Visionary": "imbued",
}


class DeckForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    description = TextAreaField("Description")
    creator = StringField("Creator")
    player = StringField("Player")
    tipo = StringField("Type", validators=[DataRequired()])
    tags = StringField("Tags")
    preconstructed = BooleanField("Preconstructed")
    code = IntegerField("Code")
    submit = SubmitField("Save")


@bp.route("/")
def list():
    username = request.args.get("username")
    name = request.args.get("name")
    card_name = request.args.get("card_name")
    code = request.args.get("code")
    preconstructed = request.args.get("preconstructed")

    response = api_client.get_decks(
        username=username,
        name=name,
        card_name=card_name,
        code=code,
        preconstructed=preconstructed,
    )
    decks = []
    if response.status_code == 200:
        data = response.json()
        decks = data.get("decks", [])
    return render_template(
        "decks/list.html",
        decks=decks,
        username=username,
        name=name,
        card_name=card_name,
        preconstructed=preconstructed,
    )


@bp.route("/my")
@login_required
def my_decks():
    username = session.get("username")
    name = request.args.get("name")
    card_name = request.args.get("card_name")
    code = request.args.get("code")
    preconstructed = request.args.get("preconstructed")

    response = api_client.get_decks(
        username=username,
        name=name,
        card_name=card_name,
        code=code,
        preconstructed=preconstructed,
    )
    decks = []
    if response.status_code == 200:
        data = response.json()
        decks = data.get("decks", [])
    return render_template(
        "decks/list.html",
        decks=decks,
        username=username,
        name=name,
        card_name=card_name,
        preconstructed=preconstructed,
    )


@bp.route("/<int:deck_id>")
def detail(deck_id):
    response = api_client.get_deck(deck_id)
    deck = None
    if response.status_code == 200:
        deck = response.json()

    slots_resp = api_client.get_slots(deck_id, limit=1000)
    slots = []
    if slots_resp.status_code == 200:
        slots = slots_resp.json().get("slots", [])

    crypt = []
    library = []
    for s in slots:
        card = s["card"]
        card["disc_list"] = [
            d.strip().upper()
            for d in card.get("disciplines", "").split("|") if d.strip()
        ]
        if "vampire" in card["tipo"].strip().lower():
            crypt.append(s)
        else:
            library.append(s)

    crypt.sort(
        key=lambda x: (
            -(int(x["card"]["capacity"]) if x["card"].get("capacity") else 0),
            x["card"]["name"],
        )
    )
    crypt_total = sum(s["quantity"] for s in crypt)
    crypt_blood = sum(
        int(s["card"]["capacity"]) * s["quantity"]
        for s in crypt if s["card"].get("capacity")
    )

    tipo_order = [
        "Master",
        "Action",
        "Political Action",
        "Action Modifier",
        "Action Modifier/Combat",
        "Action Modifier/Reaction",
        "Reaction",
        "Reaction/Action Modifier",
        "Combat",
        "Combat/Reaction",
        "Equipment",
        "Retainer",
        "Ally",
        "Event",
    ]
    grouped_library = {}
    for s in library:
        t = s["card"]["tipo"]
        grouped_library.setdefault(t, []).append(s)

    def sort_key(t):
        try:
            return tipo_order.index(t)
        except ValueError:
            return len(tipo_order)

    grouped_library = dict(
        sorted(grouped_library.items(), key=lambda x: sort_key(x[0]))
    )
    lib_total = sum(s["quantity"] for s in library)
    lib_pool = sum(
        int(s["card"]["pool"]) * s["quantity"] for s in library if s["card"].get("pool")
    )
    for group_list in grouped_library.values():
        group_list.sort(key=lambda x: x["card"]["name"])
    library_groups = {
        t: {"slots": slots, "total": sum(s["quantity"] for s in slots)}
        for t, slots in grouped_library.items()
    }

    return render_template(
        "decks/detail.html",
        deck=deck,
        crypt=crypt,
        crypt_total=crypt_total,
        crypt_blood=crypt_blood,
        library_groups=library_groups,
        lib_total=lib_total,
        lib_pool=lib_pool,
        DISCIPLINE_ICON=DISCIPLINE_ICON,
        CLAN_ICON=CLAN_ICON,
    )


@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = DeckForm()
    if form.validate_on_submit():
        data = {
            "name": form.name.data,
            "description": form.description.data,
            "creator": form.creator.data,
            "player": form.player.data,
            "tipo": form.tipo.data,
            "tags": form.tags.data or "",
            "preconstructed": form.preconstructed.data,
            "code": form.code.data,
            "owner_id": session.get("user_id"),
            "created": date.today().isoformat(),
        }
        response = api_client.create_deck(data)
        if response.status_code == 201:
            flash("Deck created", "success")
            return redirect(url_for("decks.my_decks"))
        flash("Error creating deck", "error")
    return render_template("decks/form.html", form=form, title="Create Deck")


@bp.route("/<int:deck_id>/edit", methods=["GET", "POST"])
@login_required
def edit(deck_id):
    form = DeckForm()
    if request.method == "GET":
        response = api_client.get_deck(deck_id)
        if response.status_code == 200:
            deck = response.json()
            form.name.data = deck.get("name")
            form.description.data = deck.get("description")
            form.creator.data = deck.get("creator")
            form.player.data = deck.get("player")
            form.tipo.data = deck.get("tipo")
            form.tags.data = deck.get("tags", "")
            form.preconstructed.data = deck.get("preconstructed")
            form.code.data = deck.get("code")

    if form.validate_on_submit():
        data = {
            "name": form.name.data,
            "description": form.description.data,
            "creator": form.creator.data,
            "player": form.player.data,
            "tipo": form.tipo.data,
            "tags": form.tags.data or "",
            "preconstructed": form.preconstructed.data,
            "code": form.code.data,
            "owner_id": session.get("user_id"),
        }
        response = api_client.update_deck(deck_id, data)
        if response.status_code == 200:
            flash("Deck updated", "success")
            return redirect(url_for("decks.detail", deck_id=deck_id))
        flash("Error updating deck", "error")

    return render_template("decks/form.html", form=form, title="Edit Deck")


@bp.route("/<int:deck_id>/delete")
@login_required
def delete(deck_id):
    response = api_client.delete_deck(deck_id)
    if response.status_code == 200:
        flash("Deck deleted", "success")
    else:
        flash("Error deleting deck", "error")
    return redirect(url_for("decks.my_decks"))


@bp.route("/<int:deck_id>/missing")
def missing_cards(deck_id):
    username = session.get("username")
    response = api_client.get_deck(deck_id)
    deck = None
    if response.status_code == 200:
        deck = response.json()

    missing = {"cards": [], "total": 0}
    if username:
        response = api_client.get_missing_cards(deck_id, username)
        if response.status_code == 200:
            data = response.json()
            cards = data.get("cards", [])
            for card in cards:
                response = api_client.get_preconstructed_decks_with_card(
                    card["card_id"]
                )
                if response.status_code == 200:
                    card["preconstructed_decks"] = response.json().get("decks", [])
                else:
                    card["preconstructed_decks"] = []
            missing = {"cards": cards, "total": data.get("total", 0)}

    return render_template("decks/missing.html", deck=deck, missing=missing)


@bp.route("/import-vdb", methods=["GET", "POST"])
@login_required
def import_vdb():
    form = VDBImportForm()
    if form.validate_on_submit():
        deck_id = form.deck_id.data
        owner_id = session.get("user_id")
        response = api_client.import_vdb_deck(deck_id, owner_id)
        if response.status_code == 200:
            data = response.json()
            flash(
                f"Deck imported: {data.get('name')} ({data.get('cards_imported')} cards)",
                "success",
            )
            return redirect(url_for("decks.my_decks"))
        flash("Error importing deck", "error")
    return render_template("decks/import_vdb.html", form=form)


class VDBImportForm(FlaskForm):
    deck_id = StringField(
        "VDB Deck ID", validators=[DataRequired()], description="Ex: 8c46348db"
    )
    submit = SubmitField("Import")


@bp.route("/<int:deck_id>/export-text")
def export_text(deck_id):
    resp = api_client.get_deck(deck_id)
    if resp.status_code != 200:
        return {"text": "Deck not found", "format": "twd"}, 404
    deck = resp.json()

    slots_resp = api_client.get_slots(deck_id, limit=1000)
    slots = slots_resp.json().get("slots", []) if slots_resp.status_code == 200 else []

    crypt = [
        s for s in slots if s["card"]["tipo"].strip().lower().startswith("vampire")
    ]
    library = [
        s for s in slots if not s["card"]["tipo"].strip().lower().startswith("vampire")
    ]

    lines = []
    lines.append(f'Deck Name: {deck.get("name", "Unnamed")}')
    desc = (deck.get("description") or "").strip()
    if desc:
        lines.append("Description:")
        for d in desc.split("\n"):
            lines.append(d)
    else:
        lines.append("Description:")
    lines.append("")

    # Crypt
    crypt_total = sum(s["quantity"] for s in crypt)
    lines.append(f"Crypt ({crypt_total} cards)")
    for s in sorted(
        crypt,
        key=lambda x: (
            -(int(x["card"]["capacity"]) if x["card"].get("capacity") else 0),
            x["card"]["name"],
        ),
    ):
        card = s["card"]
        qty = s["quantity"]
        name = card["name"]
        cap = card.get("capacity") or ""
        discs = (card.get("disciplines") or "").replace("|", " ").strip()
        clan = card.get("clan") or ""
        group = card.get("group") or ""
        parts = [f"{qty}x {name}", str(cap)]
        if discs:
            parts.append(discs)
        if clan:
            clan_group = f"{clan}:{group}" if group else clan
            parts.append(clan_group)
        lines.append("   " + "   ".join(parts))
    lines.append("")

    # Library
    lib_total = sum(s["quantity"] for s in library)
    lines.append(f"Library ({lib_total} cards)")

    tipo_order = [
        "Master",
        "Action",
        "Political Action",
        "Action Modifier",
        "Action Modifier/Combat",
        "Action Modifier/Reaction",
        "Reaction",
        "Reaction/Action Modifier",
        "Combat",
        "Combat/Reaction",
        "Equipment",
        "Retainer",
        "Ally",
        "Event",
    ]
    grouped = {}
    for s in library:
        t = s["card"]["tipo"]
        grouped.setdefault(t, []).append(s)

    def sort_key(t):
        try:
            return tipo_order.index(t)
        except ValueError:
            return len(tipo_order)

    for t in sorted(grouped, key=sort_key):
        cards = grouped[t]
        sec_total = sum(c["quantity"] for c in cards)
        lines.append(f"{t} ({sec_total})")
        for c in sorted(cards, key=lambda x: x["card"]["name"]):
            lines.append(f'{c["quantity"]}x {c["card"]["name"]}')
        lines.append("")

    return {"text": "\n".join(lines), "format": "twd"}


@bp.route("/<int:deck_id>/import", methods=["GET", "POST"])
@login_required
def import_to_moviment(deck_id):
    response = api_client.get_deck(deck_id)
    deck = None
    if response.status_code == 200:
        deck = response.json()

    if not deck or deck.get("owner_id") != session.get("user_id"):
        flash("Deck not found or not yours", "error")
        return redirect(url_for("decks.my_decks"))

    if request.method == "POST":
        date_move = request.form.get("date_move")
        price = float(request.form.get("price") or 0)
        owner_id = session.get("user_id")
        response = api_client.create_moviment_from_deck(
            deck_id=deck_id,
            owner_id=owner_id,
            date_move=date_move,
            price=price,
        )
        if response.status_code == 201:
            data = response.json()
            flash(
                f"Moviment created: {data.get('total_cards')} cards imported", "success"
            )
            return redirect(url_for("moviments.list"))
        flash("Error creating moviment", "error")

    from datetime import date

    return render_template(
        "decks/import.html", deck=deck, today=date.today().isoformat()
    )
