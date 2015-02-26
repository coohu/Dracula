import urllib.request,urllib.parse,time,re,os,csv
from html.parser import HTMLParser
import mysql.connector
from mysql.connector import errorcode
# MySQL Connector/Python
#http://huataimogang.1688.com/page/offerlist.htm
#showType=windows&tradenumFilter=false&sampleFilter=false&mixFilter=false&privateFilter=false&groupFilter=false&sortType=tradenumdown&pageNum=2#search-bar
class db():
    def __init__(self):
        self.config = {
          'user': 'root',
          'password': 'v',
          'host': '127.0.0.1',
          'database': 'ali',
          'raise_on_warnings': True,
        }
        self.products =(
            '''CREATE TABLE IF NOT EXISTS `products`(
              `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
              `companyid` varchar(50) COLLATE utf8_bin NOT NULL,
              `catalog` varchar(255) COLLATE utf8_bin,
              `product` varchar(60) COLLATE utf8_bin NOT NULL,
              `urlid` bigint(20) unsigned NOT NULL unique,
              KEY `id` (`id`)
            )ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;''')
        try:
            self.cnx = mysql.connector.connect(**self.config)
            self.cu = self.cnx.cursor()
            
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exists")
            else:
                print(err)
    def sqlEscap(self,istr):
        ostr=istr.replace("'","").replace("#","").replace("\\","")
        return ostr
    def tb(self):
        self.cu.execute(self.products)
    def ok(self):
        self.cnx.commit()
        self.cnx.close()
    def feed(self,conpanyid,catalog,product,urlid):
        conpanyid=self.sqlEscap(conpanyid)
        catalog=self.sqlEscap(catalog)
        product=self.sqlEscap(product)
        add_company = ('''INSERT INTO `ali`.`products` (`companyid`,`catalog`,`product`,`urlid`) VALUES ('%s','%s','%s',%d);''')
        self.cu.execute(add_company%(conpanyid,catalog,product,urlid))
        self.cnx.commit()
        
    def feedPro(self,conpanyid,product,urlid):
        conpanyid=self.sqlEscap(conpanyid)
        product=self.sqlEscap(product)
        add_company = ('''INSERT INTO `ali`.`products` (`companyid`,`product`,`urlid`) VALUES ('%s','%s',%d);''')
        self.cu.execute(add_company%(conpanyid,product,urlid))
        self.cnx.commit()

    def updataCa(self,catalog,urlid):
        catalog=self.sqlEscap(catalog)
        olds='''select catalog from `ali`.`products` where urlid=%d'''
        sql = ("update ali.products set catalog='%s' where urlid=%d;")
        self.cu.execute(olds%urlid)
        d=self.cu.fetchone()
        d=d[0].decode('utf8')+"[&]"+catalog
        self.cu.execute(sql%(d,urlid))
        self.cnx.commit()

class getCa(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.flag = 0
        self.rt={}
    def handle_starttag(self, tag, attrs):
        if tag =="div":
            for n,v in attrs:
                if n=="class" and v=='wp-category-nav-unit':
                    self.flag = 1
        if tag =="a" and self.flag == 1:
            ca=url=""
            for n,v in attrs:
                if n=="title":
                    ca=v
                if n=="href":
                    url=v
            self.rt[ca]=url
    def handle_endtag(self,tag):
        if tag == "div" and self.flag==1:
            self.flag=0
    def handle_data(self,data):
        pass
    def ret(self):
        return self.rt
class getPro(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.flag = 0
        self.rt={}
        self.pgc=0
    def handle_starttag(self, tag, attrs):
        if tag =="li":
            for n,v in attrs:
                if n=="data-prop":
                    self.flag = 1
        if tag =="div" and self.flag == 1:
            self.flag=2
        if tag =="a" and self.flag==2:
            ca=url=""
            for n,v in attrs:
                if n=="title":
                    ca=v
                if n=="href":
                    url=v
            self.rt[ca]=url
            self.flag = 0;
        if tag=="em":
            for n,v in attrs:
                if n=="class" and v=="page-count":
                        self.flag = 3
    def handle_data(self,data):
        if self.flag==3:
            self.pgc=data
            self.flag=0
    def ret(self):
        return self.rt
class getDtl(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.flag = 0
        self.rt=[]
    def handle_starttag(self, tag, attrs):
        if tag =="li":
            for n,v in attrs:
                if n=="class" and v[0:11]=="tab-trigger":
                    self.flag = 1
                if n=="data-imgs" and self.flag == 1:
                    url=v.split("original")[1]
                    self.rt.append(url[3:len(url)-2])
                    self.flag = 0
    def ret(self):
        return self.rt
def fltIllegal(fstr):
    rets=fstr.replace("*","×").replace("/","").replace("\\","").replace(":","").replace("<","").replace(">","").replace("|","").replace("?","")
    return rets
url="http://%s.1688.com/page/offerlist.htm"
cs='GBK'      
def suckCa(cid):
    global url
    count = 0
    root=os.getcwd()+"\\"+cid
    pg=urllib.request.urlopen(url%(cid)).read().decode(cs,"ignore")
    ca = getCa()
    ca.feed(pg)
    #for(a,b) in ca.ret().items():
        #print(a)
    for (k,v) in ca.ret().items():
        swd=root+"\\"+fltIllegal(k)
        os.makedirs(swd,exist_ok=True)
        pg=urllib.request.urlopen(v).read().decode(cs,"ignore")
        pro=getPro()
        pro.feed(pg)
        plist=pro.ret()
        if int(pro.pgc)>0:
            for j in range(2,int(pro.pgc)+1):
                p='''?showType=windows&tradenumFilter=false&sampleFilter=false&mixFilter=false&privateFilter=false&groupFilter=false&sortType=tradenumdown&pageNum=%s#search-bar'''%j
                pg=urllib.request.urlopen(v+p).read().decode(cs,"ignore")
                pro=getPro()
                pro.feed(pg)
                plist.update(pro.ret())
        #for(a,b) in plist.items():
            #print(a)
        for (i,j) in plist.items():
            twd=swd+"\\"+fltIllegal(i)
            os.makedirs(twd,exist_ok=True)
            pg=urllib.request.urlopen(j).read().decode(cs,"ignore")
            dtl=getDtl()
            dtl.feed(pg)
            x=0
            for y in dtl.ret():
                f=twd+"\\"+str(x)+".jpg"
                img=urllib.request.urlopen(y).read()
                fp=open(f,"wb")
                fp.write(img)
                fp.close()
                x=x+1
            try:
                data.feed(cid,k,i,int(j.split("/")[4].split(".")[0]))
            except mysql.connector.errors.IntegrityError as e:
                print('数据库已经存在此产品。',e)
            count=count+1
            print(cid,k,i,j.split("/")[4].split(".")[0])
                
    print("从：%s 下载 %d 个产品信息。"%(cid,count))
def suckPro(cid):
    global url
    count = 0
    root=os.getcwd()+"\\"+cid
    pg=urllib.request.urlopen(url%(cid)).read().decode(cs,"ignore")
    pro=getPro()
    pro.feed(pg)
    plist=pro.ret()
    if int(pro.pgc)>0:
        for j in range(2,int(pro.pgc)+1):
            p='''?showType=windows&tradenumFilter=false&sampleFilter=false&mixFilter=false&privateFilter=false&groupFilter=false&sortType=tradenumdown&pageNum=%s#search-bar'''%j
            pg=urllib.request.urlopen(url%(cid)+p).read().decode(cs,"ignore")
            pro=getPro()
            pro.feed(pg)
            plist.update(pro.ret())
    for (i,j) in plist.items():
        cwd=root+"\\"+fltIllegal(i)
        os.makedirs(cwd,exist_ok=True)
        pg=urllib.request.urlopen(j).read().decode(cs,"ignore")
        dtl=getDtl()
        dtl.feed(pg)
        x=0
        for y in dtl.ret():
            f=(cwd+"\\"+str(x)+".jpg")
            img=urllib.request.urlopen(y).read()
            fp=open(f,"wb")
            fp.write(img)
            fp.close()
            x=x+1
        try:
            data.feedPro(cid,i,int(j.split("/")[4].split(".")[0]))
        except mysql.connector.errors.IntegrityError as e:
                print('数据库已经存在此产品。',e)
        count=count+1
        print(i,j.split("/")[4].split(".")[0])       
    print("从：%s 下载 %d 个产品信息。"%(cid,count))  
    
def suck2db(cid):
    global url
    count = 0
    pg=urllib.request.urlopen(url%(cid)).read().decode(cs,"ignore")
    ca = getCa()
    ca.feed(pg)
    for (k,v) in ca.ret().items():
        pg=urllib.request.urlopen(v).read().decode(cs,"ignore")
        pro=getPro()
        pro.feed(pg)
        plist=pro.ret()
        if int(pro.pgc)>0:
            for j in range(2,int(pro.pgc)+1):
                p='''?showType=windows&tradenumFilter=false&sampleFilter=false&mixFilter=false&privateFilter=false&groupFilter=false&sortType=tradenumdown&pageNum=%s#search-bar'''%j
                pg=urllib.request.urlopen(v+p).read().decode(cs,"ignore")
                pro=getPro()
                pro.feed(pg)
                plist.update(pro.ret())
        for (i,j) in plist.items():
            try:
                data.feed(cid,k,i,int(j.split("/")[4].split(".")[0]))
                count=count+1
            except mysql.connector.errors.IntegrityError:
                data.updataCa(k,int(j.split("/")[4].split(".")[0]))
            print(cid,k,i,j.split("/")[4].split(".")[0])
    print("从：%s 下载 %d 个产品信息。"%(cid,count))
 

def suck2csv(cid):
    global url
    count = 0
    root=os.getcwd()+"\\"+cid
    os.makedirs(root,exist_ok=True)
    csvfile=open(root+'\\'+cid+'.csv', 'a+', newline='')
    cr = csv.writer(csvfile, delimiter=' ',quotechar=',', quoting=csv.QUOTE_MINIMAL)
    pg=urllib.request.urlopen(url%(cid)).read().decode(cs,"ignore")
    ca = getCa()
    ca.feed(pg)
    for (k,v) in ca.ret().items():
        pg=urllib.request.urlopen(v).read().decode(cs,"ignore")
        pro=getPro()
        pro.feed(pg)
        plist=pro.ret()
        if int(pro.pgc)>0:
            for j in range(2,int(pro.pgc)+1):
                p='''?showType=windows&tradenumFilter=false&sampleFilter=false&mixFilter=false&privateFilter=false&groupFilter=false&sortType=tradenumdown&pageNum=%s#search-bar'''%j
                pg=urllib.request.urlopen(v+p).read().decode(cs,"ignore")
                pro=getPro()
                pro.feed(pg)
                plist.update(pro.ret())
        for (i,j) in plist.items():
            cr.writerow([cid,k,i,j.split("/")[4].split(".")[0]])
            print(cid,k,i,j.split("/")[4].split(".")[0])
            count=count+1
    csvfile.close()
    print("从：%s 下载 %d 个产品信息。"%(cid,count))  
data=''
def setupDB():    
    global data
    data=db()
    try:
        data.tb()  
    except mysql.connector.errors.DatabaseError as e:
        print(e)

opt=input('''输入数字选择操作：\n
\t1：分类下载商品。
\t2：只下载商品。
\t3：导入数据库。
\t4：导入表格。\n\t''') 

if opt=='1':
    setupDB()
    keywords=input('''输入账号ID：''')
    suckCa(keywords)
    data.ok()
elif opt=='2':
    setupDB()
    keywords=input('''输入账号ID：''')
    suckPro(keywords)
    data.ok()
elif opt=='3':
    setupDB()
    keywords=input('''输入账号ID：''')
    suck2db(keywords)
    data.ok()
elif opt=='4':
    keywords=input('''输入账号ID：''')
    suck2csv(keywords)
    








