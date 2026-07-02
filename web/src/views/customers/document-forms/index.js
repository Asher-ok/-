import GenericFormEditor from './GenericFormEditor.vue'
import FeedbackEditor from './FeedbackEditor.vue'
import IntakeFormEditor from './IntakeFormEditor.vue'
import EasyReadEditor from './EasyReadEditor.vue'
import ConsentFormEditor from './ConsentFormEditor.vue'
import HandbookEditor from './HandbookEditor.vue'
import ServiceAgreementEditor from './ServiceAgreementEditor.vue'
import SupportPlanEditor from './SupportPlanEditor.vue'
import EmergencyPlanEditor from './EmergencyPlanEditor.vue'
import HomeSafetyEditor from './HomeSafetyEditor.vue'
import RiskAssessmentEditor from './RiskAssessmentEditor.vue'
import ReviewFormEditor from './ReviewFormEditor.vue'
import ExitFormEditor from './ExitFormEditor.vue'

const DOCUMENT_FORM_MAP = {
  feedback: FeedbackEditor,
  intake_form: IntakeFormEditor,
  easy_read: EasyReadEditor,
  consent_form: ConsentFormEditor,
  handbook: HandbookEditor,
  service_agreement: ServiceAgreementEditor,
  support_plan: SupportPlanEditor,
  emergency_plan: EmergencyPlanEditor,
  home_safety: HomeSafetyEditor,
  risk_assessment: RiskAssessmentEditor,
  review_form: ReviewFormEditor,
  exit_form: ExitFormEditor
}

export function getFormComponent(documentType) {
  return DOCUMENT_FORM_MAP[documentType] || GenericFormEditor
}

export { GenericFormEditor, FeedbackEditor }
