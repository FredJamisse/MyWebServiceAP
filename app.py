# app.py
from flask import Flask, jsonify, request

app = Flask(__name__)

# Rota raiz
@app.route('/')
def home():
    return jsonify({
        "status": "OK",
        "message": "MyWebServiceAP está ativo "
    })

# Exemplo de endpoint com parâmetros (POST)
@app.route('/api/somar', methods=['POST'])
def somar():
    data = request.get_json()
    a = data.get('a', 0)
    b = data.get('b', 0)
    resultado = a + b
    return jsonify({
        "a": a,
        "b": b,
        "resultado": resultado
    })

# Rota GET simples
@app.route('/api/hello/<nome>')
def hello(nome):
    return jsonify({
        "mensagem": f"Olá, {nome}! Bem-vindo ao MyWebServiceAP."
    })

if __name__ == '__main__':
    # Executa localmente em modo debug
    app.run(host='0.0.0.0', port=5000, debug=True)
