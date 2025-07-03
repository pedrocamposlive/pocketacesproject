# Importações necessárias
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import func
from brcode import brcode # Usando a biblioteca correta

# --- CONFIGURAÇÃO E INICIALIZAÇÃO (sem alterações) ---
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, template_folder=os.path.join(basedir, 'templates'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'poker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'uma-chave-secreta-bem-dificil'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
CASH_GAME_VALUE = 50

# --- MODELOS (sem alterações) ---
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
    payment_key = db.Column(db.String(200), nullable=True)

# --- ROTAS (com a rota generate_pix atualizada) ---

# Rota para gerar o payload do Pix
@app.route('/generate_pix', methods=['POST'])
def generate_pix():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Requisição inválida'}), 400

    pix_key = data.get('key')
    name = data.get('name', 'Pagamento Poker')
    amount = data.get('amount')
    
    # --- MELHORIA: Sanitização dos dados ---
    # Garante que o nome do beneficiário tenha no máximo 25 caracteres e seja simples.
    sanitized_name = ''.join(e for e in name if e.isalnum() or e.isspace())[:25].strip()
    if not sanitized_name:
        sanitized_name = 'JOGADOR'

    # Garante que o ID da transação seja único e válido.
    txid = ''.join(c for c in name if c.isalnum()) + str(Game.query.count())
    txid = "POKER" + txid[:15] # Limita o tamanho total

    try:
        # Garante que o valor seja formatado como uma string com duas casas decimais.
        formatted_amount = f"{float(amount):.2f}"

        payment = brcode(
            key=pix_key,
            name=sanitized_name,
            city='SAO PAULO', # Pode ser alterado para qualquer cidade de 2 letras maiúsculas
            amount=formatted_amount,
            txid=txid
        )
        payload = payment.generate()
        return jsonify({'payload': payload})
    except Exception as e:
        # --- MELHORIA: Retorna um erro mais específico ---
        # Isso nos ajudará a diagnosticar se o problema persistir.
        return jsonify({'error': f'Erro na biblioteca PIX: {str(e)}'}), 500

# Demais rotas permanecem as mesmas...
@app.route('/caixa', methods=['GET', 'POST'])
def caixa():
    found_player = None; search_name = ""
    if request.method == 'POST':
        search_name = request.form.get('player_name')
        if search_name:
            found_player = Player.query.filter(func.lower(Player.name) == func.lower(search_name), Player.payment_key.isnot(None)).first()
            if not found_player: flash(f'Nenhum jogador chamado "{search_name}" com chave salva foi encontrado.', 'warning')
    return render_template('caixa.html', found_player=found_player, search_name=search_name)

@app.route('/')
def index():
    games = Game.query.order_by(Game.id.desc()).all()
    return render_template('index.html', games=games)

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

@app.route('/player/<int:player_id>/set_key', methods=['POST'])
def set_key(player_id):
    player = Player.query.get_or_404(player_id)
    key = request.form.get('payment_key')
    player.payment_key = key
    db.session.commit()
    flash(f'Chave de pagamento para {player.name} foi salva!', 'success')
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
