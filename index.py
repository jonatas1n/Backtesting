from process import get_importance
from flask import Flask, request, render_template
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app, CORS_ORIGINS="*")
app.config['CORS_HEADERS'] = 'Content-Type'

fields = ['rebaixamento', 'sharpe', 'fator_rec', 'fator_lucro', 'payoff']
replace_fields = {
    'rebaixamento': '% Reb',
    'sharpe': 'Índice Sharpe',
    'fator_rec': 'Fator Rec.',
    'fator_lucro': 'Fator Lucro',
    'payoff': 'Payoff'
}

@app.route("/", methods=['GET'])
@cross_origin()
def show_page():
    return render_template('index.html')

@app.route("/", methods=['POST'])
@cross_origin()
def process_file():
    files = ['file_1', 'file_2', 'file_5']
    files = [request.files[file].read() for file in files]

    def clean_to_float(data):
        data = str(data)
        data = data.replace(',', '.')
        data = data.replace('(', '')
        data = data.replace(')', '')
        return float(data)

    calc_fields = {}

    for field in fields:
        if 'use_' + field in request.form:
            is_max = field + '_minmax' in request.form
            value = clean_to_float(request.form[field])
            calc_fields[replace_fields[field]] = {'is_max': is_max, 'value': value}

    crescente = 'crescente' in request.form
    lucros_positivos = 'positivos' in request.form

    print(crescente, lucros_positivos)

    df, fails = get_importance(files, calc_fields, crescente, lucros_positivos)
    if len(df) == 0:
        table = '<h5 class="w-100 font-italic text-secondary">Nenhum dos símbolos satisfez aos filtros aplicados.</h4>'
    else:
        table = df.to_html(classes="table-striped table table-hover", table_id="main-table", index=False)
    fails = fails.to_html(classes="table-striped table table-hover", table_id="fails-table", index=False)
    return render_template('result.html', table=table, fails=fails)

if __name__ == "__main__":
    app.run(debug=True)