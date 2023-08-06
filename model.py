import re
import os
import json

import openai
from jsonschema import validate, ValidationError
from langchain import PromptTemplate
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI




def data_preprocessing(s:str):
    s = re.sub('(Republic of Korea)|(Korea)|(대한민국)|(한국)', ' ',s)
    s = re.sub(',\S','', s)
    s = re.sub(r'문\s*앞','',s)
    s = re.sub(r'집\s*앞','',s)
    s = re.sub(r'MUN\s*AP','',s)
    s = re.sub(r'MUN\s*AP','',s)
    s = re.sub(r'B',' B',s)
    
    
    s = re.sub(r'직접\s*수령','',s)
    s = re.sub(r'\s+',' ',s).strip()
    return s


# Define the JSON Schema
request_schema = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
      "requestList": {
          "type": "array",
          "minItems": 1,
          "items": {
              "type": "object",
              "properties": {
                  "requestAddress": {
                      "type": "string"
                  },
                  "seq": {
                      "type": "integer",
                  },
              },
              "required": ["requestAddress","seq"]
          }
      }
  },
  "required": ["requestList"]
}

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
                      "type": "string",
                  },
                  "resultAddress": {
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
    - Input and Output are in json, give input in the form of a {input_schema} generate an json that adheres to the schema {output_schema} and the translation is carried out according to the Rule.
    - You don't have to print out the sample, just output json.
    |End of task|

    |Start of Rule|
    There are some rules when you translate.
    1. If you don't translate words related to Korea, such as Republic of Korea.
    requestAddress : B12 Dasan-ro Jung-gu Seoul (Sindang-dong)Republic of Korea  
    -> resultAddress : 서울특별시 중구 다산로 지하122 (신당동)

    2. If B exists in the unstructured address, it means underground. And change B to underground and get rid of B.
    requestAddress1 : 127, B, Seosomun-ro, Jung-gu, 새울 -> resultAddress1 : 서울특별시 중구 서소문로 지하127 (서소문동)
    requestAddress2 : B102 Dosan-daero Seoul (Sinsa-dong)Republic of Korea -> resultAddress2 : 서울특별시 강남구 도산대로 지하102 (신사동)

    3. Addresses and requests may be mixed. In the example below, "문 앞 배관실 넣어주세요" corresponds to the request. This is purified except when it is purified
    requestAddress : Incheon Tax Office, 75, Ugak-ro, Dong-gu, Incheon 문 앞 배관실 넣어주세요 -> resultAddress : 인천광역시 동구 우각로 75 (창영동)

    4. There may be a typo in the place name, as shown in the following example. SOUL is a typo of Seoul.
    requestAddress : B 101, Sejong-daero, Jung-gu, SOUL -> resultAddress : 서울특별시 중구 세종대로 지하101 (정동)

    5. Detailed locations such as document delivery room, front door, 1001 room, 1001 building are not translated.
    requestAddress : Dongdaemun Police Station, 29, Yaknyeongsi-ro 21-gil, Dongdaemun-gu, Seoul문서수발실 -> resultAddress : 서울특별시 동대문구 약령시로21길 29 (청량리동)

    6. Words translated into English, such as "South Mountain" and "Best-ro," may exist. This corresponds to "남산","으뜸로" respectively
    requestAddress1 : Cheongju Customs Chungju Support Center on the 3rd floor of the Chungju Chamber of Commerce and Industry, 31, Best-ro, Chungju-si, Chungcheongbuk-do, 대한민국 -> resultAddress1 : 충청북도 충주시 으뜸로 31 (금릉동)
    requestAddress2 : Gwangju Regional Joint Government Complex, 43, Advanced Science and Technology Road 208beon-gil, Buk-gu, Gwangju1001ho1001동 -> resultAddress2 : 광주광역시 북구 첨단과기로208번길 43 (오룡동)

    7. There may be an address translated into Korean and an address in English together. If that's the case, please translate one of the two. In the example below, we can see that B1-46 and 지하46 are the same
    requestAddress : 서울특별시 서초구 잠원로4길 지하46B1-46, Jamwon-ro 4-gil, Seocho-gu -> resultAddress : 서울특별시 서초구 잠원로4길 지하46
    |End of Rule|


    |Start of Example|
    "seq:3" "11, Sinmok-ro 2-gil, Yangcheon-gu, Seoul, Republic of Korea" -> "seq:3" "resultAddress": "resultAddress"": ""서울 양천구 신목로2길 11"
    "seq:1" "requestAddress:Sinmok-ro 2-gil, Yangcheon-gu, Seoul, Republic of Korea" -> "seq:1" "resultAddress": "서울 양천구 신목로2길 12"

    |End of Example|


    You don't have to print out the sample, just output Dict .

    Input:
    {Address_Input}

    Output: 
    """
    
    prompt = PromptTemplate(
    input_variables=["Address_Input", "input_schema", "output_schema"],
    template=template,
    )
    prompt = prompt.format(Address_Input=data, input_schema=request_schema, output_schema=result_schema)   
    llm = OpenAI(model_name="gpt-3.5-turbo")
    result = llm(prompt)
    result = re.sub(r'\n',' ',result)
    result = re.sub(r'\s+',' ',result)
    result = re.sub(r"\'",'\"',result)
    
    result = json.loads(result)
    return result