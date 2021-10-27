#載入LineBot所需要的套件
from flask import Flask, request, abort
import time
import pandas as pd
import yahoo_fin.stock_info as si
import numpy as np
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import ( 
    InvalidSignatureError
)
from linebot.models import *
import schedule
import datetime
import re


app = Flask(__name__)

# 必須放上自己的Channel Access Token
line_bot_api = LineBotApi('52bhA1czfLbYrFnlU38eUlDxGjkLHhOpRmAmJmWCFvok+dO/rn+BORTuA12QTat/nx3ZuplLZYQ3cnGMqy6eKn62+3edvyjcoYXrj/LxB5mT68Avgx5wnDa9swhwHsYMJZvdKZOKgEYoU0r6EJrpkQdB04t89/1O/w1cDnyilFU=')
# 必須放上自己的Channel Secret
handler = WebhookHandler('223cbe254528bf518e42358505c97bdb')

line_bot_api.push_message('U9e6f525ecd8275e7d12127dbad547c79', TextSendMessage(text='你可以開始了'))

uspric = pd.DataFrame(columns=['stock','bs','print', 'date_info','type'])
yourid = 'U9e6f525ecd8275e7d12127dbad547c79'
# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


#--------------儲存使用者的股票--------------
def write_user_stock_function(stock,bs,price,uspric):
    df=pd.DataFrame([(stock,bs,price,datetime.datetime.utcnow(),'care_stock')],columns=['stock','bs','price', 'date_info','type'])
    uspric=uspric.append(df)
    uspric.reset_index(inplace=True, drop=True)
    return uspric
#--------------刪除使用者的股票--------------
def delete_user_stock_function(stock,uspric):
    uspric.drop(index=uspric.index[np.where(uspric['stock']==stock)[0]],inplace=True)
    return uspric
#--------------秀出使用者的股票--------------
def job():
    fliter=uspric[uspric['type']=='care_stock']
    for index,row in fliter.iterrows():
        stock=row['stock']
        bs=row['bs']
        price=float(row['price']) 
        nowstock=si.get_live_price(str(row['stock'])+'.TW')
        if bs == '<'or'＜':
            if float(nowstock) < price:
                get=str(stock)+'的價格已經低於'+str(price)+'\n'+str(stock)+'價格為:'+str(nowstock)
                line_bot_api.push_message(yourid,TextSendMessage(text=get))
        elif bs == '＞'or'>':
            if float(nowstock) > price:
                get=str(stock)+'的價格已經超過'+str(price)+'\n'+str(stock)+'價格為:'+str(nowstock)
                line_bot_api.push_message(yourid,TextSendMessage(text=get))
        else :
            if float(nowstock) == price:
                get=str(stock)+'的價格抵達'+str(price)+'\n'+str(stock)+'價格為:'+str(nowstock)
                line_bot_api.push_message(yourid,TextSendMessage(text=get))
    second_5_j = schedule.every(10).seconds.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)




#訊息傳遞區塊
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    
    ##抓到客戶資料##
    profile=line_bot_api.get_profile(event.source.user_id)
    uid = profile.user_id
    usespeak = str(event.message.text)
    #判斷是否為要儲存的資料
    if re.match('[0-9]{4}[<>=＜＞＝][0-9]',usespeak):
        write_user_stock_function(stock=usespeak[0:4],bs=usespeak[4:5],price=usespeak[5:],uspric=uspric)
        line_bot_api.push_message(uid,TextSendMessage(usespeak[0:4]+'這支股票已經儲存進關注清單'))
        return 0
    elif re.match('刪除[0-9]{4}',usespeak):
        delete_user_stock_function(stock=usespeak[2:],uspric=uspric)
        line_bot_api.push_message(uid,TextSendMessage(usespeak + '成功'))
        return 0

#主程式
import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)