# Importações necessárias
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import func

# --- CONFIGURAÇÃO E INICIALIZAÇÃO ---
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, template_folder=os.path.join(basedir, 'templates'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'poker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'uma-chave-secreta-bem-dificil'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
CASH_GAME_VALUE = 50

# --- MODELOS ---
class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    buy_in_value = db.Column(db.Integer, nullable=False, default=CASH_GAME_VALUE)
    players = db.relationship('Player', backref='game', lazy=True, cascade="all, delete-orphan")

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    buy_ins = db.Column(db.Integer, default=1, nullable=False)
    stack = db.Column(db.Integer, default=0, nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    payment_key_type = db.Column(db.String(20), nullable=True)
    payment_key = db.Column(db.String(200), nullable=True)

# --- FUNÇÃO PARA GERAR O PAYLOAD PIX VÁLIDO ---
def build_pix_payload(name, city, key, txid="***"):
    name = ''.join(e for e in name if e.isalnum() or e.isspace())[:25].strip()
    city = ''.join(e for e in city if e.isalnum() or e.isspace())[:15].strip()
    
    payload_format_indicator = "000201"
    merchant_account_info = f"26{len('0014br.gov.bcb.pix' + '01' + str(len(key)).zfill(2) + key):02}0014br.gov.bcb.pix01{len(key):02}{key}"
    merchant_category_code = "52040000"
    transaction_currency = "5303986"
    country_code = "5802BR"
    merchant_name = f"59{len(name):02}{name}"
    merchant_city = f"60{len(city):02}{city}"
    additional_data_field = f"62{len('05' + str(len(txid)).zfill(2) + txid):02}05{len(txid):02}{txid}"
    
    payload = f"{payload_format_indicator}{merchant_account_info}{merchant_category_code}{transaction_currency}{country_code}{merchant_name}{merchant_city}{additional_data_field}6304"

    # CRC16 Calculation
    crc = 0xFFFF
    for b in payload.encode('utf-8'):
        crc ^= (b << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
    crc_value = "{:04X}".format(crc & 0xFFFF)
    
    return payload + crc_value

# --- ROTAS ---
@app.route('/generate_pix', methods=['POST'])
def generate_pix():
    data = request.get_json()
    if not data: return jsonify({'error': 'Requisição inválida'}), 400
    try:
        payload = build_pix_payload(name=data.get('name'), city='SAO PAULO', key=data.get('key'))
        return jsonify({'payload': payload})
    except Exception as e:
        return jsonify({'error': f'Erro ao gerar código PIX: {str(e)}'}), 500

@app.route('/player/<int:player_id>/set_key', methods=['POST'])
def set_key(player_id):
    player = Player.query.get_or_404(player_id)
    player.payment_key_type = request.form.get('payment_key_type')
    player.payment_key = request.form.get('payment_key')
    db.session.commit()
    flash(f'Chave de pagamento para {player.name} foi salva!', 'success')
    return redirect(url_for('game_details', game_id=player.game_id))

# ... (outras rotas permanecem iguais) ...
@app.route('/')
def index():
    games = Game.query.order_by(Game.id.desc()).all()
    return render_template('index.html', games=games)

@app.route('/caixa', methods=['GET', 'POST'])
def caixa():
    found_player = None; search_name = ""
    if request.method == 'POST':
        search_name = request.form.get('player_name')
        if search_name:
            found_player = Player.query.filter(func.lower(Player.name) == func.lower(search_name), Player.payment_key.isnot(None)).first()
            if not found_player: flash(f'Nenhum jogador chamado "{search_name}" com chave salva foi encontrado.', 'warning')
    return render_template('caixa.html', found_player=found_player, search_name=search_name)

@app.route('/game/new', methods=['GET', 'POST'])
def new_game():
    if request.method == 'POST':
        name = request.form['name']
        if not name: flash('O nome do jogo é obrigatório!', 'danger'); return redirect(url_for('new_game'))
        new_game = Game(name=name, buy_in_value=CASH_GAME_VALUE)
        db.session.add(new_game)
        db.session.commit()
        flash('Jogo criado com sucesso!', 'success')
        return redirect(url_for('game_details', game_id=new_game.id))
    return render_template('new_game.html')

@app.route('/game/<int:game_id>')
def game_details(game_id):
    game = Game.query.get_or_404(game_id)
    players = Player.query.filter_by(game_id=game.id).all()
    return render_template('game_details.html', game=game, players=players, cash_value=CASH_GAME_VALUE)

@app.route('/game/<int:game_id>/add_player', methods=['POST'])
def add_player(game_id):
    game = Game.query.get_or_404(game_id)
    player_name = request.form['player_name']
    if player_name:
        new_player = Player(name=player_name, game_id=game.id, buy_ins=1)
        db.session.add(new_player)
        db.session.commit()
        flash(f'Jogador {player_name} entrou na mesa com {CASH_GAME_VALUE} fichas!', 'success')
    return redirect(url_for('game_details', game_id=game.id))

@app.route('/player/<int:player_id>/rebuy', methods=['POST'])
def rebuy(player_id):
    player = Player.query.get_or_404(player_id)
    player.buy_ins += 1
    db.session.commit()
    flash(f'Rebuy de {CASH_GAME_VALUE} fichas adicionado para {player.name}!', 'info')
    return redirect(url_for('game_details', game_id=player.game_id))

@app.route('/player/<int:player_id>/delete', methods=['POST'])
def delete_player(player_id):
    player = Player.query.get_or_404(player_id)
    game_id = player.game_id
    db.session.delete(player)
    db.session.commit()
    flash('Jogador removido com sucesso.', 'warning')
    return redirect(url_for('game_details', game_id=game_id))

@app.route('/game/<int:game_id>/delete', methods=['POST'])
def delete_game(game_id):
    game = Game.query.get_or_404(game_id)
    db.session.delete(game)
    db.session.commit()
    flash('Jogo deletado com sucesso!', 'danger')
    return redirect(url_for('index'))

@app.route('/game/<int:game_id>/end', methods=['GET', 'POST'])
def end_game(game_id):
    game = Game.query.get_or_404(game_id)
    if request.method == 'POST':
        players_to_update = Player.query.filter_by(game_id=game.id).all()
        for player in players_to_update:
            stack_value = request.form.get(f'stack_{player.id}')
            try: player.stack = int(stack_value) if stack_value else 0
            except (ValueError, TypeError): player.stack = player.stack or 0
        db.session.commit()
        flash('Saldos atualizados com sucesso!', 'success')
        return redirect(url_for('end_game', game_id=game.id))

    players = Player.query.filter_by(game_id=game.id).all()
    player_results = []
    for player in players:
        total_invested = player.buy_ins * game.buy_in_value
        saldo = player.stack - total_invested
        player_results.append({'player_id': player.id, 'name': player.name, 'payment_key': player.payment_key, 'buy_ins_count': 1, 'rebuys_count': player.buy_ins - 1, 'total_invested': total_invested, 'final_stack': player.stack, 'saldo': saldo})
    
    total_chips_in_play = sum(p.buy_ins for p in players) * game.buy_in_value
    total_final_chips = sum(p.stack for p in players)
    discrepancy = total_final_chips - total_chips_in_play
    
    return render_template('end_game.html', game=game, results=player_results, discrepancy=discrepancy)

if __name__ == '__main__':
    app.run(debug=True)
