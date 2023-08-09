import re
import os
import json

import openai
from jsonschema import validate, ValidationError
from langchain import PromptTemplate
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI

def post_processing(text):
    text = re.sub(r'[bB]', '', text)
    p = re.compile(r'((로[^가-힣]\s*([0-9]{1,5}(번)?\s*길)?|길))?\s*(지하)?\s*[0-9]{1,5}(-[0-9]{1,5})?')
    s = p.search(text)
    print(s)
    if s is not None:
        text = text[:s.span()[1]]

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
              "required": ["resultList","seq"]
          }
      }
  },
  "required": ["requestList"]
}

def validate_json(data, schema):
    # Validate the JSON against the schema
    state = 0
    try:
        validate(instance=data, schema=schema)
        print("The JSON structure is valid.")
    except ValidationError as e:
        print(f"The JSON structure is not valid: {e}")
        state = 1
    return state
  
def inference(data):
    template = """
    |Start of task|
    - You will work on translating a non-refined address in English into refined Korean. 
    - Unrestricted English addresses can only be made in English or mixed with Korean.
    - Output are in json, generate an json that adheres to the schema {output_schema} and the translation is carried out according to the Rule.
    |End of task|

    |Start of Rule|
    There are some rules when you translate.
    1. If B, G/F, GF or G exists in the unstructured address, they mean underground. And change them to "지하" and get rid of them.
    requestAddress : 127, B, Seosomun-ro, Jung-gu, 새울 -> requestAddress : 서울특별시 중구 서소문로 지하127 (서소문동)
    requestAddress : GF160, Yanghwa-ro, 마포-gu, Seoul -> requestAddress : 서울특별시 마포구 양화로 지하160 (동교동)

    2. Addresses and requests may be mixed. In the example below, "문 앞 배관실 넣어주세요" corresponds to the request. This is purified except when it is purified
    requestAddress : Incheon Tax Office, 75, Ugak-ro, Dong-gu, Incheon 문 앞 배관실 넣어주세요 -> requestAddress : 인천광역시 동구 우각로 75 (창영동)
    requestAddress : 배송전 전화주세요Jungbu Tax Office, 170, Toegye-ro, Jung-gu, Seoul -> requestAddress : 서울특별시 중구 퇴계로 170 (남학동)

    3. There may be a typo in the place name, as shown in the following example. SOUL is a typo of Seoul.
    requestAddress : B 101, Sejong-daero, Jung-gu, SOUL -> requestAddress : 서울특별시 중구 세종대로 지하101 (정동)

    4. Words translated into English, such as "South Mountain" and "Best-ro," may exist. This corresponds to "남산","으뜸로" respectively
    requestAddress : Gwangju Regional Joint Government Complex, 43, Advanced Science and Technology Road 208beon-gil, Buk-gu, Gwangju1001ho1001동 -> requestAddress : 광주광역시 북구 첨단과기로208번길 43 (오룡동)

    5. Detailed locations such as document delivery room, front door, 1001 room, 1001 building are not translated.
    requestAddress : Dongdaemun Police Station, 29, Yaknyeongsi-ro 21-gil, Dongdaemun-gu, Seoul문서수발실 -> requestAddress : 서울특별시 동대문구 약령시로21길 29 (청량리동)
    requestAddress : B1721, Nambu Ring-ro, Gwanak-gu, Seoul 김&장 -> requestAddress : 서울특별시 관악구 남부순환로 지하1721 (봉천동)
    requestAddress : 86, Yongdap-gil, Seongdong-gu, Seoul customs office 100% -> requestAddress : 서울특별시 성동구 용답길 86 (용답동)

    |End of Rule|

    You don't have to print out the sample, just output answer.

    Input:
    {Address_Input}

    Output: 
    """
    
    prompt = PromptTemplate(
    input_variables=["Address_Input", "output_schema"],
    template=template,
    )
    prompt = prompt.format(Address_Input=data, output_schema=result_schema)   
    llm = OpenAI(model_name="gpt-3.5-turbo")
    result = llm(prompt)

    result = re.sub(r'\n',' ',result)
    result = re.sub(r'\s+',' ',result)
    result = re.sub(r"\'",'\"',result)
    print(result)
    result = json.loads(result)
    temp = dict()
    temp["resultList"] = [{'seq': i["seq"], 'requestAddress' : post_processing(i["requestAddress"])} for i in result["resultList"]]
    print(temp)
    return temp