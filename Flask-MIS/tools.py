def distribute_assess(db,sno_a,cno,hid):
    cursor = db.cursor()
    sql_1 = "select sno,num from assess_num where cno = '%s' and sno != '%s'"
    param_1 = (cno,sno_a)

    cursor.execute(sql_1%param_1)
    students = cursor.fetchall()
    list_num = len(students)

    if list_num >= 3:
        snos = findMin3(students)
        for sno in snos:
            sql_2 = "insert into assess (sno,cno,sno_a,hid) values('%s','%s','%s',%s)"
            param_2 = (sno,cno,sno_a,hid)
            sql_3 = "update assess_num set num = num + 1 where sno = '%s' and cno = '%s'"
            param_3 = (sno,cno)
            cursor.execute(sql_2%param_2)
            cursor.execute(sql_3%param_3)
            db.commit()
        return True
    elif list_num < 3:
        return False
        
    

def findMin3(list):
    sorted_data = sorted(list, key=lambda x: x[1])
    return (sorted_data[0][0],sorted_data[1][0],sorted_data[2][0])
    