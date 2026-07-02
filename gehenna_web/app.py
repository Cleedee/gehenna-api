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
    from flask import render_template, session
    from gehenna_web.services import api_client

    dashboard = None

    if session.get('username'):
        user_id = session.get('user_id')
        username = session.get('username')

        # Try to fetch dashboard data
        try:
            stats_resp = api_client.get_statistics(owner_id=user_id)
            stats_data = stats_resp.json() if stats_resp.status_code == 200 else {}

            decks_resp = api_client.get_decks(username=username, limit=5)
            decks_data = decks_resp.json() if decks_resp.status_code == 200 else {}

            mov_resp = api_client.get_moviments(username, limit=5)
            mov_data = mov_resp.json() if mov_resp.status_code == 200 else {}

            summary = stats_data.get('summary', {})

            dashboard = {
                'total_cards': summary.get('total_cards', 0),
                'total_decks': summary.get('total_decks', 0),
                'total_moviments': summary.get('total_moviments', 0),
                'total_value': summary.get('total_value', 0.0),
                'recent_decks': decks_data.get('decks', [])[:5],
                'recent_moviments': mov_data.get('moviments', [])[:5],
            }
        except Exception as e:
            app.logger.warning('Dashboard data fetch failed: %s', e)
            dashboard = None

    # If no dashboard data, still render the template with empty state
    if dashboard is None:
        dashboard = {
            'total_cards': '—',
            'total_decks': '—',
            'total_moviments': '—',
            'total_value': 0.0,
            'recent_decks': [],
            'recent_moviments': [],
        }

    return render_template('index.html', dashboard=dashboard)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
