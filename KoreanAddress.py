import pandas as pd
import requests
from bs4 import BeautifulSoup

def get_address(api_key, word):
    url = f'https://business.juso.go.kr/addrlink/addrLinkApi.do?currentPage=1&countPerPage%20=10&keyword={word}&confmKey={api_key}&hstryYn=Y&firstSort=road'

    response = requests.get(url)
    result = response.text
    soup = BeautifulSoup(result, 'xml')
    success = soup.find('totalCount').text
    data = []

    if int(success) > 0:                        # 검색 결과가 나오는 경우
        for item in soup.find_all('roadAddr'):
            data.append(item.text)
    else:                                       # 검색 결과가 나오지 않는 경우
        data.append("답 없음")

    return data[0]

api_key = 'devU01TX0FVVEgyMDIzMDcxMjE5MzIyMTExMzkyMjQ='
word = '대구 북구 췍로'

address = get_address(api_key, word)
print(address)