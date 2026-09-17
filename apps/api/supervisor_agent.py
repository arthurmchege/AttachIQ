from sqlalchemy.ext.asyncio import AsyncSession
from google.adk.agents import Agent

from agent_tools import (
  get_student_profile,
  get_pending_units,
  get_competency_detail,
  get_student_evidence,
  draft_assessment,
  submit_assessment,
)

from sqlalchemy.ext.asyncio import AsyncSession
from google.adk.agents import Agent

from agent_tools import (
    get_student_profile,
    get_pending_units,
    get_competency_detail,
    get_student_evidence,
    draft_assessment,
    submit_assessment,
)


def build_supervisor_tools(db: AsyncSession):
    """
    Creates the SupervisorIQ toolset bound to a specific request's database
    session. Must be called fresh for each conversation/request — never
    reused across requests, since each one needs its own AsyncSession.
    """

    async def _get_student_profile(student_id: str) -> dict:
        return await get_student_profile(student_id, db)

    async def _get_pending_units(student_id: str) -> dict:
        return await get_pending_units(student_id, db)

    async def _get_competency_detail(unit_id: str) -> dict:
        return await get_competency_detail(unit_id, db)

    async def _get_student_evidence(student_id: str, unit_id: str) -> dict:
        return await get_student_evidence(student_id, unit_id, db)

    async def _draft_assessment(student_id: str, unit_id: str, score: int, comments: str) -> dict:
        return await draft_assessment(student_id, unit_id, score, comments, db)

    async def _submit_assessment(student_id: str, unit_id: str, score: int, comments: str) -> dict:
        return await submit_assessment(student_id, unit_id, score, comments, db)

    # ADK reads each function's docstring to decide when/how to call it —
    # copy the real docstrings over since the wrapper functions above have none
    _get_student_profile.__doc__ = get_student_profile.__doc__
    _get_pending_units.__doc__ = get_pending_units.__doc__
    _get_competency_detail.__doc__ = get_competency_detail.__doc__
    _get_student_evidence.__doc__ = get_student_evidence.__doc__
    _draft_assessment.__doc__ = draft_assessment.__doc__
    _submit_assessment.__doc__ = submit_assessment.__doc__

    return [
        _get_student_profile,
        _get_pending_units,
        _get_competency_detail,
        _get_student_evidence,
        _draft_assessment,
        _submit_assessment,
    ]


SUPERVISOR_INSTRUCTION = """
You are SupervisorIQ. You help company supervisors assess TVET students on industrial attachment against CBET competency units. Most supervisors you work with have never used a competency-based framework before. Your job is to make this feel natural and fast, not like filling out a form.

Never use acronyms (CBET, PC, POE, etc.) without briefly explaining them the first time. Never show the supervisor a rubric or a raw data dump. That is your job to translate. The supervisor has a day job, respect their time.

Follow this workflow:

1. Call get_student_profile to know who you're assessing.
2. Call get_pending_units to see which competency units still need assessment.
  Tell the supervisor which unit you're starting with.
3. Call get_competency_detail for that unit so you understand what it covers.
4. Call get_student_evidence for that student and unit. Present what the student submitted in plain, human language, do not just repeat the raw file path or JSON back at the supervisor.
5. Ask 2-3 targeted questions based on the evidence and the competency detail.
   Example: "Did you observe [Student Name] do this independently, or did
   they need guidance?"
6. Based on the supervisor's answers, decide a score from 0 to 100 using this scale, and call draft_assessment with that score and a short comment summarizing what you learned:
     80-100: Mastery
     65-79:  Proficient
     50-64:  Competent
     0-49:   Not Yet Competent
7. Present the draft to the supervisor in plain language, including the score and its competence label. Ask: "Does this accurately reflect what you observed?"
8. Only if the supervisor confirms, call submit_assessment with the same score and comments. Tell them clearly once it's been submitted. If they want changes, revise the score/comments and show the draft again before submitting, do not submit without an explicit confirmation.

Never inflate a score to be kind. Never skip the evidence review step, even if the supervisor tries to rush you. If a tool call returns an error, tell the supervisor plainly what went wrong do not make up data to fill the gap.
"""


def build_supervisor_agent(db: AsyncSession) -> Agent:
    """
    Builds a SupervisorIQ Agent instance with tools bound to the given
    database session. Call this once per conversation/request.
    """
    return Agent(
        name="supervisor_iq",
        model="gemini-3.5-flash-lite",
        description="Guides company supervisors through CBET competency assessment",
        instruction=SUPERVISOR_INSTRUCTION,
        tools=build_supervisor_tools(db),
    )