# Pharma Creative Testing Prototype

This repository contains a lightweight end-to-end prototype for **synthetic testing of pharma educational creative** (static images + messaging) across different audience segments (patients and HCPs).

The goal is **directional accuracy and reasoning transparency**, not production polish.

---

## What This Does

Given:
- a **persona** (e.g., early-adopter physician, conservative prescriber, newly diagnosed patient),
- and a **piece of creative** (image + headline),

the system simulates how different audiences would react:
- Does the creative **resonate**, **confuse**, or **trigger skepticism**?
- **Why** does it produce that reaction (visual + textual drivers)?
- How does the reaction **differ by segment**?

The prototype demonstrates:
- persona-conditioned reasoning,
- multimodal (image + text) evaluation,
- explainable outputs suitable for pre-launch creative testing.

---

## Architecture Overview
UI (Vite + React)
|
|  multipart/form-data (image + text)
v
FastAPI Backend
|
|  Prompting + optional retrieval (RAG-ready)
v
LLM (vision-capable)

## Requirements

- Python 3.9+
- Node.js 18+
- An OpenAI API key with vision model access



### packages (main) - minor installation required post this 

pip install fastapi uvicorn pydantic pydantic-settings python-dotenv orjson \
  torch torchvision transformers tokenizers accelerate huggingface-hub safetensors \
  openai tiktoken \
  docling docling-core docling-parse docling-ibm-models pypdfium2 rapidocr \
  lancedb \
  numpy pandas scipy pillow opencv-python seaborn azure-search-documents azure-core


## Setup Instructions
set USE_AZURE=True /False in Agent_orchestrator.py to use azure or local runs
 
Install Uvicorn

uvicorn Agent_API:app --reload    
npm install
npm run dev 


## open browser:
http://localhost:5173


## example personas
{
  "hcp_early": "Dermatologist, 8 years experience, early adopter, comfortable with new therapies",
  "hcp_conservative": "Dermatologist, 15 years experience, conservative prescriber, guideline-driven",
  "patient_new": "Newly diagnosed patient, anxious, wants reassurance and next steps",
  "patient_long": "Long-term patient, skeptical of generic education, wants specifics"
}



## run in CMD
curl -v -X POST "http://127.0.0.1:8000/creative/react" \
  -F "headline=test" \
  -F 'personas_json={"hcp_early":"a","hcp_conservative":"b","patient_new":"c","patient_long":"d"}' \
  -F "image=@/Users/praga/sola_labs_demo/creative1.png"

## Expcted reply:

{"answer":"```json\n{\n  \"task\": \"creative_reaction_testing\",\n  \"headline\": \"test\",\n  \"personas\": [\n    {\n      \"label\": \"HCP (Early Adopter)\",\n      \"reaction_label\": \"resonate\",\n      \"why\": [\n        \"The image depicts a modern, comfortable setting that suggests a progressive approach to healthcare.\",\n        \"The interaction between the healthcare professional and the patient appears collaborative, which aligns with innovative practices.\",\n        \"The use of technology (tablet) indicates a forward-thinking approach, appealing to early adopters.\"\n      ],\n      \"questions_next\": [\n        \"What new treatments or technologies are being discussed?\",\n        \"How can I implement these practices in my own practice?\"\n      ],\n      \"suggested_edits\": [\n        \"Include specific information about innovative treatments or technologies.\",\n        \"Add a call-to-action for further engagement or learning.\"\n      ]\n    },\n    {\n      \"label\": \"HCP (Conservative)\",\n      \"reaction_label\": \"skepticism\",\n      \"why\": [\n        \"The modern setting may be perceived as too casual for serious medical discussions.\",\n        \"Lack of clinical data or evidence in the image may raise doubts about the efficacy of new approaches.\",\n        \"The focus on patient comfort might overshadow the importance of clinical outcomes.\"\n      ],\n      \"questions_next\": [\n        \"What evidence supports the effectiveness of this approach?\",\n        \"How does this align with established practices?\"\n      ],\n      \"suggested_edits\": [\n        \"Incorporate data or statistics to support claims.\",\n        \"Provide a more traditional representation of the healthcare setting.\"\n      ]\n    },\n    {\n      \"label\": \"Patient (Newly Diagnosed)\",\n      \"reaction_label\": \"resonate\",\n      \"why\": [\n        \"The image conveys a sense of warmth and support, which is comforting for someone newly diagnosed.\",\n        \"The interaction suggests a focus on patient education and empowerment.\",\n        \"The modern environment may feel reassuring, indicating that they are receiving up-to-date care.\"\n      ],\n      \"questions_next\": [\n        \"What should I expect during my treatment?\",\n        \"How can I best communicate my concerns to my healthcare provider?\"\n      ],\n      \"suggested_edits\": [\n        \"Include more information about the diagnosis and treatment options.\",\n        \"Add testimonials or experiences from other patients.\"\n      ]\n    },\n    {\n      \"label\": \"Patient (Long-Term)\",\n      \"reaction_label\": \"confuse\",\n      \"why\": [\n        \"The modern setting may feel unfamiliar compared to their long-term experiences.\",\n        \"The focus on a new approach might create uncertainty about their existing treatment plan.\",\n        \"The image does not address their specific needs or concerns as a long-term patient.\"\n      ],\n      \"questions_next\": [\n        \"How does this new approach affect my current treatment?\",\n        \"Are there changes I need to be aware of in my care?\"\n      ],\n      \"suggested_edits\": [\n        \"Provide clear information on how new approaches integrate with long-term care.\",\n        \"Include references to long-term patient experiences or outcomes.\"\n      ]\n    }\n  ],\n  \"segment_differences\": [\n    \"HCP Early Adopter is likely to embrace the innovative approach, while the Conservative HCP may question its validity and prefer traditional methods.\",\n    \"Newly Diagnosed patients find reassurance in the supportive environment, while Long-Term patients may feel confused by the shift away from their established care.\"\n  ]\n}\n```"}%    


curl -v -X POST "http://127.0.0.1:8000/creative/react" \
  -F "headline=test" \
  -F 'personas_json={
  "hcp_early": "Dermatologist, 8 years experience, early adopter, comfortable with new therapies, values mechanism and emerging evidence.",
  "hcp_conservative": "Dermatologist, 15 years experience, conservative prescriber, skeptical of new drugs, guideline-driven, high safety/evidence threshold.",
  "patient_new": "Patient newly diagnosed with microcystic lymphatic malformation, anxious, low-to-medium health literacy, wants reassurance and next steps.",
  "patient_long": "Patient living with microcystic lymphatic malformation for 10+ years, has tried treatments, skeptical of generic education, wants specific actionable info."
}' \
  -F "image=@/Users/praga/sola_labs_demo/creative1.png"

## Expcted reply:

{"answer":"```json\n{\n  \"task\": \"creative_reaction_testing\",\n  \"headline\": \"test\",\n  \"personas\": [\n    {\n      \"label\": \"HCP (Early Adopter)\",\n      \"reaction_label\": \"resonate\",\n      \"why\": [\n        \"The image depicts a modern, friendly consultation environment, appealing to innovative approaches.\",\n        \"The dermatologist's attire and demeanor suggest professionalism and openness to new therapies.\",\n        \"The patient appears engaged, indicating a positive interaction that aligns with the HCP's values.\"\n      ],\n      \"questions_next\": [\n        \"What emerging evidence supports the new therapy?\",\n        \"How does this therapy work at a mechanistic level?\"\n      ],\n      \"suggested_edits\": [\n        \"Include specific data or studies related to the therapy.\",\n        \"Highlight the mechanism of action more clearly.\",\n        \"Add a call to action for further reading on emerging therapies.\"\n      ]\n    },\n    {\n      \"label\": \"HCP (Conservative)\",\n      \"reaction_label\": \"skepticism\",\n      \"why\": [\n        \"The image lacks specific clinical data or guidelines that this persona values.\",\n        \"The headline 'test' is vague and does not convey sufficient information.\",\n        \"The consultation appears too casual, which may raise concerns about the therapy's credibility.\"\n      ],\n      \"questions_next\": [\n        \"What are the safety profiles of the new therapy?\",\n        \"Are there established guidelines recommending this treatment?\"\n      ],\n      \"suggested_edits\": [\n        \"Provide clear references to clinical guidelines.\",\n        \"Include safety data and long-term outcomes.\",\n        \"Change the headline to something more informative.\"\n      ]\n    },\n    {\n      \"label\": \"Patient (Newly Diagnosed)\",\n      \"reaction_label\": \"resonate\",\n      \"why\": [\n        \"The image shows a supportive interaction, which may reassure the patient.\",\n        \"The approachable demeanor of the healthcare provider can help alleviate anxiety.\",\n        \"The setting feels safe and welcoming, making it relatable for a newly diagnosed patient.\"\n      ],\n      \"questions_next\": [\n        \"What are the next steps in my treatment?\",\n        \"How will this therapy help my condition?\"\n      ],\n      \"suggested_edits\": [\n        \"Add a brief explanation of what to expect during treatment.\",\n        \"Include testimonials or success stories from other patients.\",\n        \"Provide a clear outline of next steps after diagnosis.\"\n      ]\n    },\n    {\n      \"label\": \"Patient (Long-Term)\",\n      \"reaction_label\": \"confuse\",\n      \"why\": [\n        \"The image does not provide specific information on treatment options or advancements.\",\n        \"The headline is too generic and does not address their experience with past treatments.\",\n        \"The consultation appears too simplistic, lacking depth for a patient with extensive experience.\"\n      ],\n      \"questions_next\": [\n        \"What makes this therapy different from what I've already tried?\",\n        \"Can you provide detailed information on efficacy and side effects?\"\n      ],\n      \"suggested_edits\": [\n        \"Include specific treatment comparisons.\",\n        \"Add detailed information on the therapy's effectiveness.\",\n        \"Change the headline to reflect a more advanced understanding of the condition.\"\n      ]\n    }\n  ],\n  \"segment_differences\": [\n    \"The early adopter HCP is likely to resonate with the creative due to its modern appeal, while the conservative HCP expresses skepticism due to a lack of detailed evidence.\",\n    \"The newly diagnosed patient finds reassurance in the supportive interaction, whereas the long-term patient feels confused by the lack of specific, actionable information.\"\n  ]\n}\n```"}% 