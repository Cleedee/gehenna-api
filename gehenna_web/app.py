import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from gehenna_web.config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

csrf = CSRFProtect(app)

import gehenna_web.routes.auth as auth
import gehenna_web.routes.decks as decks
import gehenna_web.routes.cards as cards
import gehenna_web.routes.moviments as moviments
import gehenna_web.routes.users as users
import gehenna_web.routes.slots as slots
import gehenna_web.routes.items as items
import gehenna_web.routes.trends as trends

app.register_blueprint(auth.bp)
app.register_blueprint(decks.bp)
app.register_blueprint(cards.bp)
app.register_blueprint(moviments.bp)
app.register_blueprint(users.bp)
app.register_blueprint(slots.bp)
app.register_blueprint(items.bp)
app.register_blueprint(trends.bp)


@app.route('/')
def index():
    from flask import render_template
    return render_template('base.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)