from pydantic import BaseModel
from typing import List, Optional

# Request Model for canditate
class JobFilterRequest(BaseModel):
    Job_id: str
    Country: Optional[str] = None
    Location: Optional[str] = None
    Experience: Optional[int] = None
    Certification: Optional[List[str]] = None
    Sector: Optional[str] = None
    Gender: Optional[str] = None
    Age: Optional[int] = None
    

# Request model for candidate
class CandidateFilterRequest(BaseModel):
    User_id: str
    Country: Optional[str] = None
    Location: Optional[str] = None
    Experience: Optional[int] = None
    Certification: Optional[List[str]] =  None
    Sector: Optional[str] =  None
    Gender: Optional[str] = None
    Age: Optional[int] = None
    
    
class CandidateSkillsRequest(BaseModel):
    User_id: str
    
class JobSkillsRequest(BaseModel):
    Job_id: str
    