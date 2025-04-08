import os
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# --- Modelo de Jogador ---
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

# --- Dados da Mesa ---
jogadores = {}

# --- Templates HTML ---
template_index = """template_index = """
<!DOCTYPE html>
<html>
<head>
    <title>POKER & RESENHA</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <link rel="manifest" href="/static/manifest.json">
    <link rel="icon" href="/static/pwa-icon-192-poker.png" type="image/png">
    <meta name="theme-color" content="#001133">

    <script>
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js')
          .then(() => console.log("✅ Service Worker registrado"))
          .catch(err => console.error("Erro ao registrar SW:", err));
      }
    </script>

    <style>
        body { background-color: #001; color: #fff; font-family: Arial, sans-serif; margin: 0; padding: 0;
               min-height: 100vh; display: flex; flex-direction: column; align-items: center; }
        .container {
            width: 100%; max-width: 414px; min-height: 736px;
            margin: 0 auto; padding: 20px; box-sizing: border-box;
            display: flex; flex-direction: column; align-items: center;
        }
        input, button { padding: 10px; margin: 5px; width: 90%; max-width: 300px;
                        border-radius: 5px; border: 1px solid #444; }
        ul { list-style: none; padding: 0; width: 100%; }
        li { margin: 15px 0; font-size: 18px; background: #111; padding: 15px;
             border-radius: 10px; text-align: center; }
        a, button { color: #fff; background-color: #444; border: none; border-radius: 5px;
                    cursor: pointer; padding: 10px 20px; text-decoration: none;
                    display: inline-block; margin: 5px; }
        a:hover, button:hover { background-color: #666; }
        form.inline { display: flex; flex-direction: column; align-items: center; width: 100%; }
        #timer { font-size: 80px; text-align: center; margin: 20px auto; color: #0f0; }
        #timer-controls { text-align: center; margin-bottom: 30px; width: 100%; }
        h1, h2 { text-align: center; width: 100%; }
        .actions { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; width: 100%; }
    </style>
</head>
<body>
    <div class="container">
        <h1>POKER & RESENHA</h1>
        <div id="timer">04:00:00</div>
        <div id="timer-controls">
            <button onclick="startTimer()">Iniciar</button>
            <button onclick="toggleTimer()">Pausar/Retomar</button>
        </div>
        <h2>Adicionar Jogador</h2>
        <form id="addForm" style="width: 100%; text-align: center;">
            <input type="text" id="nomeInput" required placeholder="Nome do Jogador">
            <button type="submit">Adicionar</button>
        </form>
        <h2>Jogadores</h2>
        <ul id="jogadoresList"></ul>
        <br>
        <button onclick="limparEstado()" style="width: 80%;">🔄 Resetar Mesa</button>
    </div>

    <script>
        var totalSeconds = 4 * 60 * 60;
        var paused = true;
        var started = false;

        function formatTime(seconds) {
            var h = String(Math.floor(seconds / 3600)).padStart(2, '0');
            var m = String(Math.floor((seconds % 3600) / 60)).padStart(2, '0');
            var s = String(seconds % 60).padStart(2, '0');
            return h + ":" + m + ":" + s;
        }

        function updateTimer() {
            if (!paused && totalSeconds > 0) {
                totalSeconds--;
                document.getElementById("timer").textContent = formatTime(totalSeconds);
            }
        }

        function startTimer() {
            if (!started) {
                started = true;
                paused = false;
            }
        }

        function toggleTimer() {
            if (started) {
                paused = !paused;
            }
        }

        setInterval(updateTimer, 1000);

        // ========== LOCALSTORAGE ==========
        let jogadores = {};

        function salvarEstado() {
            localStorage.setItem("jogadores", JSON.stringify(jogadores));
        }

        function carregarEstado() {
            const salvo = localStorage.getItem("jogadores");
            if (salvo) {
                jogadores = JSON.parse(salvo);
                renderJogadores();
            }
        }

        function renderJogadores() {
            const ul = document.getElementById("jogadoresList");
            ul.innerHTML = "";
            for (const nome in jogadores) {
                const j = jogadores[nome];
                const li = document.createElement("li");
                li.innerHTML = `
                    <strong>${j.nome}</strong><br>
                    Buy-ins: ${j.buy_ins} | Rebuys: ${j.rebuys}<br>
                    <div class="actions">
                        <button onclick="mudarRebuy('${nome}', 1)">+ Rebuy</button>
                        <button onclick="mudarRebuy('${nome}', -1)">- Rebuy</button>
                    </div>
                    <form onsubmit="return registrarFichas('${nome}', this)">
                        <input type="number" name="fichas" min="0" placeholder="Fichas finais">
                        <button type="submit">Registrar</button>
                    </form>
                `;
                ul.appendChild(li);
            }
        }

        function mudarRebuy(nome, delta) {
            if (jogadores[nome]) {
                jogadores[nome].rebuys += delta;
                if (jogadores[nome].rebuys < 0) jogadores[nome].rebuys = 0;
                salvarEstado();
                renderJogadores();
            }
        }

        function registrarFichas(nome, form) {
            const fichas = parseInt(form.fichas.value);
            if (!isNaN(fichas)) {
                jogadores[nome].fichas_finais = fichas;
                salvarEstado();
                renderJogadores();
            }
            return false;
        }

        function limparEstado() {
            if (confirm("Tem certeza que deseja resetar a mesa?")) {
                localStorage.removeItem("jogadores");
                jogadores = {};
                renderJogadores();
            }
        }

        document.getElementById("addForm").addEventListener("submit", function (e) {
            e.preventDefault();
            const nome = document.getElementById("nomeInput").value.trim();
            if (nome && !jogadores[nome]) {
                jogadores[nome] = {
                    nome: nome,
                    buy_ins: 1,
                    rebuys: 0,
                    fichas_finais: 0
                };
                document.getElementById("nomeInput").value = "";
                salvarEstado();
                renderJogadores();
            }
        });

        carregarEstado();
    </script>
</body>
</html>
"""

"""

template_resumo = """
<!DOCTYPE html>
<html>
<head>
    <title>Resumo Final</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background-color: #000; color: #fff; font-family: Arial, sans-serif; margin: 0; padding: 0;
               min-height: 100vh; display: flex; flex-direction: column; align-items: center; }
        .container {
            width: 100%; max-width: 414px; min-height: 736px;
            margin: 0 auto; padding: 20px; box-sizing: border-box;
        }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; }
        th, td { border: 1px solid #888; padding: 8px; text-align: center; }
        th { background-color: #222; }
        h1 { text-align: center; }
        a { color: #fff; background-color: #444; text-decoration: none; padding: 10px 20px;
            border-radius: 5px; display: block; text-align: center; margin: 20px auto; width: 80%; }
        a:hover { background-color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>💸 CHECKOUT 💸</h1>
        <div style="overflow-x: auto;">
            <table>
                <tr>
                    <th>Nome</th>
                    <th>Buy-ins</th>
                    <th>Rebuys</th>
                    <th>Total</th>
                    <th>Final</th>
                    <th>Saldo</th>
                </tr>
                {% for j in jogadores.values() %}
                <tr>
                    <td>{{ j.nome }}</td>
                    <td>{{ j.buy_ins }}</td>
                    <td>{{ j.rebuys }}</td>
                    <td>{{ j.total_fichas }}</td>
                    <td>{{ j.fichas_finais }}</td>
                    <td>{{ j.saldo_final }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        <a href="/">Voltar</a>
    </div>
</body>
</html>
"""

# --- Rotas ---
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

# --- Execução compatível com Render ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
