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
        
        if result != None:
            # 登录成功
            userId = result[0]
            
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



# 学生查看自己作业的评价
@app.route('/myHomeworkAssess/<hid>/<cno>',methods=['GET','POST'])
def myHomeworkAssess(hid,cno):

    user = session.get("user")
    sno = user[0]
    cursor = db.cursor()

    session['myAssessInform'] = (cno,hid)
    session.permanent = True

    # 查询学生课程作业
    sql_1 = "select assess.score,assess.assess,assess.sno,appeal.statue from assess left join appeal on assess.sno = appeal.sno_a and assess.cno = appeal.cno and assess.hid = appeal.hid and assess.sno_a = appeal.sno where assess.sno_a = '%s' and assess.cno = '%s' and assess.hid = %s"
    param_1 = (sno,cno,hid)

    sql_2 = "select homework.title,homework.score,homeworkcommit.content from homework,homeworkcommit where homework.cno = homeworkcommit.cno and homework.hid = homeworkcommit.hid and homeworkcommit.sno = '%s' and homework.cno = '%s' and homework.hid = %s"
    param_2 = (sno,cno,hid)

    cursor.execute(sql_1%param_1)
    assesses = cursor.fetchall()

    cursor.execute(sql_2%param_2)
    homework = cursor.fetchone()

    return render_template('student-myHomeworkAssess.html',assesses=assesses,homework=homework)



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
    sql_1 = "update assess set score = %s , assess = '%s' where sno = '%s' and hid = %s and cno = '%s' and sno_a = '%s'"
    param_1 = (score,assess,sno,inform[0],inform[1],inform[2])

    cursor.execute(sql_1%param_1)
    db.commit()

    sql_2 = "select assess.score,assess_num.w from assess,assess_num where assess.sno = assess_num.sno and assess.cno = assess_num.cno and assess.hid = %s and assess.cno = '%s' and assess.sno_a = '%s'"
    param_2 = (inform[0],inform[1],inform[2])

    sql_3 = "select score from homeworkcommit where sno = '%s' and cno = '%s' and hid = %s"
    param_3 = (inform[2],inform[1],inform[0])
    
    cursor.execute(sql_2%param_2)
    scores = cursor.fetchall()

    len = 0
    sum_w = 0
    # 获取当前所有互评分数和权重总和
    for score in scores:
        if score[0] != None:
            sum_w = sum_w + score[1]
            len = len + 1
    
    # 获取当前分数,如果不为None,则表示老师已经评价过该作业
    cursor.execute(sql_3%param_3)
    appeal_score = cursor.fetchone()[0]

    # 按照权重来求作业均分
    avg_score = 0
    if len == 3 and appeal_score == None:
        for score in scores:
            avg_score = avg_score + score[0] * (score[1]/sum_w)

        sql_4 = "update homeworkcommit set score = %s where hid = %s and cno = '%s' and sno = '%s'"
        param_4 = (avg_score,inform[0],inform[1],inform[2])

        cursor.execute(sql_4%param_4)
        db.commit()

    return redirect('/assess')



# 学生提交互评申诉
@app.route('/comfirmAppeal/<sno_a>',methods=['GET','POST'])
def comfirmAppeal(sno_a):

    user = session.get("user")
    sno = user[0]
    cursor = db.cursor()

    inform = session.get("myAssessInform")

    # 提交互评申诉
    sql = "insert into appeal values('%s','%s',%s,'%s','F',NULL)"
    param = (sno,inform[0],inform[1],sno_a)

    cursor.execute(sql%param)
    db.commit()

    return redirect("/myHomeworkAssess/"+inform[1]+"/"+inform[0])


# 学生查看申诉列表
@app.route('/selectAppeal',methods=['GET','POST'])
def selectAppeal():

    user = session.get("user")
    sno = user[0]
    cursor = db.cursor()

    # 查看申诉列表
    sql = "select course.cname,homework.title,assess.score,homework.score,appeal.statue,appeal.inform from appeal,homework,course,assess where appeal.sno = assess.sno_a and appeal.cno = assess.cno and appeal.hid = assess.hid and appeal.sno_a = assess.sno and appeal.cno = course.cno and appeal.cno = homework.cno and appeal.hid = homework.hid and appeal.sno = '%s'" 
    param = (sno)

    cursor.execute(sql%param)
    informs = cursor.fetchall()

    return render_template("student-appeal.html",informs=informs)


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

    sql_2 = "select LAST_INSERT_ID()"

    sql_3 = "select distinct(sno) from sc where cno = '%s'"
    param_3 = (cno)


    cursor.execute(sql_1%param_1)
    db.commit()

    cursor.execute(sql_2)
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



# 教师查看学生互评申诉列表
@app.route('/checkAppealList',methods=['GET','POST'])
def checkAppealList():

    user = session.get("user")
    tno = user[0]
    cursor = db.cursor()

    sql_1 = "select course.cname,homework.title,appeal.sno,appeal.sno_a,assess.score,homework.score,appeal.statue,assess.cno,assess.hid from teaching,sc,appeal,homework,course,assess where teaching.cno = appeal.cno and teaching.cid = sc.cid and sc.sno = appeal.sno and sc.cno = appeal.cno and appeal.sno = assess.sno_a and assess.cno = appeal.cno and assess.hid = appeal.hid and assess.sno = appeal.sno_a and appeal.cno = homework.cno and appeal.hid = homework.hid and appeal.cno = course.cno and teaching.tno = '%s'"
    param_1 = (tno)

    cursor.execute(sql_1%param_1)
    informs = cursor.fetchall()

    return render_template('teacher-appealList.html',informs=informs)




# 教师进行申诉处理
@app.route('/handleAppeal/<sno>/<sno_a>/<cno>/<hid>',methods=['GET','POST'])
def handleAppeal(sno,sno_a,cno,hid):

    user = session.get("user")
    tno = user[0]
    cursor = db.cursor()

    # 将信息保存在session中
    session['inform'] = (sno,sno_a,cno,hid)
    session.permanent = True

    sql_1 = "select s.sno,s.sname,assess_num.w from s,assess_num where s.sno = assess_num.sno and s.sno = '%s' and assess_num.cno = '%s'"
    param_1 = (sno,cno)

    sql_2 = "select s.sno,s.sname,assess_num.w from s,assess_num where s.sno = assess_num.sno and s.sno = '%s' and assess_num.cno = '%s'"
    param_2 = (sno_a,cno)

    sql_3 = "select homework.title,homeworkcommit.content,homework.score from homework,homeworkcommit where homework.cno = homeworkcommit.cno and homework.hid = homeworkcommit.hid and homework.cno = '%s' and homework.hid = %s and homeworkcommit.sno = '%s'"
    param_3 = (cno,hid,sno)

    sql_4 = "select score,assess from assess where sno = '%s' and cno = '%s' and sno_a = '%s' and hid = %s"
    param_4 = (sno_a,cno,sno,hid)

    cursor.execute(sql_1%param_1)
    s1 = cursor.fetchone()

    cursor.execute(sql_2%param_2)
    s2 = cursor.fetchone()

    cursor.execute(sql_3%param_3)
    homework = cursor.fetchone()

    cursor.execute(sql_4%param_4)
    assess = cursor.fetchone()

    return render_template('teacher-handleAppeal.html',s1=s1,s2=s2,homework=homework,assess=assess)


# 教师修改学生互评权重
@app.route('/modifyW',methods=['GET','POST'])
def modifyW():

    sno = str(request.form.get('sno'))
    w = str(request.form.get('w'))

    inform = session.get("inform")

    cursor = db.cursor()

    sql = "update assess_num set w = %s where sno = '%s'"
    param = (w,sno)
    
    cursor.execute(sql%param)
    db.commit()

    path = "/handleAppeal/%s/%s/%s/%s"

    return redirect(path%inform)


# 教师提交申诉结果的结果
@app.route('/commitHandle',methods=['GET','POST'])
def commitHandle():

    score = str(request.form.get('score'))
    inform = str(request.form.get('inform'))

    informs = session.get("inform")

    cursor = db.cursor()

    sql_1 = "update appeal set statue = 'T',inform = '%s' where sno = '%s' and sno_a = '%s' and cno = '%s' and hid = %s"
    param_1 = (inform,informs[0],informs[1],informs[2],informs[3])
    
    sql_2 = "update homeworkcommit set score = %s where sno = '%s' and cno = '%s' and hid = %s"
    param_2 = (score,informs[0],informs[2],informs[3])

    cursor.execute(sql_1%param_1)
    cursor.execute(sql_2%param_2)
    db.commit()

    return redirect("/checkAppealList")


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
 


