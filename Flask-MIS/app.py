from flask import Flask,render_template,request,url_for,redirect,session
from datetime import timedelta
import os
import pymysql
from datetime import datetime
from tools import distribute_assess

app = Flask(__name__,static_url_path='', static_folder='templates', template_folder='templates')

app.config['SECRET_KEY'] = os.urandom(24)  # 使用Session模块时一定要配置SECRET_KEY全局宏(设置为随机字符串)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # 配置1天有效

db = pymysql.connect(host="localhost",user="root",password="Hx1551986048",database="student")

@app.route('/')
def index():
    return render_template('Login.html')


# 注册判断
@app.route('/login',methods=['GET', 'POST'])
def login():

    name = str(request.form.get('name'))
    password = str(request.form.get('password'))
    
    cursor = db.cursor()
    sql_1 = "select * from login where username = '"+name +"' and password = '"+password+"'"

    try:
        cursor.execute(sql_1)
        result = cursor.fetchone()
        userId = result[0]
        
        if result != None:
            # 登录成功
            session['user'] = result  # 设置session
            session.permanent = True  # 设置session有效时间

            if result[-1]=='student':
                sql_2 = "select * from s where sno = '"+userId+"'"
                cursor.execute(sql_2)
                student = cursor.fetchone()
                return render_template('student.html',user=student)
            
            elif result[-1]=='teacher':
                sql_2 = "select * from teacher where tno = '"+userId+"'"
                cursor.execute(sql_2)
                teacher = cursor.fetchone()

                # 查询教授课程
                sql_3 = "select course.cname,course.cno,teaching.cid,teaching.time,teaching.classroomno from course,teaching where course.cno = teaching.cno and teaching.tno = '"+userId+"'"
                cursor.execute(sql_3)
                courses = cursor.fetchall()
                return render_template('teacher.html',user=teacher,courses=courses)
            
            elif result[-1]=='administrator':
                return render_template('administrator.html',user=user)
        else:
            # 登陆失败
            return render_template('Login.html',msg='erro')
    except:
        print('Error')


# 学生查看课程平台
@app.route('/sCourses',methods=['GET', 'POST'])
def selctStudentCourses():
    user = session.get("user")
    sno = user[0]

    cursor = db.cursor()
    # 查询学生所选课程
    sql_1 = "select course.cname,sc.cid,teacher.tname,course.cno from sc,course,teacher,teaching where sc.cno = course.cno and teaching.tno = teacher.tno and teaching.cno = course.cno and teaching.cid=sc.cid and sc.sno = '"+sno+"'"

    try:
        cursor.execute(sql_1)
        courses = cursor.fetchall()
        return render_template('student-courses.html',courses=courses)

    except:
        print('Error')
    

# 学生查看课程作业
@app.route('/sHomeworks/<cno>/<tname>',methods=['GET','POST'])
def selctStudentHomeworks(cno,tname):

    now_time = datetime.now()

    user = session.get("user")
    sno = user[0]
    cursor = db.cursor()

    # 查询学生课程作业
    sql_1 = "select homework.title,homework.deadline,homework.score,homework.hid,homework.cno,homeworkcommit.commitTime from sc,homework,homeworkcommit where sc.cno = homework.cno and homework.hid=homeworkcommit.hid and homework.cno=homeworkcommit.cno and homeworkcommit.sno=sc.sno and sc.sno = '%s' and sc.cno = '%s'"
    param = (sno,cno)

    cursor.execute(sql_1%param)
    homeworks = cursor.fetchall()
    return render_template('student-homeworks.html',homeworks=homeworks,tname=tname,now_time=now_time)


# 渲染作业提交页面
@app.route('/showHomeworks/<hid>/<cno>',methods=['GET','POST'])
def showHomeworks(hid,cno):
    
    cursor = db.cursor()
    sql_1 = "select title,content from homework where hid = %s and cno = '%s'"
    param = (hid,cno)

    try:
        cursor.execute(sql_1%param)
        homework = cursor.fetchone()
        return render_template('student-commitHomework.html',homework=homework,hid=hid,cno=cno)
    except:
        print('Error')



# 学生提交课程作业
@app.route('/commitHomeworks/<hid>/<cno>',methods=['GET','POST'])
def commitHomeworks(hid,cno):

    user = session.get("user")
    sno = user[0]

    # 从表单中获取作业内容
    content = str(request.form.get('content'))

    cursor = db.cursor()

    # 学生提交课程作业
    sql_1 = "update homeworkcommit set content='%s',commitTime=now() where sno = '%s' and cno = '%s' and hid = %s"
    param = (content,sno,cno,hid)

    sql_2 = "select teacher.tname from sc,teaching,teacher where sc.cno=teaching.cno and sc.cid=teaching.cid and teacher.tno = teaching.tno and sc.sno = '"+sno+"' and sc.cno = '"+cno+"'"
    
    try:
        cursor.execute(sql_1%param)
        db.commit()

        # 学生提交作业后实现互评工作的分配
        if ~distribute_assess(db,sno,cno,hid):
            print('Error')

        cursor.execute(sql_2)
        tname =cursor.fetchone()[0]
        return redirect('/sHomeworks/'+cno+'/'+tname)

    except:
        print('Error')


# 学生取消提交课程作业
@app.route('/cancelCommitHomeworks/<cno>',methods=['GET','POST'])
def cancelCommitHomeworks(cno):
    cursor = db.cursor()

    user = session.get("user")
    sno = user[0]

    # 查询tname
    sql= "select teacher.tname from sc,teaching,teacher where sc.cno=teaching.cno and sc.cid=teaching.cid and teacher.tno = teaching.tno and sc.sno = '"+sno+"' and sc.cno = '"+cno+"'"
    cursor.execute(sql)
    tname =cursor.fetchone()[0]
    return redirect('/sHomeworks/'+cno+'/'+tname)


# 学生查看互评作业列表
@app.route('/assess',methods=['GET','POST'])
def selctAssessList():

    user = session.get("user")
    sno = user[0]
    cursor = db.cursor()

    # 查询互评作业列表
    sql = "select course.cname,course.cno,homework.title,assess.sno_a,assess.score,assess.hid from assess,homework,course where assess.cno = homework.cno and assess.hid = homework.hid and homework.cno = course.cno and assess.sno = '%s'"
    param = (sno)

    cursor.execute(sql%param)
    assessList = cursor.fetchall()
    return render_template('student-assessList.html',assessList=assessList)


# 学生互评其他学生作业
@app.route('/assessHomework/<sno_a>/<hid>/<cno>',methods=['GET','POST'])
def assessHomework(sno_a,hid,cno):

    user = session.get("user")
    sno = user[0]
    cursor = db.cursor()

    # 将hid放入session中
    session['inform'] = (hid,cno,sno_a)
    session.permanent = True

    # 查询互评学生的作业详情
    sql = "select homework.title,assess.sno_a,homeworkcommit.content,homework.score from homework,homeworkcommit,assess where homework.hid = homeworkcommit.hid and homework.cno = homeworkcommit.cno and assess.cno = homework.cno and assess.hid = homework.hid and homeworkcommit.sno = assess.sno_a and assess.sno = '%s' and assess.sno_a = '%s' and assess.hid = %s and assess.cno = '%s'"
    param = (sno,sno_a,hid,cno)

    cursor.execute(sql%param)
    homework = cursor.fetchone()
    return render_template('student-assessHomework.html',homework=homework)


# 学生提交作业互评结果
@app.route('/commitAssess',methods=['GET','POST'])
def commitAssess():

    user = session.get("user")
    sno = user[0]

    inform = session.get("inform")

    # 获取提交结果
    score = str(request.form.get('score'))
    assess = str(request.form.get('assess'))

    cursor = db.cursor()

    # 提交作业互评成绩和评价
    sql = "update assess set score = %s , assess = '%s' where sno = '%s' and hid = %s and cno = '%s' and sno_a = '%s'"
    param = (score,assess,sno,inform[0],inform[1],inform[2])

    print(sql%param)
    cursor.execute(sql%param)
    db.commit()

    return redirect('/assess')


# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# 教师查看教授课程
@app.route('/tCourses',methods=['GET', 'POST'])
def selctTeacherCourses():
    user = session.get("user")
    tno = user[0]

    cursor = db.cursor()
    # 查询教师教授课程
    sql_1 = "select course.cname,course.cno,teaching.cid from course,teaching where teaching.cno = course.cno and teaching.tno = '"+tno+"'"

    try:
        cursor.execute(sql_1)
        courses = cursor.fetchall()
        return render_template('teacher-courses.html',courses=courses)

    except:
        print('Error')



# 教师查看课程作业
@app.route('/tHomework/<cno>',methods=['GET','POST'])
def tHomework(cno):

    now_time = datetime.now()

    user = session.get("user")
    tno = user[0]
    cursor = db.cursor()

    # 将cno保存至session
    session['cno'] = cno
    session.permanent = True

    # 查询教师课程作业
    sql_1 = "select homework.title,homework.deadline,homework.score,homework.hid from teaching,homework where teaching.cno = homework.cno and teaching.cno = '%s' and teaching.tno='%s'"
    param = (cno,tno)

    try:
        cursor.execute(sql_1%param)
        homeworks = cursor.fetchall()
        return render_template('teacher-homeworks.html',homeworks=homeworks,now_time=now_time,cno=cno)

    except:
        print('Error')


# 跳转至作业布置界面
@app.route('/show',methods=['GET','POST'])
def show():
    return render_template('teacher-setHomework.html')


# 教师布置作业
@app.route('/setHomework',methods=['GET','POST'])
def setHomework():

    title = str(request.form.get('title'))
    deadline = str(request.form.get('deadline'))
    score = str(request.form.get('score'))
    content = str(request.form.get('content'))

    # 从session中获取cno, 然后删除session中的cno
    cno = session.get("cno")
    # session.pop("cno")

    cursor = db.cursor()


    # 教师插入课程作业
    sql_1 = "insert into homework values(NULL,'%s','%s','%s','%s',%s)"
    param_1 = (cno,title,content,deadline,score)

    sql_2 = "select hid from homework where cno = '%s' and title = '%s'"
    param_2 = (cno,title)

    sql_3 = "select distinct(sno) from sc where cno = '%s'"
    param_3 = (cno)


    try:
        cursor.execute(sql_1%param_1)
        db.commit()

        cursor.execute(sql_2%param_2)
        hid = cursor.fetchone()[0]
        
        cursor.execute(sql_3%param_3)
        snos = cursor.fetchall()

        print(hid,snos)

        for sno in snos:
            sql = "insert into homeworkcommit (sno,cno,hid) values('%s','%s',%s)"
            print(sql)
            param = (sno[0],cno,hid)
            cursor.execute(sql%param)
            db.commit()
            
        return redirect("/tHomework/"+cno)

    except:
        print('Error')



# 教师取消布置课程作业
@app.route('/cancelSetHomeworks',methods=['GET','POST'])
def cancelSetHomeworks():

    # 从session中获取cno, 然后删除session中的cno
    cno = session.get("cno")
    # session.pop("cno")

    return redirect("/tHomework/"+cno)


# 教师查看所有学生作业
@app.route('/checkStudentHomeworks/<hid>',methods=['GET','POST'])
def checkStudentHomeworks(hid):

    cno = session.get('cno')
    # session.pop("cno")

    cursor = db.cursor()
    sql_1 = "select s.sname,s.sno,homeworkcommit.commitTime from homeworkcommit,sc,s where homeworkcommit.sno=sc.sno and sc.sno=s.sno and sc.cno=homeworkcommit.cno and sc.cno = '%s' and homeworkcommit.hid = %s"
    param_1 = (cno,hid)

    sql_2 = "select title,content from homework where cno = '%s' and hid = %s"
    param_2 = (cno,hid)


    cursor.execute(sql_1%param_1)
    homeworks = cursor.fetchall()

    cursor.execute(sql_2%param_2)
    title = cursor.fetchone()

    return render_template('teacher-checkStudentHomework.html',homeworks=homeworks,title=title,hid=hid)



# 教师查看单个学生作业详情
@app.route('/checkOneHomework/<sno>/<hid>',methods=['GET','POST'])
def checkOneHomework(sno,hid):

    cno = session.get('cno')
    # session.pop("cno")

    cursor = db.cursor()
    sql_1 = "select s.sno,s.sname,homeworkcommit.commitTime,homeworkcommit.content from homeworkcommit,s where homeworkcommit.sno = s.sno and s.sno = '%s' and homeworkcommit.cno = '%s' and homeworkcommit.hid = %s"
    param_1 = (sno,cno,hid)

    cursor.execute(sql_1%param_1)
    homework = cursor.fetchone()

    return render_template('teacher-checkOneHomework.html',homework=homework)




# 重定向到主页面
@app.route('/redirect',methods=['GET', 'POST'])
def reDirect():
    user = session.get("user")
    userId = user[0]

    cursor = db.cursor()

    try:
        if user[-1]=='student':
            sql_1 = "select * from s where sno = '"+userId+"'"
            cursor.execute(sql_1)
            student = cursor.fetchone()
            return render_template('student.html',user=student)
                
        elif user[-1]=='teacher':
            sql_1 = "select * from teacher where tno = '"+userId+"'"
            cursor.execute(sql_1)
            teacher = cursor.fetchone()

            # 查询教授课程
            sql_2 = "select course.cname,course.cno,teaching.cid,teaching.time,teaching.classroomno from course,teaching where course.cno = teaching.cno and teaching.tno = '"+userId+"'"
            cursor.execute(sql_2)
            courses = cursor.fetchall()
            return render_template('teacher.html',user=teacher,courses=courses)
                
        elif user[-1]=='administrator':
            return render_template('administrator.html',user=user)
    except:
        print('Error')


if __name__ == '__main__':
    # app.run(host='0.0.0.0',port=9000,debug=True)
    app.run(debug=True)
 


