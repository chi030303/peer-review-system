
# 算本次作业互评得分
# a,b,c为三个评分
# 输入数据在规定区间就返回均值，否则报错
def meanScore(a,b,c):
    if(a >= 0 and a<=10 and b>=0 and b<=10 and c>=0 and c<=10):
        return a+b+c/3
    else:
        return -1

# sno和cno作为主键
# 每个cno下hid对应一个作业
# 进入到一个cno下的hid后按照sno分配
# 分配到自己以外的人的作业
# 添加一个计数器，确保每个作业不会被分到三次以上
def distribute(snoList):
    n = len(snoList)
    dis_count = [0] * n
    result = []
    j = 0
    dis_sno = []
    # 当有人的作业分配次数不够3次时，继续分配
    while any(count < 3 for count in dis_count):
        for index,sno in enumerate(reversed(snoList)):
            if len(dis_sno) < 3:
                if sno not in dis_sno and dis_count[n - index - 1] < 3 and sno != snoList[j]:
                    dis_sno.append(sno)
                    dis_count[n - index - 1] += 1
            else:
                result.append(dis_sno.copy())
                j += 1
                dis_sno.clear()
    return(result)

snoList = ["21301151","21301152","21301153","21301154","21301155","21301156","21301157","21301158","21301159","21301160"]
distribute(snoList) 
print(snoList)