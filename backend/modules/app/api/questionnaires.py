from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Any
from core.database import get_db
from shared.models import Questionnaire, Employee, Task, Customer, QuestionnaireResponse as QuestionnaireResponseModel, IncidentReport, TaskQuestionnaire
from ..schemas.questionnaire import QuestionnaireResponse, QuestionnaireSubmissionCreate, QuestionnaireSubmissionResponse
from ..dependencies import get_current_employee
from datetime import datetime

router = APIRouter(prefix="/api/app/questionnaires", tags=["问卷"])

FALL_KEYWORDS = ["跌倒", "fall", "near fall", "near_fall", "差点跌倒", "near-fall"]


def _answers_contain_fall(questionnaire, answers: dict) -> bool:
    """检查 answers 是否含有跌倒相关选项"""
    if not questionnaire or not questionnaire.questions:
        return False
    for q in questionnaire.questions:
        opts = q.options or []
        opt_map = {}
        for o in opts:
            if not isinstance(o, dict):
                continue
            option_text = (
                o.get("text")
                or o.get("label")
                or (o.get("text_i18n") or {}).get("zh")
                or (o.get("text_i18n") or {}).get("en")
                or o.get("value")
                or ""
            )
            opt_map[str(o.get("id", ""))] = str(option_text).lower()
        ans = answers.get(q.id)
        if ans is None:
            continue
        ids = [ans] if not isinstance(ans, list) else ans
        for oid in ids:
            text = opt_map.get(str(oid), "")
            if any(kw.lower() in text for kw in FALL_KEYWORDS):
                return True
    return False


def _check_conditional_required(questionnaire, answers: dict) -> str | None:
    """条件必填校验，返回错误信息或 None"""
    if not questionnaire or not questionnaire.questions:
        return None
    import json
    for q in questionnaire.questions:
        if not getattr(q, "conditional_required", False):
            continue
        dep = getattr(q, "depends_on", None)
        if not dep:
            continue
        try:
            cond = json.loads(dep) if isinstance(dep, str) else dep
        except Exception:
            continue
        qid = cond.get("question_id") or cond.get("questionId")
        expected = cond.get("value")
        if not qid:
            continue
        ans = answers.get(qid)
        if ans is None:
            continue
        actual = ans if isinstance(ans, (str, int, float, bool)) else (ans[0] if isinstance(ans, list) and ans else None)
        if actual is None:
            continue
        matches = actual == expected if expected is not None else True
        if isinstance(ans, list) and expected is not None:
            matches = expected in ans
        if matches:
            val = answers.get(q.id)
            if val is None or (isinstance(val, str) and not val.strip()) or (isinstance(val, list) and not val):
                return f"请填写：{q.title}"
    return None


@router.get("", response_model=List[QuestionnaireResponse])
async def get_questionnaires(
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """获取活跃的问卷列表"""
    questionnaires = db.query(Questionnaire).filter(Questionnaire.is_active == True).all()
    return questionnaires


@router.get("/{questionnaire_id}", response_model=QuestionnaireResponse)
async def get_questionnaire(
    questionnaire_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """获取问卷详情"""
    questionnaire = db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()
    if not questionnaire:
        raise HTTPException(status_code=404, detail="问卷不存在")
    return questionnaire


@router.post("/{questionnaire_id}/responses", response_model=QuestionnaireSubmissionResponse)
async def submit_questionnaire(
    questionnaire_id: str,
    submission: QuestionnaireSubmissionCreate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """提交问卷"""
    questionnaire = db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()
    if not questionnaire:
        raise HTTPException(status_code=404, detail="问卷不存在")

    task = db.query(Task).filter(Task.id == submission.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    tq_list = db.query(TaskQuestionnaire).filter(TaskQuestionnaire.task_id == submission.task_id).all()
    if tq_list:
        allowed = {tq.questionnaire_id for tq in tq_list}
        if questionnaire_id not in allowed:
            raise HTTPException(status_code=400, detail="该任务未关联此问卷")
    elif getattr(task, "questionnaire_id", None) and task.questionnaire_id != questionnaire_id:
        raise HTTPException(status_code=400, detail="该任务指定的问卷与提交问卷不一致")

    if task.customer_id != submission.customer_id:
        raise HTTPException(status_code=400, detail="客户与任务不匹配")

    if task.assigned_employee_id and task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="无权提交该任务问卷")

    if _answers_contain_fall(questionnaire, submission.answers):
        report = db.query(IncidentReport).filter(IncidentReport.task_id == submission.task_id).first()
        if not report:
            raise HTTPException(
                status_code=400,
                detail="问卷中选择跌倒/差点跌倒时，请先填写事故报告",
            )

    cond_err = _check_conditional_required(questionnaire, submission.answers)
    if cond_err:
        raise HTTPException(status_code=400, detail=cond_err)

    customer = db.query(Customer).filter(Customer.id == submission.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    response = db.query(QuestionnaireResponseModel).filter(
        QuestionnaireResponseModel.questionnaire_id == questionnaire_id,
        QuestionnaireResponseModel.task_id == submission.task_id,
        QuestionnaireResponseModel.customer_id == submission.customer_id,
        QuestionnaireResponseModel.employee_id == current_employee.id,
    ).first()

    if response:
        now = datetime.utcnow()
        db.query(QuestionnaireResponseModel).filter(
            QuestionnaireResponseModel.id == response.id
        ).update(
            {"answers": submission.answers, "submitted_at": now}
        )
        response.answers = submission.answers
        response.submitted_at = now
    else:
        response = QuestionnaireResponseModel(
            questionnaire_id=questionnaire_id,
            task_id=submission.task_id,
            customer_id=submission.customer_id,
            employee_id=current_employee.id,
            answers=submission.answers
        )
        db.add(response)

    if tq_list:
        db.query(TaskQuestionnaire).filter(
            TaskQuestionnaire.task_id == submission.task_id,
            TaskQuestionnaire.questionnaire_id == questionnaire_id,
        ).update({"is_filled": True})
    else:
        if getattr(task, "questionnaire_id", None) == questionnaire_id:
            task.questionnaire_data = submission.answers

    db.commit()
    db.refresh(response)
    return response
