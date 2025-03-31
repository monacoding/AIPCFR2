import os
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일에서 환경변수 불러오기
load_dotenv()

# 최신 OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_response(inquiry, company, name, item_no):
    try:
        system_prompt = "당신은 배를 만드는 엔지니어입니다. 선주 문의에 대해 전문적이고 친절한 회신을 작성하세요."

        user_prompt = (
            f"항목 번호: {item_no}\n"
            f"회사: {company}\n"
            f"담당자: {name}\n"
            f"문의: {inquiry}\n"
            f"\n회신:"
        )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"회신 생성 중 오류 발생: {str(e)}"
