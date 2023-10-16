from flask import Flask,render_template,request,url_for,redirect,session,escape
from datetime import timedelta
import os
import pymysql

app = Flask(__name__,static_url_path='', static_folder='templates', template_folder='templates')

app.config['SECRET_KEY'] = os.urandom(24)  # 使用Session模块时一定要配置SECRET_KEY全局宏(设置为随机字符串)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # 配置1天有效

db = pymysql.connect(host="localhost",user="root",password="Hx1551986048",database="student")

@app.route('/')
def index():
    homeworks = (('作业一','刘铎','2023-11-02','100'), ('作业二','刘铎','2023-11-09','100'))
    return render_template('student-homeworks.html',homeworks=homeworks)


if __name__ == '__main__':
    app.run(debug=True)