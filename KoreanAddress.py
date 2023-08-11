import pandas as pd
import requests
from bs4 import BeautifulSoup

def get_address(api_key, word):
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
    if (len(data) > 1) and (data[0] != data[1]):
        index = data[0].find("(")
        if (word == data[0]) or (word == data[0][:index-1]):    # 검색어가 ()안에 있는 문자를 삭제했을 때와 동일하거나, 삭제하지 않았을 때와 동일하거나
            pass
        else:
            data = ["답 없음"]

    return data[0]