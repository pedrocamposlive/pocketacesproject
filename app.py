# Importações necessárias do Flask e outras bibliotecas
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

# Inicialização do aplicativo Flask
app = Flask(__name__)

# --- Configuração do Banco de Dados ---
# Define a variável de ambiente para o caminho do banco de dados
# Isso garante que o banco de dados seja criado na mesma pasta do projeto
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'poker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'uma-chave-secreta-bem-dificil' # Troque por uma chave mais segura em produção

# Inicialização do SQLAlchemy e do Migrate
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- Modelos do Banco de Dados (Estrutura das Tabelas) ---

class Game(db.Model):
    """Modelo para a tabela de Jogos/Partidas."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    buy_in_value = db.Column(db.Integer, nullable=False)
    # Relacionamento: um jogo pode ter vários jogadores. Se um jogo for deletado, todos os jogadores associados também serão.
    players = db.relationship('Player', backref='game', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Game {self.name}>'

class Player(db.Model):
    """Modelo para a tabela de Jogadores."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    buy_ins = db.Column(db.Integer, default=1, nullable=False)
    stack = db.Column(db.Integer, default=0, nullable=False)
    # Chave estrangeira para ligar o jogador a um jogo específico
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)

    def __repr__(self):
        return f'<Player {self.name}>'

# --- Rotas da Aplicação (As páginas do site) ---

@app.route('/')
def index():
    """Página inicial que lista todos os jogos criados."""
    games = Game.query.order_by(Game.id.desc()).all()
    return render_template('index.html', games=games)

@app.route('/game/new', methods=['GET', 'POST'])
def new_game():
    """Página para criar um novo jogo."""
    if request.method == 'POST':
        name = request.form['name']
        buy_in_value = int(request.form['buy_in_value'])
        
        # Verifica se os campos não estão vazios
        if not name or not buy_in_value:
            flash('Nome do jogo e valor do Buy-in são obrigatórios!', 'danger')
            return redirect(url_for('new_game'))

        # Cria um novo jogo e salva no banco de dados
        new_game = Game(name=name, buy_in_value=buy_in_value)
        db.session.add(new_game)
        db.session.commit()
        
        flash('Jogo criado com sucesso!', 'success')
        return redirect(url_for('game_details', game_id=new_game.id))
        
    return render_template('new_game.html')

@app.route('/game/<int:game_id>')
def game_details(game_id):
    """Página que exibe os detalhes de um jogo específico e seus jogadores."""
    game = Game.query.get_or_404(game_id)
    players = Player.query.filter_by(game_id=game.id).all()
    return render_template('game_details.html', game=game, players=players)

@app.route('/game/<int:game_id>/add_player', methods=['POST'])
def add_player(game_id):
    """Rota para adicionar um novo jogador a um jogo."""
    game = Game.query.get_or_404(game_id)
    player_name = request.form['player_name']
    
    if player_name:
        new_player = Player(name=player_name, game_id=game.id, buy_ins=1, stack=0)
        db.session.add(new_player)
        db.session.commit()
        flash(f'Jogador {player_name} adicionado!', 'success')
        
    return redirect(url_for('game_details', game_id=game.id))

@app.route('/player/<int:player_id>/update_buyins', methods=['POST'])
def update_buyins(player_id):
    """Rota para adicionar ou remover buy-ins de um jogador."""
    player = Player.query.get_or_404(player_id)
    action = request.form.get('action')

    if action == 'add':
        player.buy_ins += 1
    elif action == 'remove' and player.buy_ins > 0:
        player.buy_ins -= 1
    
    db.session.commit()
    flash(f'Buy-ins de {player.name} atualizados!', 'info')
    return redirect(url_for('game_details', game_id=player.game_id))

@app.route('/player/<int:player_id>/delete', methods=['POST'])
def delete_player(player_id):
    """Rota para remover um jogador de um jogo."""
    player = Player.query.get_or_404(player_id)
    game_id = player.game_id
    db.session.delete(player)
    db.session.commit()
    flash('Jogador removido com sucesso.', 'warning')
    return redirect(url_for('game_details', game_id=game_id))

@app.route('/game/<int:game_id>/delete', methods=['POST'])
def delete_game(game_id):
    """Rota para deletar um jogo inteiro."""
    game = Game.query.get_or_404(game_id)
    db.session.delete(game)
    db.session.commit()
    flash('Jogo deletado com sucesso!', 'danger')
    return redirect(url_for('index'))

@app.route('/game/<int:game_id>/end', methods=['GET', 'POST'])
def end_game(game_id):
    """Página para encerrar o jogo, registrar stacks finais e auditar as fichas."""
    game = Game.query.get_or_404(game_id)
    players = Player.query.filter_by(game_id=game.id).all()

    # Se o formulário for enviado (método POST), atualiza os stacks
    if request.method == 'POST':
        for player in players:
            # Pega o valor do stack do formulário. Se não existir, usa 0 como padrão.
            player.stack = int(request.form.get(f'stack_{player.id}', 0))
        db.session.commit()
        flash('Stacks finais salvos com sucesso!', 'success')
        # É necessário recarregar os jogadores da sessão para garantir que os cálculos
        # usem os dados que acabaram de ser salvos.
        players = Player.query.filter_by(game_id=game.id).all()

    # --- NOVA LÓGICA DA AUDITORIA ---
    # Esta parte é executada sempre que a página é carregada (GET) ou após salvar (POST).
    
    # 1. Calcula o total de fichas que deveriam estar no jogo.
    #    (Soma de todos os buy-ins) x (Valor em fichas de cada buy-in)
    total_chips_in_play = sum(p.buy_ins for p in players) * game.buy_in_value
    
    # 2. Soma os stacks finais de todos os jogadores que foram informados.
    total_final_chips = sum(p.stack for p in players)
    
    # 3. Calcula a diferença (discrepância). O valor ideal é 0.
    discrepancy = total_final_chips - total_chips_in_play
    # --- FIM DA LÓGICA DA AUDITORIA ---

    # Renderiza o template, passando as variáveis da auditoria para o frontend
    return render_template('end_game.html', 
                           game=game, 
                           players=players,
                           total_chips_in_play=total_chips_in_play,
                           total_final_chips=total_final_chips,
                           discrepancy=discrepancy)

# Ponto de entrada para executar o aplicativo
if __name__ == '__main__':
    # Cria o banco de dados se ele não existir
    with app.app_context():
        db.create_all()
    app.run(debug=True)

