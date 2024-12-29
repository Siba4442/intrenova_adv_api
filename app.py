from fastapi import FastAPI, HTTPException
from Domain.domain import JobFilterRequest, CandidateFilterRequest, JobSkillsRequest, CandidateSkillsRequest
from Service.recommedation import RecommedationService

rem_app = FastAPI(title="Job Recommendation API")

recommendation_service = RecommedationService()

@rem_app.get("/")
def root():
    return {"message": "Welcome to the Job Recommendation API!"}

@rem_app.post("/match_candidates")
async def match_candidates(request: JobFilterRequest):
    try:
        return recommendation_service.JobService(request=request)
    except ValueError as e: 
        raise HTTPException(status_code=400, detail=str(e))
    
@rem_app.post("/match_jobs")
async def match_jobs(request: CandidateFilterRequest):
    try:
        return recommendation_service.CandidateServices(request=request)
    except ValueError as e: 
        raise HTTPException(status_code=400, detail=str(e))
    
    
@rem_app.post("/jobskills")
async def jobskills(request: JobSkillsRequest):
    try:
        return recommendation_service.JobSkills(request=request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@rem_app.post("/canskills")
async def canskills(request: CandidateSkillsRequest):
    try:
        return recommendation_service.CandidateSkills(request=request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    