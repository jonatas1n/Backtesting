import pandas as pd
import xmltodict

def get_importance(files, fields_parameters, use_ascending_profit=True, positive_profit=True):
    #Clean file
    def clean_to_float(data):
        data = str(data)
        data = data.replace(',', '.')
        data = data.replace('(', '')
        data = data.replace(')', '')
        return float(data)

    dataframes = []
    columns_names = ['Symbol', 'Profit', 'Payoff', 'Fator Lucro', 'Fator Rec.', 'Índice Sharpe', '% Reb', 'Trade']
    float_columns = ['Profit', 'Payoff', '% Reb', 'Fator Lucro', 'Índice Sharpe', "Fator Rec."]

    for file in files:
        xmlDict = xmltodict.parse(file)
        cols = [item['Data']['#text'] for item in xmlDict['Workbook']['Worksheet']['Table']['Row'][0]['Cell']]
        rows = [item['Cell'] for item in xmlDict['Workbook']['Worksheet']['Table']['Row'][1:]]
        for index, row in enumerate(rows):
            new_row = []
            for item in [item['Data'] for item in row]:
                if not '#text' in item.keys():
                    item['#text'] = '0'
                new_row.append(item['#text'])
            rows[index] = new_row
        
        df = pd.DataFrame(rows, columns=cols)
        df.drop(['Pass', 'Result', 'Custom'], axis=1, inplace=True)
        df.sort_values(by=['Symbol'], inplace=True)
        df.columns = columns_names

        for column in float_columns:
            df[column] = df[column].apply(clean_to_float)

        dataframes.append(df)

    filtered = {}

    #Set filtering functions
    def profit_positive(periodo_1, periodo_2, periodo_3):
        profits = periodo_1['Profit'], periodo_2['Profit'], periodo_3['Profit']
        profits = [x.values[0] > 0 for x in profits]
        return not positive_profit or all(profits)

    def profit_ascending(periodo_1, periodo_2, periodo_3):
        profit_1, profit_2, profit_3 = periodo_1['Profit'].values[0], periodo_2['Profit'].values[0], periodo_3['Profit'].values[0]
        return not use_ascending_profit or (profit_1 <= profit_2 <= profit_3)

    def check_parameter(periodo_1, periodo_2, periodo_3, parameter, is_max, value):
        value_1, value_2, value_3 = periodo_1[parameter].values[0], periodo_2[parameter].values[0], periodo_3[parameter].values[0]
        if is_max:
            return value_1 <= value and value_2 <= value and value_3 <= value
        return value_1 >= value and value_2 >= value and value_3 >= value

    #Reply Function
    def create_reply(parameter, data):
        if data['is_max']:
            return 'O ' + parameter + ' máximo é ' + str(data['value'])
        return 'O ' + parameter + ' mínimo é ' + str(data['value'])

    filtered_keys = ['Lucros negativos', 'Lucro não crescente']
    check_functions = [profit_positive, profit_ascending]

    Symbols_to_remove = []
    Symbols_list = dataframes[0]['Symbol'].values

    for Symbol in Symbols_list:
        row_1 = dataframes[0][dataframes[0]['Symbol'] == Symbol]
        row_2 = dataframes[1][dataframes[1]['Symbol'] == Symbol]
        row_5 = dataframes[2][dataframes[2]['Symbol'] == Symbol]
        
        for i, function in enumerate(check_functions):
            if not function(row_1, row_2, row_5):
                if Symbol not in filtered:
                    filtered[Symbol] = []
                filtered[Symbol].append(filtered_keys[i])
                Symbols_to_remove.append(Symbol)
                continue

        for parameter in fields_parameters.keys():
            if not check_parameter(row_1, row_2, row_5, parameter, fields_parameters[parameter]['is_max'], fields_parameters[parameter]['value']):
                if Symbol not in filtered:
                    filtered[Symbol] = []
                filtered[Symbol].append(create_reply(parameter, fields_parameters[parameter]))
                Symbols_to_remove.append(Symbol)

    for key, value in filtered.items():
        filtered[key] = [key] + [" | ".join(value)]

    gaspar = dataframes[2]
    for key in Symbols_to_remove:
        gaspar.drop(gaspar[gaspar['Symbol'] == key].index, inplace=True)
    gaspar = gaspar.reset_index().drop(columns=['index'])


    # Set importance calculations
    importance_order = ['Fator Lucro', 'Índice Sharpe', '% Reb', 'Fator Rec.', 'Payoff']

    for item in importance_order:
        is_ascending = item == '% Reb'
        gaspar = gaspar.sort_values(by=[item], ascending=is_ascending)
        gaspar = gaspar.reset_index().drop(columns=['index'])
        selection = list(range(1, len(gaspar)+1))
        selection = pd.DataFrame(selection, columns=[item + "*"])
        gaspar = pd.concat([gaspar, selection], axis=1)

    importance = gaspar.iloc[:, 8:]
    importance = pd.concat([gaspar.iloc[:, :1], importance], axis=1)
    importance = importance.sort_values(by=['Symbol'])
    importance = importance.reset_index().drop(columns=['index'])

    column_sum = importance.iloc[:, 1:]
    for i, value in enumerate(importance_order):
        column_sum[value+"*"] = column_sum[value+'*'].apply(lambda x: x * (5 - i))

    column_sum = column_sum.sum(axis=1)
    column_sum = column_sum.apply(lambda x: x / 15)
    column_sum = column_sum.reset_index().drop(columns=['index'])

    gaspar = gaspar.iloc[:, :7]
    gaspar = pd.concat([gaspar, column_sum], axis=1)
    gaspar = gaspar.sort_values(by=[0], ascending=False)
    gaspar.rename(columns={0: 'Result'}, inplace=True)

    fails = pd.DataFrame.from_dict(data=filtered, columns=['Symbol', "Motivos"], orient='index')

    return gaspar, fails