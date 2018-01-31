# coding=utf-8
from __future__ import print_function, absolute_import, unicode_literals
import numpy as np
from gm.api import *
from pandas import DataFrame
'''
本策略以0.8为初始权重跟踪指数标的沪深300中权重大于0.35%的成份股.
个股所占的百分比为(0.8*成份股权重)*100%.然后根据个股是否:
1.连续上涨5天 2.连续下跌5天
来判定个股是否为强势股/弱势股,并对其把权重由0.8调至1.0或0.6
回测时间为:2017-07-01 08:50:00到2017-10-01 17:00:00
'''
def init(context):
    # 资产配置的初始权重,配比为0.6-0.8-1.0
    context.ratio = 0.8
    # 获取沪深300当时的成份股和相关数据
    stock300 = get_history_constituents(index='SHSE.000300', start_date='2017-06-30', end_date='2017-06-30')[0][
        'constituents']
    stock300_symbol = []
    stock300_weight = []
    for key in stock300:
        # 保留权重大于0.35%的成份股
        if (stock300[key] / 100) > 0.0035:
            stock300_symbol.append(key)
            stock300_weight.append(stock300[key] / 100)
    context.stock300 = DataFrame([stock300_weight], columns=stock300_symbol, index=['weight']).T
    print('选择的成分股权重总和为: ', np.sum(stock300_weight))
    subscribe(symbols=stock300_symbol, frequency='1d', count=5, wait_group=True)
def on_bar(context, bars):
    # 若没有仓位则按照初始权重开仓
    for bar in bars:
        symbol = bar['symbol']
        position = context.account().position(symbol=symbol, side=PositionSide_Long)
        if not position:
            buy_percent = context.stock300['weight'][symbol] * context.ratio
            order_target_percent(symbol=symbol, percent=buy_percent, order_type=OrderType_Market,
                                 position_side=PositionSide_Long)
            print(symbol, '以市价单开多仓至仓位:', buy_percent)
        else:
            # 获取过去5天的价格数据,若连续上涨则为强势股,权重+0.2;若连续下跌则为弱势股,权重-0.2
            recent_data = context.data(symbol=symbol, frequency='1d', count=5, fields='close')['close'].tolist()
            if all(np.diff(recent_data) > 0):
                buy_percent = context.stock300['weight'][symbol] * (context.ratio + 0.2)
                order_target_percent(symbol=symbol, percent=buy_percent, order_type=OrderType_Market,
                                     position_side=PositionSide_Long)
                print('强势股', symbol, '以市价单调多仓至仓位:', buy_percent)
            elif all(np.diff(recent_data) < 0):
                buy_percent = context.stock300['weight'][symbol] * (context.ratio - 0.2)
                order_target_percent(symbol=symbol, percent=buy_percent, order_type=OrderType_Market,
                                     position_side=PositionSide_Long)
                print('弱势股', symbol, '以市价单调多仓至仓位:', buy_percent)
if __name__ == '__main__':
    '''
    strategy_id策略ID,由系统生成
    filename文件名,请与本文件名保持一致
    mode实时模式:MODE_LIVE回测模式:MODE_BACKTEST
    token绑定计算机的ID,可在系统设置-密钥管理中生成
    backtest_start_time回测开始时间
    backtest_end_time回测结束时间
    backtest_adjust股票复权方式不复权:ADJUST_NONE前复权:ADJUST_PREV后复权:ADJUST_POST
    backtest_initial_cash回测初始资金
    backtest_commission_ratio回测佣金比例
    backtest_slippage_ratio回测滑点比例
    '''
    run(strategy_id='strategy_id',
        filename='main.py',
        mode=MODE_BACKTEST,
        token='token_id',
        backtest_start_time='2017-07-01 08:50:00',
        backtest_end_time='2017-10-01 17:00:00',
        backtest_adjust=ADJUST_PREV,
        backtest_initial_cash=10000000,
        backtest_commission_ratio=0.0001,
        backtest_slippage_ratio=0.0001)