import requests
from bs4 import BeautifulSoup
import re

def get_address(api_key, word):
    if word =="답 없음":
        return "답 없음"
    url = f'https://business.juso.go.kr/addrlink/addrLinkApi.do?currentPage=1&countPerPage%20=10&keyword={word}&confmKey={api_key}&hstryYn=Y&firstSort=road'

    response = requests.get(url, timeout=60)
    result = response.text
    soup = BeautifulSoup(result, 'xml')
    success = soup.find('totalCount').text
    data = []

    if int(success) > 0:                        # 검색 결과가 나오는 경우
        for item in soup.find_all('roadAddr'):
            data.append(item.text)
    else:                                       # 검색 결과가 나오지 않는 경우
        data.append("답 없음")

    # 결과는 여러 개가 나오는데 도로명주소는 모두 동일한 경우.
    # 결과는 여러 개가 나오는데 검색어와 1번째 결과가 일치하는 경우. 나머지 결과들은 다름.
    # 문제점 : 검색어와 1번째 결과가 조금 달라서 "답 없음"처리가 되는 경우. 이 경우에는 1번째 결과가 정답인 경우임.
    if (len(data) > 1):
        address_1 = re.sub('\([^\)]+\)','',data[0]).strip()
        address_2 = re.sub('\([^\)]+\)','',data[1]).strip()
        
        if address_1.split()[-2] not in address_2.split()[-2]:
            data = ["답 없음"]
        elif address_1.split()[-1] not in address_2.split()[-1]:
            data = ["답 없음"]
    return data[0]