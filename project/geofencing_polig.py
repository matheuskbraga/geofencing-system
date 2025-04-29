from flask import Flask, request, render_template
from shapely.geometry import Point, Polygon

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('mapa.html')

@app.route('/verificar', methods=['POST'])
def verificar():
    data = request.json
    pontos_poligono = [(p['lat'], p['lng']) for p in data['poligono']]
    ponto_teste = (data['ponto']['lat'], data['ponto']['lng'])

    poligono = Polygon(pontos_poligono)
    ponto = Point(ponto_teste)

    dentro = poligono.contains(ponto)
    return {'dentro': dentro}

if __name__ == '__main__':
    app.run(debug=True)
