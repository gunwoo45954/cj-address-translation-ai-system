from fastapi import FastAPI
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import uvicorn
from KoreanAddress import get_address
import numpy as np
import logging
from omegaconf import OmegaConf
from model import validate_json,inference, request_schema

import os
import argparse
import openai

# 해야 할 일_0806
# 1. Chat gpt를 사용해 영문 주소 -> 한글 주소로 변환 구현.
# 2. request에선 seq이 int, response에선 seq이 char인데, 예시를 보면 request에서도 char를 쓰는게 좋아보임.
# 3. API URL로 배포. heroku 사용 예정.
# 4. CJ에서 지급한 데이터를 json형식으로 모두 변환하여 테스트. 지연 시간도 확인.


# Argument
parser = argparse.ArgumentParser()
parser.add_argument('--config','-c', type=str, default='')
args, _ = parser.parse_known_args()

conf = OmegaConf.load(f'./config/{args.config}.yaml')

# 도로명주소 api_key 값
api_key = conf.api
chatapi_key = conf.chatgpt


os.environ["OPENAI_API_KEY"] = chatapi_key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Response JSON 형식
    # HEADER : 응답 성공/실패 여부(Array)
    # resultCode : S / F (CHAR)
    # resultMessage : Success, Fail Message (CHAR)
    # BODY : 번역 결과 반환 List (List)
    # resultList/seq : 고유 seq 번호(CHAR)
    # resultList/resultAddres : 번역 한글주소

# Request JSON 형식
class RequestItem(BaseModel):
    seq : int = Field(gt = 0, le = 99999999)
    requestAddress : str = Field(...)

class Request(BaseModel):
    requestList: List[RequestItem] = Field(...)

# Response JSON 형식
class HeaderItem(BaseModel):
    RESULT_CODE : str = "S"
    RESULT_MSG : str = "Success"

class BodyItem(BaseModel):
    seq : str
    resultAddress : str

class Response(BaseModel):
    HEADER : HeaderItem
    BODY : Optional[List[BodyItem]] = None      

class Response_fail(BaseModel):
    HEADER : HeaderItem
        
app = FastAPI()

# 경로는 /, 동작은 get, 함수는 데코레이터 아래에 있는 함수가 동작함.
# async def 대신 일반 함수를 사용해 정의할 수도 있음.
# 응용 프로그램이 다른 프로그램과 통신하지 않고 응답할 때까지 기다릴 필요가 없는 경우 async def
# fastapi에서는 일반 함수를 사용해도 비동기 처리 되도록 구현되어 있음.

# response_model를 통해 다음과 같은 기능을 수행
# 출력 데이터를 모델로 제한하며 해당 타입 선언으로 변환
# 데이터를 검증
# 응답을 위한 JSON 스키마를 OpenAPI path operation에 더함
# 자동 문서화 시스템에 사용

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.info(f"Request received: {request.method} - {request.url}")
    response = await call_next(request)
    return response

def chunk_list(lst, chunk_size):
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]



@app.post('/result/')
def create_response(item : Request):
    # 이 함수는 다음과 같은 기능을 수행
    # 1. 도로명주소 검증 API를 사용해 주소 존재 여부를 확인
    # 2. response 반환
    response = Response(HEADER=HeaderItem())
    request_list = item.requestList
    
    chunk_size = 10
    input_data =  [{'seq': i.seq, 'requestAddress': i.requestAddress} for i in request_list]
    data_chunk = chunk_list(input_data, chunk_size)
    data_chunk = [{"requestList":i} for i in data_chunk]
    
    result_list = []
    for idx,chunk in enumerate(data_chunk):
        if validate_json(chunk,request_schema):
            check_address = 0
            response.HEADER.RESULT_CODE = "F"
            response.HEADER.RESULT_MSG = f"seq {request_list[i].seq} is failed to transfer"
            response2 = Response_fail(HEADER=HeaderItem())
            response2.HEADER.RESULT_CODE = response.HEADER.RESULT_CODE
            response2.HEADER.RESULT_MSG = response.HEADER.RESULT_MSG
            return response2

        result_list += inference(chunk)["resultList"]
    
    for i in result_list:
        i['seq'] = int(i['seq'])
    print(result_list)
    
    result_dict = {"requestList":result_list}
    request_list = result_dict
    check_address = 1
    body_items = []

    for i in range(len(request_list)):
        body_item = BodyItem(seq="some_value", resultAddress="some_address")
        
        
        ## TODO: 받는 형식 확인
        
        ### 
        result_address = get_address(api_key, request_list[i].requestAddress)
        if result_address == "답 없음":
            check_address = 0
            response.HEADER.RESULT_CODE = "F"
            response.HEADER.RESULT_MSG = f"seq {request_list[i].seq} is failed to transfer"
            break
        
        body_item.seq = str(request_list[i].seq)
        body_item.resultAddress = result_address
        body_items.append(body_item)
    
    if check_address:
        response.BODY = body_items
    else:
        response2 = Response_fail(HEADER=HeaderItem())
        response2.HEADER.RESULT_CODE = response.HEADER.RESULT_CODE
        response2.HEADER.RESULT_MSG = response.HEADER.RESULT_MSG
        return response2

    return response

if __name__ == "__main__":
    uvicorn.run("fastapi_test:app")