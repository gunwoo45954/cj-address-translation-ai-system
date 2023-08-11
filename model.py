import re
import json

from jsonschema import validate, ValidationError
from langchain import PromptTemplate
from langchain.llms import OpenAI

def pre_processing(text):
    text = re.sub(r"(대한민국|Republic of Korea)"," ",text)

    text = re.sub(r"-(do|도)","-do ",text)
    text = re.sub(r"-(si|시)","-si ",text)
    text = re.sub(r"-(gu|구)","-gu ",text)
    text = re.sub(r"-(ro|로)","-ro ",text)
    
    text = re.sub(r"[\!\?@#$\^&*]",'',text)

    # 문앞 집앞
    text = re.sub(r'문\s*앞',' ',text)
    text = re.sub(r'집\s*앞',' ',text)
    text = re.sub(r'[Mm][Uu][Nmn]\s*[Aa][Pp]',' ',text)
    text = re.sub(r'[Jj][Ii][Pp]\s*[Aa][Pp]',' ',text)
    
    # 괄호 전처리 (삭제)
    s = re.search(r"\([^\)]+\)",text)
    if s:
        text = text[:s.span()[0]] + text[s.span()[1]:]
    
    
    # 지하 전처리
    text = re.sub("B1-","B",text)
    p = re.compile(r"(B\s?([0-9]{1,}|,)| B |([0-9]{1,}\s?|,)B)")
    s = p.search(text)
    if s:
        match = text[s.start():s.end()]
        match = re.sub(r"B"," 지하",match)
        if s.start() == 0:
            text = match + text[s.span()[1]:]
        else:
            text = text[:s.start()]+ match +text[s.end():]
    p = re.compile(r"(G/F\s?([0-9]{1,}|,)| G/F |([0-9]{1,}\s?|,)G/F)")
    s = p.search(text)
    
    if s:
        match = text[s.start():s.end()]
        match = re.sub(r"G/F"," 지하",match)
        if s.start() == 0:
            text = match + text[s.span()[1]:]
        else:
            text = text[:s.start()]+ match +text[s.end():]

    p = re.compile(r"(GF\s?([0-9]{1,}|,)| GF |([0-9]{1,}\s?|,)GF)")
    s = p.search(text)
    
    if s:
        match = text[s.start():s.end()]
        match = re.sub(r"GF"," 지하",match)
        if s.start() == 0:
            text = match + text[s.span()[1]:]
        else:
            text = text[:s.start()]+ match +text[s.end():]
            
    p = re.compile(r"(G\s?([0-9]{1,}|,)| G |([0-9]{1,}\s?|,)G)")
    s = p.search(text)
    
    if s:
        match = text[s.start():s.end()]
        match = re.sub(r"G"," 지하",match)
        if s.start() == 0:
            text = match + text[s.span()[1]:]
        else:
            text = text[:s.start()]+ match +text[s.end():]
    

    text = re.sub(r"\s+"," ",text).strip()            
    
    text = re.sub(' ,',",",text)
    text = re.sub(",$",' ',text)

    return text

def post_processing(text):
    text = re.sub(r'[bB]', '', text)
    
    # 수정 부분 : 서울특별시 관악구 관악로5길 33 -> "서울특별시 관악구 관악로5 처리되는 부분 수정
    text = re.sub(r',','',text)
    p = re.compile(r'[가-힣0-9]+(로|길)\s*([0-9]+번?\s*길)?\s*(지하)?\s*[0-9]+(-[0-9]+)?')
    
    s = p.search(text)
    if s is not None:
        text = text[:s.span()[1]]

    p2 = re.compile(r'(지하)?\s?[0-9]+') # (지하) #### 인 경우 잡기
    s2 = p2.match(text)
    
    if s2:
        text = "답 없음"
    
    return text

# Define the JSON Schema
result_schema = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
      "resultList": {
          "type": "array",
          "minItems": 1,
          "items": {
              "type": "object",
              "properties": {
                  "seq": {
                      "type": "integer",
                  },
                  "requestAddress": {
                      "type": "string"
                  },
              },
              "required": ["requestAddress","seq"]
          }
      }
  },
  "required": ["resultList"]
}

def validate_json(data, schema):
    # Validate the JSON against the schema
    state = True
    try:
        validate(instance=data, schema=schema)
        print("The JSON structure is valid.")
    except ValidationError as e:
        print(f"The JSON structure is not valid: {e}")
        state = False
    return state
  
def inference(input):
    template = """
    |Start of task|
    - You will work on translating a non-refined address in English into refined Korean. 
    - Unrestricted English addresses can only be made in English or mixed with Korean.
    - Output are in json, generate an json that adheres to the schema {output_schema} and the translation is carried out according to the Rule.

    |End of task|

    |Start of Rule|
    There are some rules when you translate.
    1. Addresses and requests may be mixed. The request may be in front of or behind the address. In the example below, "문 앞 배관실 넣어주세요" corresponds to the request. Delete requests.
    requestAddress : Incheon Tax Office, 75, Ugak-ro, Dong-gu, Incheon 문 앞 배관실 넣어주세요 -> requestAddress : 인천광역시 동구 우각로 75 (창영동)
    requestAddress : 배송전 전화주세요Jungbu Tax Office, 170, Toegye-ro, Jung-gu, Seoul -> requestAddress : 서울특별시 중구 퇴계로 170 (남학동)

    2. There may be a typo in the place name, as shown in the following example. SOUL is a typo of Seoul.
    requestAddress : B 101, Sejong-daero, Jung-gu, SOUL -> requestAddress : 서울특별시 중구 세종대로 지하101 (정동)

    3. Words translated into English, such as "South Mountain" and "Best-ro," may exist. This corresponds to "남산","으뜸로" respectively
    requestAddress : Gwangju Regional Joint Government Complex, 43, Advanced Science and Technology Road 208beon-gil, Buk-gu, Gwangju1001ho1001동 -> requestAddress : 광주광역시 북구 첨단과기로208번길 43 (오룡동)

    4. Do not translate detailed address information such as the unit/floor/apartment number. Delete detailed address information.
    requestAddress : Dongdaemun Police Station, 29, Yaknyeongsi-ro 21-gil, Dongdaemun-gu, Seoul문서수발실 -> requestAddress : 서울특별시 동대문구 약령시로21길 29 (청량리동)
    requestAddress : B1721, Nambu Ring-ro, Gwanak-gu, Seoul 김&장 -> requestAddress : 서울특별시 관악구 남부순환로 지하1721 (봉천동)
    requestAddress : 86, Yongdap-gil, Seongdong-gu, Seoul customs office 100% -> requestAddress : 서울특별시 성동구 용답길 86 (용답동)
    requestAddress : B 93, Wangsan-ro, Dongdaemun-gu, Seoul 1001ho1001동 -> requestAddress : 서울특별시 동대문구 왕산로 지하93 (제기동)


    |End of Rule|

    You don't have to print out the sample, just output answer.

    Input:
    {Address_Input}

    Output: 
    """

    # 전처리 추가
    data = dict()
    data["requestList"] = [{"seq":i["seq"],"requestAddress":pre_processing(i["requestAddress"])}for i in input["requestList"]]
    print("전처리 후 결과")
    print(data)
    state = False
    while(not state):
        prompt = PromptTemplate(
        input_variables=["Address_Input", "output_schema"],
        template=template,
        )
        prompt = prompt.format(Address_Input=data, output_schema=result_schema)   
        llm = OpenAI(model_name="gpt-3.5-turbo-16k")
        result = llm(prompt)
        
        result = re.sub(r'\n',' ',result)
        result = re.sub(r'\s+',' ',result)
        result = re.sub(r"\'",'\"',result)
        result = json.loads(result)
        
        state = validate_json(result, result_schema)
    print("chat gpt 실행 후 결과")
    print(result)
    temp = dict()
    temp["resultList"] = [{'seq': i["seq"], 'requestAddress' : post_processing(i["requestAddress"])} for i in result["resultList"]]
    print("후처리 이후 데이터")
    print(temp)
    return temp