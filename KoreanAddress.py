import re
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
    if (len(data) > 1):

        # data[1]에서 ()를 없앤 문자열이매칭되는지 검색 -> 매칭되면 data[0] 사용 아니라면 답 없음
        
        # 되는 경우
        # data[0] = 서울특별시 서대문구 통일로 81 (미근동) 
        # data[1] = 서울특별시 서대문구 통일로 83-1 (미근동) 인경우
        # 서울특별시 서대문구 통일로 81
        
        # 안되는 경우
        # data[0] = 서울특별시 서대문구 통일로 81 (미근동) 
        # data[1] = 서울특별시 서대문구 통일로 87 (미근동) 인경우
        # 서울특별시 서대문구 통일로 81가 매칭되지 않음 -> 답없음
        
        temp = re.sub(r'\([가-힣]+\)','',data[0]).strip()
        m = re.match(temp,data[1])
        if m is None:
            data = ["답 없음"]
    return data[0]