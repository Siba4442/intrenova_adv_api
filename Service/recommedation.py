from pymongo import MongoClient
import numpy as np
import joblib
import spacy
import json 
from PyPDF2 import PdfReader
import requests
from gensim.models import Word2Vec
from sklearn.metrics.pairwise import cosine_similarity 
from datetime import datetime
from Domain.domain import CandidateSkillsRequest, JobFilterRequest, CandidateFilterRequest, JobSkillsRequest

class RecommedationService():
    
    def __init__(self):
        
        self.nlp = spacy.load("Artifacts/en_core_web_sm-3.7.1")
        self.path_WVmodel = "Artifacts/Word2vec_skills.model"
        self.path_TFmomdel = "Artifacts/TF-IDF_skills.pkl"
        self.path_Skills_ID = "Artifacts/SKills_ID.json"
        self.path_SurfaceFrom_ID = "Artifacts/SurfaceFrom_ID.json"
        self.path_SurfaceFrom = "Artifacts/SurfaceForm.json"
        self.path_vectorizer = "Artifacts/vectorizer.pkl"
        
        self.word2vec_model = Word2Vec.load(self.path_WVmodel)
        
        with open(self.path_Skills_ID, 'r') as f:
            self.Skills_ID = json.load(f)
            
        with open(self.path_SurfaceFrom_ID, 'r') as f:
            self.SurfaceFrom_ID = json.load(f)
            
        with open(self.path_SurfaceFrom, 'r') as f:
            self.SurfaceForm = json.load(f) 
            
        self.TFIDF_skills = joblib.load(self.path_TFmomdel)
        
        # self.summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
        
        self.vectorizer = joblib.load(self.path_vectorizer)
        
        mongo_uri = "mongodb+srv://tm026575:ansu2003@internovacluster.byibt.mongodb.net/?retryWrites=true&w=majority&appName=internovaCluster"
        self.client = MongoClient(mongo_uri)
        self.db = self.client["internova_profile"]
        self.candidate_collection = self.db["candidate_profile"]
        self.job_collection = self.db["job_profile"]
        self.resume_collection = self.db["resume"]
    
        
    def normalize_token(self, token):
        return token.lower().replace(',', ' ').replace(' ', '_').split()
    
    
    def compute_vector(self, words_list, model):
        vectors = [model[word] for word in words_list if word in model]
        return np.mean(vectors, axis=0) if vectors else np.zeros(model.vector_size)
    
    
    def calculate_age(self, dob):
        if isinstance(dob, datetime):
            dob_date = dob  # Already a datetime object
        elif isinstance(dob, str):
            dob_date = datetime.strptime(dob, "%Y-%m-%dT%H:%M:%S.%f")
        else:
            raise ValueError("Invalid type for 'dob'. Must be a string or datetime object.")
    
        today = datetime.now()
        return today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
    
    
    def validate_candidate_details(self, candidate: dict, required_fields: dict):
        """
        Validates candidate details and assigns default values if fields are missing.
    
        Args:
            candidate (dict): Candidate data.
            required_fields (dict): Dictionary of required fields with their default values.
    
        Returns:
            dict: Validated candidate details with default values if missing.
        """
        validated_details = {}
        for field, default_value in required_fields.items():
            if not candidate.get(field):
                validated_details[field] = default_value
            else:
                validated_details[field] = candidate.get(field)
    
        return validated_details
    
    
    def JobService(self, request: JobFilterRequest):
        job = self.job_collection.find_one({"Job Id": int(request.job_id)})
        
        if not job:
            raise ValueError(f"No Job found with Job ID: {request.job_id}")
        
        required_skills = job.get("required_skills", [])
        
        if not required_skills:
            raise ValueError(f"No Required Skills found with Job ID: {request.job_id}")
            
        query = {}
        query = {
            "country": request.Country,
            "location": request.Location,
            "experience": {"$gte": request.Experience},
            "sector": request.Sector,
            "gender": {"$in": ["both", request.Gender]},
            "age": {"$gte": request.Age}
        }
        
        candidates = self.candidate_collection.find(query)

        if not candidates:
            raise ValueError(f"No candidate matched")
            
        job_vector = self.compute_vector([self.normalize_token(skill) for skill in required_skills], self.word2vec_model.wv)
        
        matched_candidates = []
        
        for candidate in candidates:
            candidate_skills = candidate.get("skills", [])
            
            if not candidate_skills:
                continue  # Skip candidates with no skills

            candidate_vector = self.compute_vector([self.normalize_token(skill) for skill in candidate_skills], self.word2vec_model.wv)
            similarity = cosine_similarity([job_vector], [candidate_vector])[0][0]

            # Include only _id and can_id in the response
            matched_candidates.append({
                "_id": str(candidate["_id"]),  # Convert ObjectId to string
                "can_id": candidate.get("can_id"),
                "similarity": similarity  # Store similarity for sorting
            })

        # Sort by similarity in descending order
        matched_candidates.sort(key=lambda x: x["similarity"], reverse=True)

        # Keep only the top 10 candidates
        top_candidates = matched_candidates[:10]

        # Remove the similarity field from the output
        for candidate in top_candidates:
            del candidate["similarity"]

        return {
            "matched_candidates_count": len(top_candidates),
            "matched_candidates": top_candidates
        }
        
        
    def CandidateServices(self, request: CandidateFilterRequest):
        
        can = self.candidate_collection.find_one({"user_id": str(request.User_id)})
        
        if not can:
            raise ValueError(f"No candidate found with Candidate ID: {request.User_id}")
        
        
        skills = can.get("required_skills", [])
        
        query = {}
        if request:
            query = {
                "country": request.Country,
                "location": request.Location,
                "experience": {"$gte": request.Experience},
                "sector": request.Sector,
                "preference": {"$in": ["both", request.Gender]},
                "age_limit": {"$gte": request.Age}
            }
    
        
        # Convert skills and certification to lowercase for matching
        candidate_skills = [self.normalize_token(skill) for skill in skills]
        
        # Compute vector for the candidate's skills and certification
        candidate_skills_vector = self.compute_vector(candidate_skills, self.word2vec_model.wv)
        
        # Filter jobs based on gender and experience
        jobs = self.job_collection.find(query)

    
        if not jobs:
            raise ValueError(f"No job matched")
        
        # List to store matched jobs
        matched_jobs = []

        for job in jobs:
            job_skills = job.get('skills', [])
            job_skills_lower = [self.normalize_token(skill) for skill in job_skills]
        
            # Compute vector for the job's required skills
            job_vector = self.compute_vector(job_skills_lower, self.word2vec_model.wv)

            # Compute cosine similarity between the job and the candidate vectors
            similarity = cosine_similarity([job_vector], [candidate_skills_vector])[0][0]

            # Add job to the matched list if similarity is above a certain threshold (e.g., 0.5)
            if similarity > 0:
                matched_jobs.append({
                    "_id": str(job["_id"]),  # Return the job document _id
                    "job_id": job.get("ob Id"),  # Return the job's Job Id
                    "similarity": similarity  # Store similarity for sorting
                })

        # Sort by similarity in descending order
        matched_jobs.sort(key=lambda x: x["similarity"], reverse=True)

        # Keep only the top 10 jobs
        top_jobs = matched_jobs[:10]

        # Remove the similarity field from the output
        for job in top_jobs:
            del job["similarity"]

        return {
            "matched_jobs_count": len(top_jobs),
            "matched_jobs": top_jobs
        }
        
    # The function for the summarizing the text
    # def Summarizer(self, resume_text):
    #     summary = self.summarizer(resume_text, max_length=75, min_length=30, do_sample=False)
    #     return summary[0]['summary_text']

    # Test with a sample resume    
    def Extract(self, text, threshold):
        doc = self.nlp(text)
        phrases = [chunk.text for chunk in doc.noun_chunks]

        # Generate TF-IDF vectors for the input phrases
        phrase_vectors = self.vectorizer.transform(phrases)

        matched_skills = []
        mtch_list = []

        for i, phrase in enumerate(phrases):
            # Compute cosine similarity between the current phrase and all TF-IDF skills
            similarities = cosine_similarity(phrase_vectors[i], self.TFIDF_skills).flatten()

            # Find the best match
            best_idx = np.argmax(similarities)
            best_score = similarities[best_idx]
            
            if best_score >= threshold:
                best_surface_word = self.SurfaceForm[best_idx]
                skill_id = self.SurfaceFrom_ID[best_surface_word]
                skill = self.Skills_ID[skill_id]
                matched_skills.append((phrase, skill, best_surface_word, best_score))
                mtch_list.append(skill)

        return mtch_list

    
    def extract_text_from_google_drive(self, drive_link):
        
        # Extract the file ID from the Google Drive link
        file_id = drive_link.split("/d/")[1].split("/view")[0]
        download_url = f"https://drive.google.com/uc?id={file_id}&export=download"
    
        # Download the PDF
        response = requests.get(download_url)
        if response.status_code == 200:
            with open("downloaded.pdf", "wb") as file:
                file.write(response.content)
        else:
            raise ValueError("Failed to download the PDF. Check the link or permissions.")
    
        # Extract text from the PDF using PyPDF2
        reader = PdfReader("downloaded.pdf")
        extracted_text = ""
        for page in reader.pages:
            extracted_text += page.extract_text()  # Extract text page by page

        if not extracted_text.strip():
            raise ValueError("No text found in the PDF.")
    
        return extracted_text
    
    
    def CandidateSkills(self, request: CandidateSkillsRequest):
        
        resume = self.resume_collection.find_one({"User ID": request.User_id})
        
        if not resume:
            raise ValueError(f"No Resume found with User ID: {request.User_id}")
        try:
            file_path = resume.get("file")
        except:
            raise ValueError("Error in extracting the resume")
        
        text = self.extract_text_from_google_drive(file_path)
        
        return list(set(self.Extract(text, 0.9)))
        
    
    def JobSkills(self, request: JobSkillsRequest):
        
        job = self.job_collection.find_one({"Job Id": int(request.Job_id)})
        
        description = job.get("Job Description", " ")
        
        if not description:
            raise ValueError(f"There is no description for the Job_id {request.Job_id}")
        
        return list(set(self.Extract(description, 0.9)))
    
    
        
    # def Candidate_resume(self, request: CandidateSkillsRequest):
        
    #     can = self.candidate_collection.find_one({"user_id": str(request.User_id)})
        
    #     if not can:
    #         raise ValueError(f"No candidate found with Candidate ID: {request.User_id}")
        
    #     description = can.get("description", " ")
        
    #     if not description:
    #         raise ValueError(f"There is no description in this {request.User_id}")
        
    #     return self.summarizer(description)