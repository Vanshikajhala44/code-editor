from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.http import JsonResponse
from .models import CodingQuestion, CodeSubmission

from .service.groq import generate_coding_question
import json
import requests

def index(request):
    return render(request, 'editor/index.html')

def generate_question(request):
    if request.method == "POST":
        data = json.loads(request.body)
        topic = data.get("topic", "Arrays")
        difficulty = data.get("difficulty", "medium")
        language = data.get("language", "python")

        # generate from groq
        question_data = generate_coding_question(topic, difficulty, language)

        # save to DB
        question = CodingQuestion.objects.create(
            topic=topic,
            difficulty=difficulty,
            language=language,
            title=question_data['title'],
            description=question_data['description'],
            example_input=question_data['example_input'],
            example_output=question_data['example_output'],
            constraints=question_data['constraints'],
            starter_code=question_data['starter_code']
        )

        return JsonResponse({
            "success": True,
            "question_id": question.id,
            "question": question_data
        })


def coding_round(request, question_id):
    question = CodingQuestion.objects.get(id=question_id)
    return render(request, 'editor/coding_round.html', {
        'question': question
    })


def run_code(request):
    if request.method == "POST":
        data = json.loads(request.body)
        code = data.get("code")
        language = data.get("language", "python")
        stdin = data.get("stdin", "")      # ← stdin bhi lo

        language_map = {
            'python': {'language': 'python3', 'versionIndex': '3'},
            'javascript': {'language': 'nodejs', 'versionIndex': '3'},
            'java': {'language': 'java', 'versionIndex': '3'},
            'cpp': {'language': 'cpp17', 'versionIndex': '0'},
        }

        lang_config = language_map.get(language, language_map['python'])

        response = requests.post(
            "https://api.jdoodle.com/v1/execute",
            json={
                "clientId": "1b99ff6abbef12758a0932e1bcabb832",
                "clientSecret": "982c1da6685e5a1a55c6cfe2c958fa64c0e9ab488212139ceeb608fad74d0f29",
                "script": code,
                "stdin": stdin,             # ← stdin pass karo
                "language": lang_config['language'],
                "versionIndex": lang_config['versionIndex'],
            }
        )

        result = response.json()
        print("JDOODLE RESPONSE:", result)

        return JsonResponse({
            "output": result.get("output", "No output"),
            "stderr": "",
        })
def submit_code(request):
    if request.method == "POST":
        data = json.loads(request.body)
        question = CodingQuestion.objects.get(id=data.get("question_id"))

        submission = CodeSubmission.objects.create(
            question=question,
            language=data.get("language"),
            code=data.get("code"),
            output=data.get("output", ""),
            stderr=data.get("stderr", ""),
            status="Submitted"
        )

        return JsonResponse({
            "success": True,
            "redirect": f"/success/{submission.id}/"
        })


def success(request, submission_id):
    submission = CodeSubmission.objects.get(id=submission_id)
    return render(request, 'editor/success.html', {
        'submission': submission
    })