from flask import Flask, render_template_string, request, redirect, url_for

import os

app = Flask(__name__)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

class Jogador:
    def __init__(self, nome):
        self.nome = nome
        self.buy_ins = 1
        self.rebuys = 0
        self.fichas_finais = 0

    @property
    def total_fichas(self):
        return (self.buy_ins + self.rebuys) * 50

    @property
    def saldo_final(self):
        return self.fichas_finais - self.total_fichas

jogadores = {}

template_index = """
<!doctype html><html><head><title>Poker</title></head><body>
<h1>POKER & RESENHA</h1>
<a href='/resumo'>Final do jogo</a>
<form method='post' action='/add'>
    <input name='nome' placeholder='Nome do Jogador' required>
    <button type='submit'>Adicionar</button>
</form>
<ul>
{% for j in jogadores.values() %}
    <li>
        <strong>{{ j.nome }}</strong> - Buy-ins: {{ j.buy_ins }} | Rebuys: {{ j.rebuys }}
        <a href='/rebuy/{{ j.nome }}/add'>+ Rebuy</a>
        <a href='/rebuy/{{ j.nome }}/sub'>- Rebuy</a>
        <form method='post' action='/finalizar/{{ j.nome }}'>
            <input type='number' name='fichas' min='0' placeholder='Fichas finais'>
            <button type='submit'>Registrar</button>
        </form>
    </li>
{% endfor %}
</ul>
</body></html>
"""

template_resumo = """
<!doctype html><html><head><title>Resumo</title></head><body>
<h1>Resumo Final</h1>
<table border=1>
<tr><th>Nome</th><th>Buy-ins</th><th>Rebuys</th><th>Total</th><th>Final</th><th>Saldo</th></tr>
{% for j in jogadores.values() %}
<tr><td>{{ j.nome }}</td><td>{{ j.buy_ins }}</td><td>{{ j.rebuys }}</td>
<td>{{ j.total_fichas }}</td><td>{{ j.fichas_finais }}</td><td>{{ j.saldo_final }}</td></tr>
{% endfor %}
</table>
<a href='/'>Voltar</a>
</body></html>
"""

@app.route("/")
def index():
    return render_template_string(template_index, jogadores=jogadores)

@app.route("/add", methods=["POST"])
def add_jogador():
    nome = request.form['nome']
    if nome not in jogadores:
        jogadores[nome] = Jogador(nome)
    return redirect(url_for('index'))

@app.route("/rebuy/<nome>/<acao>")
def rebuy(nome, acao):
    if nome in jogadores:
        if acao == "add":
            jogadores[nome].rebuys += 1
        elif acao == "sub" and jogadores[nome].rebuys > 0:
            jogadores[nome].rebuys -= 1
    return redirect(url_for('index'))

@app.route("/finalizar/<nome>", methods=["POST"])
def finalizar(nome):
    if nome in jogadores:
        fichas = int(request.form['fichas'])
        jogadores[nome].fichas_finais = fichas
    return redirect(url_for('index'))

@app.route("/resumo")
def resumo():
    return render_template_string(template_resumo, jogadores=jogadores)

if __name__ == '__main__':
    app.run(debug=True)
