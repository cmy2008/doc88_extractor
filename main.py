print("DOC88 （预览）文档提取工具")
print("by: Cuite_Piglin")

import json
import os
import requests
import compressor
import re
from decode import decode
from decode import get_url

# m_main.init
def get_str(url):
    proxies = { "http": None, "https": None}
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.39", 'Content-Type': "application/x-www-form-urlencoded"}
    request = requests.get(url, headers = headers, proxies = proxies)
    a = str(request.text)
    b=re.search( r'm_main.init\(\".*\"\);', a)
    c=b.span()
    return a[c[0]+13:c[1]-3]

encoded_str = get_str(input('请输入网址：'))
config = json.loads(decode(encoded_str))
# print(decode(encoded_str))
# print(decode(config['pageInfo']))
page=1
url=get_url(config['p_code'],config['headerInfo'],page,config['p_swf'],config['pageInfo'],config['ebt_host'])
print("文档名：" + config['p_name'])
print("上传日期：" + config['p_upload_date'])
print("PK = " + url[0])
print("PH = " + url[1])

dir_path = 'docs/' + config['p_name'] + '/' 
file_path = dir_path + url[0][25:]
response = requests.get(url[0])
try:
    os.makedirs(dir_path)
except:
    print("")
print("Downloading BT...")
with open(file_path, "wb") as f:
    f.write(response.content)

for i in range(1,config['pageCount']+1):
    print("Downloading page " + str(i) + '...')
    url=get_url(config['p_code'],config['headerInfo'],i,config['p_swf'],config['pageInfo'],config['ebt_host'])
    file_path = dir_path  + url[1][25:]
    print(url[1])
    response = requests.get(url[1])
    with open(file_path, "wb") as f:
        f.write(response.content)
    compressor.make(dir_path + url[0][25:],dir_path + url[1][25:],dir_path + str(i) + '.swf')
