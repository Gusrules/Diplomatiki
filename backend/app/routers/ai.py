import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.core.gemini_client import generate_questions_json

from app.models.subject import Subject as SubjectModel
from app.models.module import Module as ModuleModel
from app.models.question import Question as QuestionModel
from app.models.resource import Resource as ResourceModel
from app.schemas.ai import AIGenerateFlashcardsIn, AIGenerateFlashcardsOut

from app.schemas.ai import (
    AIGenerateQuestionsIn,
    AIGenerateFromResourceIn,
    AIGenerateFromResourceOut,
)
from app.models.quiz import Quiz as QuizModel
from app.models.quiz_question import QuizQuestion as QuizQuestionModel
from app.core.deps import require_teacher

import random

def shuffle_choices_keep_correct(choices: list[str], correct_index: int):
    pairs = list(enumerate(choices))          # [(0,"..."), (1,"..."), ...]
    correct_pair = pairs[correct_index]       # (ci, "correct text")
    random.shuffle(pairs)
    new_choices = [text for _, text in pairs]
    new_correct_index = [i for i, p in enumerate(pairs) if p == correct_pair][0]
    return new_choices, new_correct_index


router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/generate-questions")
def ai_generate_questions(
    data: AIGenerateQuestionsIn,
    db: Session = Depends(get_db),
    _s = Depends(require_teacher),
):
    subject = db.query(SubjectModel).filter(SubjectModel.id == data.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    module = None
    if data.module_id is not None:
        module = db.query(ModuleModel).filter(ModuleModel.id == data.module_id).first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")

    module_txt = f"Module: {module.title}" if module else "No module"
    prompt = f"""
Create {data.n} multiple-choice questions for students.

Subject: {subject.name}
{module_txt}

Return ONLY JSON with exactly this schema:
{{
  "questions": [
    {{
      "prompt": "string",
      "choices": ["A", "B", "C", "D"],
      "correct_index": 0
    }}
  ]
}}

Rules:
- choices must be exactly 4 strings
- correct_index must be 0..3
- Keep questions short and clear
"""

    try:
        out = generate_questions_json(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini error: {str(e)}")

    if "questions" not in out or not isinstance(out["questions"], list):
        raise HTTPException(status_code=500, detail="Invalid Gemini JSON format")

    created = []
    for q in out["questions"]:
        if "prompt" not in q or "choices" not in q or "correct_index" not in q:
            continue

        choices = q["choices"]
        ci = q["correct_index"]

        # optional: shuffle so the correct is not always same position
        choices, ci = shuffle_choices_keep_correct(choices, ci)

        question = QuestionModel(
            subject_id=data.subject_id,
            module_id=data.module_id,
            prompt=q["prompt"],
            choices=choices,
            correct_index=ci,
            difficulty_score=5.0,
        )
        db.add(question)
        db.flush()
        created.append({"id": question.id, "prompt": question.prompt})

    db.commit()
    return {"created": created, "count": len(created)}
    
@router.post("/generate-from-resource", response_model=AIGenerateFromResourceOut)
def ai_generate_from_resource(
    data: AIGenerateFromResourceIn,
    db: Session = Depends(get_db),
    _s = Depends(require_teacher),
):
    res = (
        db.query(ResourceModel)
        .filter(ResourceModel.id == data.resource_id)
        .filter(ResourceModel.deleted == False)  # noqa
        .first()
    )
    if not res:
        raise HTTPException(status_code=404, detail="Resource not found")

    if not res.content or not res.content.strip():
        raise HTTPException(
            status_code=400,
            detail="Resource has no content. Fill resources.content first.",
        )

    # βρίσκουμε module + subject για context
    module = db.query(ModuleModel).filter(ModuleModel.id == res.module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found for this resource")

    subject = db.query(SubjectModel).filter(SubjectModel.id == module.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found for this module")

    # πολύ σημαντικό: "use ONLY this content" για να μην βγάζει random
    prompt = f"""
You are an educational content generator.

Create {data.n} multiple-choice questions STRICTLY based on the STUDY MATERIAL below.
Do NOT use outside knowledge. If something is not in the material, do not ask it.

Subject: {subject.name}
Module: {module.title}

STUDY MATERIAL:
\"\"\"{res.content}\"\"\"

Return ONLY JSON with exactly this schema:
{{
  "questions": [
    {{
      "prompt": "string",
      "choices": ["A", "B", "C", "D"],
      "correct_index": 0
    }}
  ]
}}

Rules:
- choices must be exactly 4 strings
- correct_index must be 0..3
- Questions must be answerable from the STUDY MATERIAL.
- Use terminology appearing in the STUDY MATERIAL.
- Avoid translation-style or meta questions about the text.
- Prefer questions that test understanding (small examples), not only definitions.
"""

    try:
        out = generate_questions_json(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini error: {str(e)}")

    if "questions" not in out or not isinstance(out["questions"], list):
        raise HTTPException(status_code=500, detail="Invalid Gemini JSON format")

    created = []
    for q in out["questions"]:
        if "prompt" not in q or "choices" not in q or "correct_index" not in q:
            continue
        if not isinstance(q["choices"], list) or len(q["choices"]) != 4:
            continue
        if not isinstance(q["correct_index"], int) or not (0 <= q["correct_index"] <= 3):
            continue


        choices = q["choices"]
        ci = q["correct_index"]

        # optional: shuffle so the correct is not always same position
        choices, ci = shuffle_choices_keep_correct(choices, ci)    

        question = QuestionModel(
            subject_id=subject.id,
            module_id=module.id,
            resource_id=res.id, 
            prompt=q["prompt"],
            choices=choices,
            correct_index=ci,
            difficulty_score=5.0,
        )
        db.add(question)
        db.flush()
        created.append({"id": question.id, "prompt": question.prompt})

    db.commit()

    # AUTO-ADD TO QUIZ
    if data.auto_add_to_quiz:
        # 1) resolve quiz
        quiz = None
        if data.quiz_id is not None:
            quiz = db.query(QuizModel).filter(QuizModel.id == data.quiz_id).first()
            if not quiz:
                raise HTTPException(status_code=404, detail="Quiz not found")

        # 2) if no quiz_id: find or create a default quiz for module
        if quiz is None:
            quiz = (
                db.query(QuizModel)
                .filter(QuizModel.module_id == module.id)   # αν έχεις module_id στο quiz
                .first()
            )

            if quiz is None:
                quiz = QuizModel(
                    subject_id=subject.id,
                    module_id=module.id,  # αν υπάρχει
                    title=f"Auto Quiz - {module.title}",
                )
                db.add(quiz)
                db.flush()

        # 3) add question links (avoid duplicates)
        for item in created:
            qid = item["id"]
            exists = (
                db.query(QuizQuestionModel)
                .filter(
                    QuizQuestionModel.quiz_id == quiz.id,
                    QuizQuestionModel.question_id == qid,
                )
                .first()
            )
            if not exists:
                db.add(QuizQuestionModel(quiz_id=quiz.id, question_id=qid))

        db.commit()

        return {"resource_id": res.id, "created": created, "count": len(created), "quiz_id": quiz.id}

    return {"resource_id": res.id, "created": created, "count": len(created)}


@router.post("/generate-flashcards-from-resource", response_model=AIGenerateFlashcardsOut)
def ai_generate_flashcards_from_resource(
    data: AIGenerateFlashcardsIn,
    db: Session = Depends(get_db),
    _s = Depends(require_teacher),
):
    res = (
        db.query(ResourceModel)
        .filter(ResourceModel.id == data.resource_id)
        .filter(ResourceModel.deleted == False)  # noqa
        .first()
    )
    if not res:
        raise HTTPException(status_code=404, detail="Resource not found")

    if not res.content or not res.content.strip():
        raise HTTPException(status_code=400, detail="Resource has no content")

    module = db.query(ModuleModel).filter(ModuleModel.id == res.module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found for resource")

    subject = db.query(SubjectModel).filter(SubjectModel.id == module.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found for module")

    prompt = f"""
You are an educational flashcard generator.

Create {data.n} flashcards STRICTLY based on the STUDY MATERIAL below.
Do NOT use outside knowledge. If something is not in the material, do not include it.

Subject: {subject.name}
Module: {module.title}

STUDY MATERIAL:
\"\"\"{res.content}\"\"\"

Return ONLY JSON with exactly this schema:
{{
  "flashcards": [
    {{
      "front": "string",
      "back": "string"
    }}
  ]
}}

Rules:
- Each flashcard must be answerable ONLY from the STUDY MATERIAL.
- front: a short question/term
- back: short, clear explanation/answer
"""

    try:
        out = generate_questions_json(prompt)  # ναι, την ίδια helper χρησιμοποιούμε, απλά περιμένουμε flashcards JSON
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini error: {str(e)}")

    if "flashcards" not in out or not isinstance(out["flashcards"], list):
        raise HTTPException(status_code=500, detail="Invalid Gemini JSON format for flashcards")

    cards = []
    for fc in out["flashcards"]:
        if not isinstance(fc, dict):
            continue
        front = fc.get("front")
        back = fc.get("back")
        if not front or not back:
            continue
        cards.append({"front": front.strip(), "back": back.strip()})

    if not cards:
        raise HTTPException(status_code=500, detail="Gemini returned no valid flashcards")

    flash_res = ResourceModel(
        module_id=res.module_id,
        type="flashcard",
        title=f"Flashcards - {res.title}",
        file_path="generated",
        file_type="json",
        uploaded_by=res.uploaded_by,
        content=json.dumps({"flashcards": cards}, ensure_ascii=False),
    )

    db.add(flash_res)
    db.commit()
    db.refresh(flash_res)

    return AIGenerateFlashcardsOut(
        source_resource_id=res.id,
        flashcard_resource_id=flash_res.id,
        count=len(cards),
    )
