from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from typing import List
from core.database import get_db
from shared.models import Questionnaire, Question, QuestionnaireResponse as QuestionnaireResponseModel
from ..schemas.questionnaire import (
    QuestionnaireCreate, QuestionnaireUpdate, QuestionnaireResponse,
    QuestionCreate, QuestionUpdate, QuestionResponse,
    QuestionnaireSubmissionListItem, QuestionnaireSubmissionDetail
)
from ..dependencies import get_current_user
from core.utils.file_utils import ensure_upload_dir
from ..services.questionnaire_export import generate_questionnaire_response_pdf
from datetime import datetime

router = APIRouter(prefix="/api/houtai/questionnaires", tags=["管理-问卷"])


@router.get("", response_model=List[QuestionnaireResponse])
async def get_questionnaires(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取所有问卷列表"""
    questionnaires = db.query(Questionnaire).order_by(Questionnaire.created_at.desc()).all()
    return questionnaires


@router.get("/responses", response_model=List[QuestionnaireSubmissionListItem])
async def get_questionnaire_responses(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取问卷提交记录列表"""
    responses = (
        db.query(QuestionnaireResponseModel)
        .filter(QuestionnaireResponseModel.submitted_at.isnot(None))
        .order_by(QuestionnaireResponseModel.submitted_at.desc())
        .all()
    )
    return [
        QuestionnaireSubmissionListItem(
            id=response.id,
            questionnaire_id=response.questionnaire_id,
            questionnaire_title=response.questionnaire.title if response.questionnaire else "",
            task_id=response.task_id,
            task_title=response.task.title if response.task else "",
            customer_id=response.customer_id,
            customer_name=response.customer.name if response.customer else "",
            employee_id=response.employee_id,
            employee_name=response.employee.name if response.employee else "",
            submitted_at=response.submitted_at
        )
        for response in responses
    ]


@router.get("/responses/{response_id}", response_model=QuestionnaireSubmissionDetail)
async def get_questionnaire_response(
    response_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取问卷提交记录详情"""
    response = db.query(QuestionnaireResponseModel).filter(
        QuestionnaireResponseModel.id == response_id
    ).first()
    if not response:
        raise HTTPException(status_code=404, detail="提交记录不存在")

    return QuestionnaireSubmissionDetail(
        id=response.id,
        questionnaire_id=response.questionnaire_id,
        questionnaire_title=response.questionnaire.title if response.questionnaire else "",
        task_id=response.task_id,
        task_title=response.task.title if response.task else "",
        customer_id=response.customer_id,
        customer_name=response.customer.name if response.customer else "",
        employee_id=response.employee_id,
        employee_name=response.employee.name if response.employee else "",
        submitted_at=response.submitted_at,
        answers=response.answers,
        questions=response.questionnaire.questions if response.questionnaire else []
    )


@router.get("/responses/{response_id}/export")
async def export_questionnaire_response(
    response_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """导出问卷提交记录 PDF"""
    response = db.query(QuestionnaireResponseModel).filter(
        QuestionnaireResponseModel.id == response_id
    ).first()
    if not response:
        raise HTTPException(status_code=404, detail="提交记录不存在")

    upload_dir = ensure_upload_dir()
    filename = f"questionnaire_response_{response_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = upload_dir / filename

    generate_questionnaire_response_pdf(response, str(file_path))

    return FileResponse(
        str(file_path),
        filename=filename,
        media_type="application/pdf"
    )


@router.delete("/responses/{response_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_questionnaire_response(
    response_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除问卷提交记录"""
    response = db.query(QuestionnaireResponseModel).filter(
        QuestionnaireResponseModel.id == response_id
    ).first()
    if not response:
        raise HTTPException(status_code=404, detail="提交记录不存在")
    db.delete(response)
    db.commit()
    return None


@router.post("", response_model=QuestionnaireResponse, status_code=status.HTTP_201_CREATED)
async def create_questionnaire(
    questionnaire_data: QuestionnaireCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建问卷"""
    questions_data = questionnaire_data.questions or []
    questionnaire_dict = questionnaire_data.model_dump(exclude={"questions"})
    
    questionnaire = Questionnaire(**questionnaire_dict)
    db.add(questionnaire)
    db.flush()  # 获取ID
    
    # 添加问题
    for idx, question_data in enumerate(questions_data):
        q_dict = question_data.model_dump()
        order_index = q_dict.pop("order_index", idx)
        question = Question(
            questionnaire_id=questionnaire.id,
            order_index=order_index,
            **q_dict
        )
        db.add(question)
    
    db.commit()
    db.refresh(questionnaire)
    return questionnaire


@router.get("/{questionnaire_id}", response_model=QuestionnaireResponse)
async def get_questionnaire(
    questionnaire_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取问卷详情"""
    questionnaire = db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()
    if not questionnaire:
        raise HTTPException(status_code=404, detail="问卷不存在")
    return questionnaire


@router.put("/{questionnaire_id}", response_model=QuestionnaireResponse)
async def update_questionnaire(
    questionnaire_id: str,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新问卷"""
    if "questions" not in payload:
        for alt in ("questionList", "question_list", "items"):
            if alt in payload:
                payload["questions"] = payload.get(alt)
                break
    questions = payload.get("questions")
    if isinstance(questions, list):
        normalized = []
        for q in questions:
            if not isinstance(q, dict):
                normalized.append(q)
                continue
            q2 = dict(q)
            if "id" not in q2:
                for kid in ("question_id", "questionId"):
                    if kid in q2:
                        q2["id"] = q2.get(kid)
                        break
            if "order_index" not in q2:
                for kidx in ("orderIndex", "order"):
                    if kidx in q2:
                        q2["order_index"] = q2.get(kidx)
                        break
            normalized.append(q2)
        payload["questions"] = normalized

    questionnaire_data = QuestionnaireUpdate.model_validate(payload)
    questionnaire = (
        db.query(Questionnaire)
        .options(joinedload(Questionnaire.questions))
        .filter(Questionnaire.id == questionnaire_id)
        .first()
    )
    if not questionnaire:
        raise HTTPException(status_code=404, detail="问卷不存在")
    
    update_data = questionnaire_data.model_dump(exclude_unset=True, exclude={"questions"})
    for key, value in update_data.items():
        setattr(questionnaire, key, value)

    if questionnaire_data.questions is not None:
        existing_by_id = {q.id: q for q in questionnaire.questions}
        keep_question_ids = set()

        for idx, incoming in enumerate(questionnaire_data.questions):
            q_payload = incoming.model_dump(exclude_unset=True)
            incoming_id = q_payload.pop("id", None)
            incoming_order_index = q_payload.pop("order_index", None)
            q_payload["order_index"] = idx if incoming_order_index is None else incoming_order_index

            if incoming_id and incoming_id in existing_by_id:
                keep_question_ids.add(incoming_id)
                q_obj = existing_by_id[incoming_id]
                for k, v in q_payload.items():
                    setattr(q_obj, k, v)
            else:
                q_obj = Question(questionnaire_id=questionnaire.id, **q_payload)
                db.add(q_obj)
                db.flush()
                keep_question_ids.add(q_obj.id)

        for q_obj in list(questionnaire.questions):
            if q_obj.id not in keep_question_ids:
                db.delete(q_obj)
    
    db.commit()
    updated = (
        db.query(Questionnaire)
        .options(joinedload(Questionnaire.questions))
        .filter(Questionnaire.id == questionnaire_id)
        .first()
    )
    return updated


@router.delete("/{questionnaire_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_questionnaire(
    questionnaire_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除问卷"""
    questionnaire = db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()
    if not questionnaire:
        raise HTTPException(status_code=404, detail="问卷不存在")
    
    db.delete(questionnaire)
    db.commit()
    return None


@router.post("/{questionnaire_id}/questions", status_code=status.HTTP_201_CREATED)
async def add_question(
    questionnaire_id: str,
    question_data: QuestionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """添加问题"""
    questionnaire = db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()
    if not questionnaire:
        raise HTTPException(status_code=404, detail="问卷不存在")
    
    question = Question(questionnaire_id=questionnaire_id, **question_data.dict())
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.put("/{questionnaire_id}/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    questionnaire_id: str,
    question_id: str,
    question_data: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新问题"""
    question = db.query(Question).filter(
        Question.id == question_id,
        Question.questionnaire_id == questionnaire_id
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="问题不存在")
    
    update_data = question_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(question, key, value)
    
    db.commit()
    db.refresh(question)
    return question


@router.delete("/{questionnaire_id}/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    questionnaire_id: str,
    question_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除问题"""
    question = db.query(Question).filter(
        Question.id == question_id,
        Question.questionnaire_id == questionnaire_id
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="问题不存在")
    
    db.delete(question)
    db.commit()
    return None
