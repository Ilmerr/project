import websocket
from talib import abstract
import numpy as np
import json

cc = 'btcusdt'
interval ='1m'

socket = f'wss://stream.binance.com:9443/ws/{cc}@kline_{interval}'

amount = 1000
core_trade_amount = amount*0.90
trade_amount = amount*0.10
core_quantity = 0
core_to_trade = True
transaction_cost = 0.0005
min_trade_amt = 30

portfolio = 0
investment, real_time_port_value, opens, highs, lows, closes, volumes = [], [], [], [], [], [], []
money_end = amount
candles = [opens, highs, lows, closes, volumes]

# Функции для торговли
def buy(allocated_money, price):
    global money_end, portfolio, investment
    quantity = allocated_money / price
    money_end = money_end - allocated_money - transaction_cost*allocated_money
    portfolio += quantity
    if investment ==[]:
        investment.append(allocated_money)
    else:
        investment.append(allocated_money)
        investment[-1] += investment[-2]

def sell(allocated_money, price):
    global money_end, portfolio, investment
    quantity = allocated_money / price
    money_end = money_end + allocated_money - transaction_cost*allocated_money
    portfolio -= quantity
    investment.append(-allocated_money)
    investment[-1] += investment[-2]

f = abstract

dir1 = dir(f)
public_method_names = [method for method in dir1 if method.startswith('CDL')]

def on_close(ws, close_status_code, close_msg):
    global money_end
    portfolio_value = portfolio*closes[-1]
    if portfolio_value > 0:
        sell(portfolio_value, closes[-1])
    else:
        buy(-portfolio_value, price = closes[-1])
    money_end += investment[-1]
    print(f'Результат: ${money_end}', '\n')

    beginning = closes[0]
    end = closes[-1]

    #Показатели
    btc_return = np.mean(np.log(np.array(closes[1:]) / np.array(closes[:-1])))
    bot_return = np.mean(np.log(np.array(real_time_port_value[1:]) / np.array(real_time_port_value[:-1])))
    alpha = bot_return - btc_return
    btc_risk = np.std(np.log(np.array(closes[1:]) / np.array(closes[:-1])))
    bot_risk = np.std(np.log(np.array(real_time_port_value[1:]) / np.array(real_time_port_value[:-1])))
    btc_sharpe_ratio = round(btc_return / btc_risk, 3)
    bot_charpe_ratio = round(bot_return / bot_risk, 3)

    print(f'Отдача биткоина: {btc_return}', '\n')
    print(f'Отдача бота: {bot_return} ', '\n')
    print(f'Альфа-фактор: {alpha}', '\n')
    print(f'Коэффицент Шарпа для биткоина: {btc_sharpe_ratio}', '\n')
    print(f'Коэффицент Шарпа для бота: {bot_charpe_ratio}', '\n')

def on_message(ws, message):
    global portfolio, investment, closes, highs, lows, money_end, core_to_trade, core_quantity, real_time_port_value
    json_message = json.loads(message)
    cs = json_message['k']
    candle_closed, close, high, low, open, volume = cs['x'], cs['c'], cs['h'], cs['l'], cs['o'], cs['v']
    candle = [open, high, low, close, volume]
    if candle_closed:
        for i in candles:
            i.append(float(candle[candles.index(i)]))
        print(f'Closes: {closes}')

        inputs = {'open': np.array(opens), 'high': np.array(highs), 'low': np.array(lows), 'close': np.array(closes), 'volume': np.array(volumes)}

        if core_to_trade:
            buy(core_trade_amount, closes[-1])
            print(f'Приобретено биткоина на сумму в ${core_trade_amount} (основное вложение)', '\n')
            core_quantity += core_trade_amount / closes[-1]
            core_to_trade = False

        indicators = []

        for method in public_method_names:
            indicator = getattr(f, method)(inputs)
            indicators.append(indicator[-1])
        av_indicators = np.mean(indicators)

        if av_indicators >= 10:
            amt = trade_amount
        elif av_indicators <= -10:
            amt = -trade_amount
        else:
            amt = av_indicators*10

        port_value = portfolio*closes[-1] - core_quantity*closes[-1]
        trade_amt = amt - port_value
        RT_port_value = money_end + portfolio*closes[-1]
        real_time_port_value.append(float(RT_port_value))
        print(f'Среднее всех индикаторов - "{av_indicators}", и рекомендуемый лимит торговли ${amt}')
        print(f'Стоимость портфеля в данный момент: ${RT_port_value}', '\n')
        print(f'Вложенные средства: ${portfolio*closes[-1]}')

        if trade_amt > min_trade_amt:
            buy(trade_amt, price=closes[-1])
            print(f'Приобретено биткоина на сумму ${trade_amt}', '\n', '\n')
        elif trade_amt < -min_trade_amt:
            sell(-trade_amt, price=closes[-1])
            print(f'Продано биткоина на сумму ${-trade_amt}', '\n', '\n')



ws = websocket.WebSocketApp(socket, on_message = on_message, on_close = on_close)
ws.run_forever()
