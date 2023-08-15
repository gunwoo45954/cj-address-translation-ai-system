import re
from jsonschema import validate, ValidationError


def pre_processing(text):
    
    # ',' -> ' '
    text = re.sub(r',',' ',text)
    # text = re.sub(r'100%','',text)
    text = re.sub(r"(대한민국|Republic of Korea)"," ",text)

    text = re.sub(r"-(do|도)","-do ",text)
    text = re.sub(r"-(si|시)","-si ",text)
    text = re.sub(r"-(gu|구)","-gu ",text)
    text = re.sub(r"-(ro|로)","-ro ",text)
    
    text = re.sub(r"[\!\?@#$\^&*]",' ',text)

    # 문앞 집앞
    text = re.sub(r'문\s*앞',' ',text)
    text = re.sub(r'집\s*앞',' ',text)
    text = re.sub(r'[Mm][Uu][Nmn]\s*[Aa][Pp]',' ',text)
    text = re.sub(r'[Jj][Ii][Pp]\s*[Aa][Pp]',' ',text)
    
    # 괄호 전처리 (삭제)
    s = re.search(r"\([^\)]+\)",text)
    if s:
        text = text[:s.span()[0]] + text[s.span()[1]:]
    
    # # 지하 전처리
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

    return text

def post_processing(text):
    text = re.sub(r'[bB]', ' 지하 ', text)
    
    # 수정 부분 : 서울특별시 관악구 관악로5길 33 -> "서울특별시 관악구 관악로5 처리되는 부분 수정
    text = re.sub(r',','',text)
    p = re.compile(r'([가-힣0-9]+(로|길)\s*([0-9]+번?\s*(길|가)\s*)?)?(지하)?\s*[0-9]+(-[0-9]+)?(가|번?길|로)?\s?(지하)?')
    s = p.search(text)
    
    if s is not None:
        text = text[:s.span()[1]]

    p2 = re.compile(r'(지하)?\s?[0-9]+') # (지하) #### 인 경우 잡기
    s2 = p2.match(text)
    
    if s2:
        if text[s2.start():s2.end()] == text.strip():
            text = "답 없음"
    
    # 을지로1가 -> 을지로 1가
    p3 = re.compile(r'[0-9]+가')
    s3 = p3.search(text)
    if s3:
        match = text[s3.start():s3.end()]
        text = re.sub(match," "+match,text)
    
    text = re.sub(r"\s+"," ",text).strip()
    
    return text

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