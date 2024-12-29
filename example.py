# # from fastapi import FastAPI, HTTPException
# # from Domain.domain import JobFilterRequest, CandidateFilterRequest, CandidateSkillsRequest
# # from Service.recommedation import RecommedationService

# # recommendation_service = RecommedationService()

# # print(recommendation_service.Extract("Laxmi Nar ayan Reddy narayann.dev laxminarayaanreddy432@gmail.com +918249903317 Bengaluru, India linkedin.com/naRayann github.com/2narayanan7 stackoverflow.com narraann experience SDE 1, Nymble •Currently, responsible for maintaining two apps that are integrated with a cooking robot. It utilizes method and event channels to interact seamlessly with the robot. •Worked on performance optimization, by analyzing (DevTools) and implementing various techniques that reduced frozen frames from 66% to 35%. •Following TDD (Test-Driven Development) with unit, widget, and bloc testing, refactored code for testability, and also contributing to internal and admin tools using Flutter Web. SDE intern, Caravel •Contributed to and maintained an ed-tech app and worked on River Pod (state management), Razor Pay (payment), Integrated 15+ Queries (GraphQL), Sync fusion (chat, gauges), and integrated Authorization flow, v2 of the StockDaddy app has 100k+ downloads Technical Skills Languages: C++, Dart, JavaScript Libraries: Flutter, React, Node, Express, MUIFamiliar with: Go, Fiber, Mongo Db, Redis Others: Firebase, Linux, Git, Docker, Figma Projects Extension Enabler •A Flutter Package (CLI App) that enables the Flutter web app as a Chromium-based extension with simple commands ", 0.9))


# from transformers import pipeline

# # Download and save the summarization model locally
# def download_model():
#     summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
#     summarizer.save_pretrained("local_summarizer")

import pymongo
import gridfs


mongo_uri = "mongodb+srv://tm026575:ansu2003@internovacluster.byibt.mongodb.net/?retryWrites=true&w=majority&appName=internovaCluster"
client = pymongo.MongoClient(mongo_uri)
db = client["internova_profile"]
collection = db['resume']      
fs = gridfs.GridFS(db)

# Sample data
user_id = "CAND00016"
pdf_file_path = "Resume-Raghabendra Sahu.pdf"  # Path to your PDF file

# Store PDF in GridFS
with open(pdf_file_path, "rb") as pdf_file:
    pdf_id = fs.put(pdf_file, filename="Resume-Raghabendra Sahu.pdf")

# Create the document
document = {
    "User_id": user_id,
    "Resume": pdf_id  # Reference to the PDF stored in GridFS
}

# Insert the document into MongoDB
collection.insert_one(document)

print("Document uploaded successfully!")
