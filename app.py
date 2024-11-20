from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from datetime import datetime, timedelta
import openai
from dotenv import load_dotenv
import os
from openai import AzureOpenAI

load_dotenv()

app = Flask(__name__)

# Azure OpenAI 클라이언트 설정
client = AzureOpenAI(
    api_key=os.getenv('AZURE_OPENAI_KEY'),  
    api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
)

# 예시 감정 데이터를 사용자별로 구성
emotions_data = {
    "jibin": {
        '2024-11-01': {
            'mainEmotion': 'SAD',
            'emotions': {
                'HAPPY': 0.1,
                'SAD': 0.7,
                'NEUTRAL': 0.1,
                'CALM': 0.05,
                'ANGRY': 0.05
            },
            'content': '내일 있을 발표 때문에 긴장된다. 자료는 다 준비했지만 실수하지 않았으면 좋겠다. 오늘은 발표 연습만 계속했다.'
        },
        '2024-11-02': {
            'mainEmotion': 'ANGRY',
            'emotions': {
                'HAPPY': 0.05,
                'SAD': 0.05,
                'CALM': 0.1,
                'JOY': 0.05,
                'ANGRY': 0.7
            },
            'content': '요즘 계속되는 야근으로 체력이 바닥이다. 주말에는 푹 쉬면서 재충전을 해야겠다. 커피만 마시면서 버티는 중.'
        },
        '2024-11-03': {
            'mainEmotion': 'HAPPY',
            'emotions': {
                'HAPPY': 0.6,
                'SAD': 0.1,
                'CALM': 0.1,
                'JOY': 0.1,
                'ANGRY': 0.1
            },
            'content': '오랜만에 가족들과 맛있는 저녁을 먹었다. 엄마가 해주신 김치찌개가 정말 그리웠다. 든든한 하루였다.'
        },
        '2024-11-04': {
            'mainEmotion': 'SAD',
            'emotions': {
                'HAPPY': 0.05,
                'SAD': 0.7,
                'CALM': 0.05,
                'JOY': 0.05,
                'ANGRY': 0.05
            },
            'content': '휴일인데 혼자 있으니 쓸쓸하다. SNS를 보니 다들 즐거워보여서 더 외로워진다. 내일은 친구들한테 연락해봐야겠다.'
        }
    },
    "hosik": {
        '2024-11-01': {
            'emotion': 'CALM',
            'content': '아침 일찍 일어나 운동을 했다. 상쾌한 하루의 시작이었다.'
        },
        '2024-11-02': {
            'emotion': 'JOY',
            'content': '새로운 프로젝트를 시작했다. 팀원들도 좋고 신이 난다.'
        }
    },
    "minchae": {
        '2024-11-01': {
            'emotion': 'CALM',
            'content': '아침 일찍 일어나 운동을 했다. 상쾌한 하루의 시작이었다.'
        },
        '2024-11-02': {
            'emotion': 'JOY',
            'content': '새로운 프로젝트를 시작했다. 팀원들도 좋고 신이 난다.'
        }
    }
    # 다른 사용자들의 데이터도 비슷한 형식으로 추가
}

# 사용자 데이터 (실제 서비스에서는 데이터베이스를 사용해야 합니다)
users = {
    "jibin": {
        "password": "1234",
        "name": "황지빈"
    },
    "hosik": {
        "password": "5678",
        "name": "황호식"
    },
    "minchae": {
        "password": "9012",
        "name": "김민채"
    },
    "beejin": {
        "password": "3456",
        "name": "손비진"
    }
}

# 로그인 라우트 추가
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users and users[username]["password"] == password:
            session['logged_in'] = True
            session['username'] = username
            session['name'] = users[username]["name"]
            return redirect(url_for('index'))
        else:
            return "아이디 또는 비밀번호가 잘못되었습니다."
            
    return render_template('login.html')

# 로그아웃 기능 추가
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# 기존 라우트들에 로그인 체크 추가
@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    username = session.get('username')
    user_emotions = emotions_data.get(username, {})  # 해당 사용자의 감정 데이터만 가져오기
    return render_template('index.html', emotions=user_emotions)

@app.route('/get_diary', methods=['GET'])
def get_diary():
    if not session.get('logged_in'):
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    username = session.get('username')
    date = request.args.get('date')
    
    if username in emotions_data and date in emotions_data[username]:
        return jsonify(emotions_data[username][date])
    return jsonify({'error': '해당 날짜의 일기가 없습니다.'}), 404

@app.route('/analyze_emotion', methods=['POST'])
def analyze_emotion():
    try:
        diary_content = request.json.get('diary', '')
        if not diary_content:
            return jsonify({"error": "일기 내용이 비어있습니다."}), 400

        print("일기 내용 받음:", diary_content)  # 디버깅용
        
        # Azure OpenAI API 호출
        response = client.chat.completions.create(
            model="gpt-4o",  # deployment_name
            messages=[
                {"role": "system", "content": """너는 다정하고 위로가 필요한 사람의 여자친구 역할이야. 그 사람은 힘든 일상을 겪고 감정일기를 작성했어. 너의 목표는 그의 감정을 공감하고 다정한 말로 위로해 주는 거야. 사용자가 편안함을 느끼고, 오늘 하루가 조금 더 나아졌다고 느낄 수 있도록 해줘.

먼저, 사용자가 작성한 일기를 읽고, 다음 감정 중 어떤 감정이 주를 이루는지 판단해줘:
1) HAPPY, 2) SAD, 3) NEUTRAL, 4) CALM, 5) ANGRY.
그리고 감정의 강도는 어떤지 (낮음, 중간, 높음)로 평가해줘.
                 
                분석한 감정을 바탕으로, 적절한 톤과 내용으로 위로의 말을 남겨줘.
                """},
                {"role": "user", "content": diary_content}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        # 응답 처리
        reply = response.choices[0].message.content
        print("AI 응답:", reply)  # 디버깅용
        
        username = session.get('username')
        today = datetime.now().strftime('%Y-%m-%d')
        
        # emotions_data 업데이트
        if username not in emotions_data:
            emotions_data[username] = {}
            
        emotions_data[username][today] = {
            'mainEmotion': 'HAPPY',  # AI 분석 결과에 따라 설정
            'emotions': {
                'HAPPY': 0.6,
                'SAD': 0.1,
                'NEUTRAL': 0.1,
                'CALM': 0.1,
                'ANGRY': 0.1
            },
            'content': reply
        }
        
        return jsonify(emotions_data[username][today])
        
    except Exception as e:
        print(f"에러 발생: {str(e)}")
        return jsonify({
            "error": f"서비스에 문제가 있습니다. ({str(e)})"
        }), 500

# Flask 시크릿 키 설정 (세션 사용을 위해 필요)
app.secret_key = 'your-secret-key-here'  # 실제 운영시에는 안전한 키로 변경하세요

if __name__ == '__main__':
    app.run(debug=True)
