# %% Agent_orchestrator
# ##### Libraries

# %%
import base64
import json
import requests
import os
import pandas as pd
import logging
import requests
import Agent_memory 
import lancedb
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Literal, List
from dotenv import load_dotenv
import time
from openai._exceptions import BadRequestError
import smtplib
from email.message import EmailMessage
import seaborn as sns
import matplotlib.pyplot as plt
import warnings
import utils.ReportFiles as rf
warnings.filterwarnings("ignore")

USE_AZURE=False   #switch this off for local runs
# %% [markdown]
# ##### General parameters and configurations

# %%
report_metrics_file = "report_metrics.csv"
reports_dir = "reports"
memory_file = "memory.json"
tools_schema = "tools_schema.json"

header = ['Datetime_request', 'Input_prompt', 'Total_time_request',  'Step' , 'Tool', 'Success', 'Latency', 'Confidence', 'Tokens', 'Calls_API', 'Response']

# Set up logging configuration
logging.basicConfig(
    filename="application.log",                 
    filemode="w",
    level=logging.INFO,
    format="\n%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True    
    
)
logger = logging.getLogger(__name__)

# Setup LLM 
# Load environment variables
load_dotenv()
# Initialize OpenAI client

if USE_AZURE:
    client = OpenAI(
    api_key=os.getenv("AZURE_FDRY_KEY"),
    base_url=os.getenv("AZURE_FDRY_ENDPOINT").rstrip("/") + "/openai/v1/"
    )

    # In Azure: model == deployment name
    model = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
    model_tools = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")

    # Embedding deployment for RAG
    embed_model = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT")
else:
    client = OpenAI()
    model = "gpt-4o-mini"
    model_tools = "gpt-4"


# %% [markdown]
# ##### Tools schema load

# %%
# Load the tools structure from file
with open(tools_schema, "r", encoding="utf-8") as f:
    tools = json.load(f)


# %% [markdown]
# #### Memory functions 


def creative_reaction_process_request(
    headline: str,
    personas_json: str,
    image_bytes: bytes,
    image_mime: str = "image/png"
) -> str:
    """
    Entry point for Part-2 Creative Testing flow.
    """
    orchestrator = Orchestrator()
    return orchestrator.process_creative_reaction(
        headline=headline,
        personas_json=personas_json,
        image_bytes=image_bytes,
        image_mime=image_mime
    )

# %%
def get_agent_memory():
    """Load the agent memory from the file and return the recent messages."""
    try:    
        memory = Agent_memory.load_memory_from_file(memory_file)  
        return memory.get_recent_messages()
    except Exception as e:
        logger.error(f"Error loading the memory: {e}")
        return None

def clean_agent_memory():
    """Clear the agent memory file."""
    Agent_memory.clear_memory_file(memory_file)
    return 

# Create the memory file
memory = Agent_memory.Memory()
Agent_memory.save_memory_to_file(memory_file, memory)

# %% [markdown]
# ##### Functions/Tools called by the Agent

# %%
def _convert_dataframe_to_json(df, message_if_none):
    """Convert a DataFrame to JSON format."""
    if df is None or df.empty:
        return {"temperature": 0.0, "response": message_if_none}
    return df.to_json(orient='records')

def send_email_notification(to: str, subject: str, body: str):
    """Send an email notification."""
    sender_email = os.getenv("SENDER_EMAIL")
    password = os.getenv("SENDER_PASSWORD")
    to = os.getenv("RECEIVER_EMAIL")

    msg = EmailMessage()
    msg["From"] = sender_email
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, password)
            smtp.send_message(msg)
        logger.info("Email sent successfully")
        return {"action": "Email sent", "to": to, "subject": subject, "body": body}
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return {"error": str(e), "action": "Email failed"}

def call_API(endpoint: str, method: str, title: str, body: str, userId: int):
    """Call an external API."""
    payload = {
        "title": title,
        "body": body,
        "userId": userId
    }

    try:
        if method.upper() == "POST":
            response = requests.post(endpoint, json=payload)
        elif method.upper() == "GET":
            response = requests.get(endpoint, params=payload)
        else:
            raise ValueError("Unsupported method: use 'GET' or 'POST'")

        response.raise_for_status()
        logger.info("API called successfully")
        return {
            "action": "API called",
            "endpoint": endpoint,
            "method": method,
            "response_id": response.json().get("id", None),
            **payload
        }
    except Exception as e:
        logger.error(f"Error calling API: {e}")
        return {"error": str(e), "action": "API call failed"}  


# %% [markdown]
# ##### Request classes

# %%
class GeneralFlowRequestType(BaseModel):
    """Router LLM call: Determine the step of the initial request according user input or prompt"""

    request_type: Literal["analyze_test_results", "apply_action", "response_question", "other"] = Field(
        description="Step or process to start the flow of the agent"
    )
    confidence_score: float = Field(description="Confidence score between 0 and 1")


class RequestAction(BaseModel):
    """Router LLM call: Determine the action to apply according user input or prompt"""

    request_type: Literal["call_API", "send_email_notification",  "other"] = Field(
        description="Type of detection request being made"
    )
    confidence_score: float = Field(description="Confidence score between 0 and 1")    

class EmailRequestType(BaseModel):
    """Details for calling the function to send an email notification"""

    to: str = Field(description="Destination email address")
    subject: str = Field(description="Subject of the email")
    body: str =  Field(description="Body of the email")
    confidence_score: float = Field(description="Confidence score between 0 and 1")

class APIRequestType(BaseModel):
    """Details for calling the function to call an API"""

    endpoint: str  = Field(description="Endpoint of the API called")
    method: Literal["GET", "POST"] = Field(description="HTTP method used to call the API")  
    title: str = Field(description="Title of the API called")
    body: str = Field(description="Body of the API called")
    userId: int = Field(description="User ID of the API called")
    confidence_score: float = Field(description="Confidence score between 0 and 1")



# %% [markdown]
# #### Response classes

# %%
class InvestigationResponse(BaseModel):    
    """Response model for a result in a investigation search"""    

    source: str = Field(description="Source of information about the medical results") 
    title: str = Field(description="Title of the information") 
    text: str = Field(description="Detail about the medical results in the investigation") 
    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(description="User-friendly response message")
    next_step: str = Field(description="Next step to take after get investigation")
    tokens: int = Field(description="Number of tokens used in the request")
    confidence_score: float = Field(description="Confidence score between 0 and 1")


class ActionResponse(BaseModel):
    """Response model for an action applied"""  
    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(description="User-friendly response message")  
    next_step: str = Field(description="Next step to take after the action") 
    tokens: int = Field(description="Number of tokens used in the request")
    confidence_score: float = Field(description="Confidence score between 0 and 1")



# %% [markdown]
# ##### Prompts definition

# %%

SYNTHESIZED_PROMPT = """
You are an agent who helps patients to explain medical concepts in a friendly and positive way. 
You have to summarize the below information and provide a clear and concise response to the user.

 {investigation_result}

"""

#SYNTHESIZED_PROMPT =
"""
You are an agent who helps patients analyze the results of their medical tests and explain, in a friendly and positive way, the results, a possible action plan, next steps, and healthy recommendations. 
You have to synthesize the information from the tools and provide a clear and concise response to the user.

investigation_result= {investigation_result},
action_result = {action_result}
confidence_score = Confidence score between 0 and 1

Return your response in this format:

1. Give the information about the result of the analysis or investigation of the medical test results.
2. Give the information about a posible plan, or suggested next steps to follow, based on the investigation. 
3. Give the information about the action applied.

"""



SUMMARY_PROMPT = """
You are an agent who helps patients analyze the results of their medical tests and explain, in a friendly and positive way, the results, a possible action plan, next steps, and healthy recommendations. 
You have to summary the information in short format, around 10 words to save the most important information for historical context.

Analysis_investigation: {investigation_result},
action_result = {action_result}
confidence_score = Confidence score between 0 and 1

Return your response in this format:

1. Give the summary of information about the result of the analysis or investigation of the medical test results.
4. Give the information about what action applied, only the action any other detail.
"""

# %% [markdown]
# #### Print functions for verification of each step

# %%
  
def print_investigation(investigation_result):    
    print("\nINVESTIGATION RESULT\n")
    print(f"Investigation Source: {investigation_result.source}")
    print(f"Investigation Title: {investigation_result.title}")
    print(f"Investigation Text: {investigation_result.text}")
    print(f"Investigation message: {investigation_result.message}")

def print_action(action_result):    
    print("\nACTION RESULT\n")
    print(f"Action Success: {action_result.success}")
    print(f"Action Message: {action_result.message}")



# %% [markdown]
# ##### Orchestrator of the Agent AI 

# %%
class Orchestrator:
    """Orchestrator class to handle the routing of the agent flow and all the functions to be called by the agent"""
    def __init__(
        self,       
    ):        
        self.sections_content = {}
        self.function_map = {       
        "send_email_notification": send_email_notification,
        "call_API": call_API
    }        
    
    def process_creative_reaction(
        self,
        headline: str,
        personas_json: str,
        image_bytes: bytes,
        image_mime: str = "image/png",
    ) -> str:
        """
        Generates reactions for:
          - 2 HCP personas (early adopter vs conservative)
          - 2 patient personas (newly diagnosed vs long-term)
        using the same creative (image + headline).
        """

        # Parse personas
        try:
            personas = json.loads(personas_json)
        except Exception as e:
            return f"Invalid personas_json. Must be JSON. Error: {e}"

        # Ensure required keys exist (fallback to defaults if missing)
        hcp_early = personas.get(
            "hcp_early",
            "Dermatologist, 8 years experience, early adopter, comfortable with new therapies, values mechanism and emerging evidence."
        )
        hcp_conservative = personas.get(
            "hcp_conservative",
            "Dermatologist, 15 years experience, conservative prescriber, skeptical of new drugs, guideline-driven, high safety/evidence threshold."
        )
        patient_new = personas.get(
            "patient_new",
            "Patient newly diagnosed with microcystic lymphatic malformation, anxious, low-to-medium health literacy, wants reassurance and next steps."
        )
        patient_long = personas.get(
            "patient_long",
            "Patient living with microcystic lymphatic malformation for 10+ years, has tried treatments, skeptical of generic education, wants specific actionable info."
        )

        persona_bundle = [
            ("HCP (Early Adopter)", hcp_early),
            ("HCP (Conservative)", hcp_conservative),
            ("Patient (Newly Diagnosed)", patient_new),
            ("Patient (Long-Term)", patient_long),
        ]

        # Encode image for vision prompt
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{image_mime};base64,{b64}"

        system = (
            "You are a pharma creative testing assistant. "
            "Your job is to predict how different personas react to educational creative (static image + headline). "
            "You must be cautious: do not invent clinical claims not supported by the creative. "
            "Focus on clarity, trust, emotional tone, skepticism triggers, and what questions the persona would ask next. "
            "Output concise, structured results."
        )

        # We ask the model to return one JSON object for all 4 personas + segment diffs
        user_instructions = {
            "task": "creative_reaction_testing",
            "headline": headline,
            "personas": [
                {"label": lbl, "persona": p} for (lbl, p) in persona_bundle
            ],
            "required_output": {
                "per_persona": {
                    "reaction_label": "one of: resonate, confuse, skepticism",
                    "why": "3-6 bullets tied to image/copy cues",
                    "questions_next": "2-4 bullets",
                    "suggested_edits": "2-4 bullets"
                },
                "segment_differences": [
                    "Compare HCP early adopter vs conservative for this creative",
                    "Compare newly diagnosed vs long-term patient for this creative"
                ]
            }
        }

        # Vision + instruction prompt
        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze this pharma educational creative for the personas provided. Return JSON only."},
                    {"type": "text", "text": json.dumps(user_instructions)},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ]

        try:
            resp = client.chat.completions.create(
                model=model,  # gpt-4o-mini default in your file (vision-capable)
                messages=messages,
                temperature=0.4,
            )
            raw = resp.choices[0].message.content
        except Exception as e:
            return f"LLM call failed: {e}"

        # Best-effort: if model returns non-JSON, wrap it
        try:
            parsed = json.loads(raw)
            return json.dumps(parsed, indent=2)
        except Exception:
            return raw

    
# Initialize LanceDB connection
    def init_RAG_db(self):
        """Initialize database connection. Returns: LanceDB table object"""
        db = lancedb.connect("data/lancedb")
        return db.open_table("docling")

    def call_function(self, name, args):
        """Calls the appropriate function based on the provided name."""
        func = self.function_map.get(name)
        if func:
            return func(**args)
        raise ValueError(f"Invalid function name: {name}")
       
    def call_tool(self, messages: List[Dict]) -> List[Dict]:  
        """Function to identify the function/tool to call based on the prompts, extract datails and parameters to add in the messages or prompt to execute and call it. Returns: The messages appending the tool call and the result of the tool call"""      
        response = client.chat.completions.create(
            model=model_tools,
            messages=messages,
            tools=tools,
        ) 
        tool_calls = response.choices[0].message.tool_calls

        if tool_calls:
            for tool_call in tool_calls:
                # Extract tool call details
                tool_call = tool_call
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                logger.info(f"Tool call: {tool_name} with args: {tool_args}")

                # Append the assistant's tool_call message
                messages.append(response.choices[0].message)

                # Call the function directly
                tool_result = self.call_function(tool_name, tool_args)          

                # Append the result of the tool call
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result)
                })

            return messages
        return None
    
    def route_orchestrator_request(self, user_input: str) -> GeneralFlowRequestType:
        """Router LLM call to determine the flow of the request"""
  
        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "Determine if this is a request to response a question or analyze information or apply an action like schedule an appointment.",
                },
                {"role": "user", "content": user_input},
            ],
            response_format=GeneralFlowRequestType,
        )
        result = completion.choices[0].message.parsed
        logger.info(
            f"Request routed route_orchestrator_request as: {result.request_type} with confidence: {result.confidence_score}"
        )
        if result:        
            return result, completion.usage.total_tokens 
        
        logging.error(f"Error routing request")
        raise ValueError(f"Failes to route the request route_orchestrator_request")
    
       
    def route_action(self, investigation_result: str) -> RequestAction:
        """Router LLM call to determine action to apply"""

        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "Determine if this is a request to an email send notification by or call an API.",
                },
                {"role": "user", "content": investigation_result},
            ],
            response_format=RequestAction,
        )
        result = completion.choices[0].message.parsed
        logger.info(
            f"Request action routed as: {result.request_type} with confidence: {result.confidence_score}"
        )
        if result:        
            return result, completion.usage.total_tokens 
        
        logging.error(f"Error routing request")
        raise ValueError(f"Failes to route the request route_orchestrator_request") 
    
    def get_RAG_context(self, query: str, table, num_results: int = 3) -> str:
        """Search the RAG database for context of the information to search in investigation"""
        results = table.search(query).limit(num_results).to_pandas()
        contexts = []

        for _, row in results.iterrows():
            # Extract metadata
            filename = row["metadata"]["filename"]
            #page_numbers = row["metadata"]["page_numbers"]
            page_numbers_str = row["metadata"].get("page_numbers")  # now: "1,2,5" or None
            title = row["metadata"]["title"]

            # Build source 
            source_parts = []
            if filename:
                source_parts.append(filename)
            if page_numbers_str:
                # Normalize spacing (optional) and show in a consistent format
                pages_display = ", ".join(p.strip() for p in str(page_numbers_str).split(",") if p.strip())
                if pages_display:
                    source_parts.append(f"p. {pages_display}")

            source = f"\nSource: {' - '.join(source_parts)}"
            if title:
                source += f"\nTitle: {title}"

            contexts.append(f"{row['text']}{source}")

        return "\n\n".join(contexts)


    def get_RAG_response(self, context, results) -> InvestigationResponse:
        """Get streaming response with the documenation found in RAG. """
        next_step = ""
        message_response = ""
        sucess = False

        system_prompt = f"""You are a helpful assistant that analyze medical test results from documents and give recommendations or next steps.
        Use only the information from the context to answer questions. If you're unsure or the context
        doesn't contain the relevant information, say so.     
        """
        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": "Find information related with " + results + " in the context" +  context },
            ],
            response_format=InvestigationResponse,
        )

        # Extract the full response content
        details = completion.choices[0].message.parsed

        if details.text and details.text != "":
            next_step=f"Apply the action indicated in the text: {details.text}" 
            message_response=f" {details.text}. Information was found in document {details.source}"   
            sucess = True      
        else:
            next_step=""
            message_response = "There is no investigation related with the results"   
            sucess = False  
                       
        return InvestigationResponse(
            message=message_response,           
            source=details.source,
            title=details.title,
            text=details.text,
            success=sucess,
            next_step=next_step,
            tokens=completion.usage.total_tokens,
            confidence_score=details.confidence_score,
        )       
            
    def handle_analyze_test_results(self, results: str) -> InvestigationResponse:
        """LLM call to get the investigation, search and analysis of the medical test results"""

        # Initialize database connection
        table = self.init_RAG_db()

        context = self.get_RAG_context("Check all the information about medical questions " + results, table)

        for chunk in context.split("\n\n"): 
            # Split into text and metadata parts
            parts = chunk.split("\n")
            text = parts[0]
            metadata = {
                line.split(": ")[0]: line.split(": ")[1]
                for line in parts[1:]
                if ": " in line
            }

        response = self.get_RAG_response(context, results)   
        logger.info(f"Search completed")      
        return response
            
        
    
    def handle_send_email_notification(self, description: str) -> ActionResponse:
        """LLM call the function/tool to apply the action to send an email notification, extracing the information from the user message or prompt"""
        next_step = ""
        response_message = ""
        success = True

        messages=[
                {
                    "role": "system",
                    "content": "Send a notification about the analysis done. You have to call the function send_email_notification.",
                },
                {"role": "user", "content": "Please send an email to email@notificacion.com explaing to the patient the analysis about the tests results, describe in a positive way the results and the plan to apply" + description}
            ]
                
        messages = self.call_tool(messages)
        
        completion = client.beta.chat.completions.parse(
            model=model,
            messages=messages,
            response_format=EmailRequestType,
        )    

        details = completion.choices[0].message.parsed

        if details.subject and details.subject != "":
            next_step=""
            response_message=f"Email send to {details.to}, subject {details.subject}. Text {details.body}"    
            success = True       
        else:
            next_step=""
            response_message="Email not send. Please check the information."   
            success = False         
            
        logger.info(f"Send an email notification: {details.model_dump_json(indent=2)}")
        
        return ActionResponse(
            message=response_message,         
            success=success,
            next_step=next_step,     
            tokens=completion.usage.total_tokens, 
            confidence_score=details.confidence_score,       
        )       
    
    def handle_call_API(self, description: str) -> ActionResponse:
        """LLM call the function/tool to apply the action to call an API, extracing the information from the user message or prompt"""
        next_step = ""
        response_message = ""
        success = True

        messages=[
                {
                    "role": "system",
                    "content": "Call a public API. 1. You have to call the function call_API. ",
                },
                {"role": "user", "content": "Call the API https://jsonplaceholder.typicode.com/posts, method POST and payload parameters in the description " + description}
            ]
                
        messages = self.call_tool(messages)
        
        completion = client.beta.chat.completions.parse(
            model=model,
            messages=messages,
            response_format=APIRequestType,
        )    

        details = completion.choices[0].message.parsed

        if details.endpoint and details.endpoint != "":
            next_step="Send an email with the notification that the API called executed sucesfully" + description
            response_message=f"API call {details.endpoint}, method {details.method}. Title {details.title}. Body {details.body}. User ID {details.userId}"
            success = True            
        else:
            next_step="Send an email with the notification that the API called was not executed" + description
            response_message="Call to API was no executed Please check the information."  
            success = False       
            
        logger.info(f"Call and API: {details.model_dump_json(indent=2)}")
        
        return ActionResponse(
            message=response_message,           
            success=success,
            next_step=next_step, 
            tokens=completion.usage.total_tokens, 
            confidence_score=details.confidence_score,            
        )      

    def handle_synthesized_response(self, investigation_result: str, action_result: str) -> str:
        """LLM call the function/tool to consolidate the information for user response"""

        
        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": SYNTHESIZED_PROMPT.format(
                        investigation_result=investigation_result.text,
                        action_result = action_result,
                       
                    ),
                }
            ],            
        )
           
        details= completion.choices[0].message.content

        history_response, history_tokens = self.handle_summary_history_response(investigation_result, action_result)

        memory = Agent_memory.load_memory_from_file(memory_file)  
        memory.add_message("assistant", history_response)
        Agent_memory.save_memory_to_file(memory_file, memory)

        logger.info(f"Executed synthesized response")

        print("Answer ", details)

        return details, completion.usage.total_tokens + history_tokens
    
    def handle_summary_history_response(self, investigation_result: str, action_result: str) -> str:
        """LLM call the function/tool to summary the information for historical context"""

        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": SUMMARY_PROMPT.format(
                        investigation_result=investigation_result,
                        action_result = action_result,
                       
                    ),
                }
            ],            
        )
           
        details= completion.choices[0].message.content

        return details, completion.usage.total_tokens
    
    def apply_action(self, investigation_result: str) -> Optional[ActionResponse]:
        """Function implementing the process workflow for the type of action to apply according to user input or prompt"""
        logger.info("Processing validating type of action")

        # Route the request
        route_result, tokens = self.route_action(investigation_result)


        # Check confidence threshold
        if route_result.confidence_score < 0.7:
            logger.warning(f"Low confidence score: {route_result.confidence_score}")
            return None
        
        # Route to appropriate handler
        if route_result.request_type == "send_email_notification":
            return self.handle_send_email_notification(investigation_result), tokens
        elif route_result.request_type == "call_API":
            return self.handle_call_API(investigation_result), tokens
        else:
            return self.handle_send_email_notification(investigation_result), tokens
        

    def process_agent(self, input: str) -> Dict:
        """Main function implementing the entire process routing workflow following flexible flow depend of the user message or prompt"""
       
        investigation_result = None
        action_result = None        
        
        datetime_request = time.time()   
        input_prompt = input
        latency = 0
        tokens = 0
        step = ""
        tool = ""
        success = False          
        confidence = 0
        calls_api = 0
        response = ""
        report_metrics = rf.ReportFiles()
        df_metrics = report_metrics.create_report_metrics()

        past_context = get_agent_memory()  
        # Extract and concatenate only the content field
        past_content = " ".join([msg["content"] for msg in past_context])
        past_content = past_content.replace("\n", " ")   
        past_content = past_content.replace("\r", " ")  
        past_content = past_content.replace("  ", " ")        

        if past_content.strip() != "":
            past_content = ". This is the context of the previous or historical request to analyze results:" + past_content
        
       
        try:       
            logger.info("Processing general flow")
            start_time = time.time()                        
        
            # Route the request
            route_result, tokens = self.route_orchestrator_request(input)

            print(f"Routed to: {route_result.request_type} with confidence {route_result.confidence_score}")

            if route_result == None or route_result.request_type == "other":
                logger.warning("Request classified as other")
                return
        
            # Check confidence threshold
            if route_result.confidence_score < 0.7:
                logger.warning(f"Low confidence score: {route_result.confidence_score}")
                print("Low confidence score")
                return None
            
            input = input + " " + route_result.request_type + past_content
            step = route_result.request_type
            print(f"Input for processing: {input}")

            if route_result.request_type == "analyze_test_results" or route_result.request_type == "response_question":     
                investigation_result = self.handle_analyze_test_results(input)
                print_investigation("Investigation " , investigation_result)
                if investigation_result:                     
                    logger.info(f"Test results {investigation_result.message}")
                    print_investigation(investigation_result)
                    input = investigation_result.next_step
                    success = investigation_result.success
                    confidence = investigation_result.confidence_score
                    tokens += investigation_result.tokens
                    response = investigation_result.message

            if route_result.request_type == "apply_action":  
                action_result, tokens_router = self.apply_action(input)                    
                if action_result:                        
                    logger.info(f"Apply action {action_result.message}")
                    print_action(action_result)
                    input = action_result.next_step  
                    success = action_result.success
                    confidence = action_result.confidence_score
                    tokens += action_result.tokens + tokens_router
                    response = action_result.message

        except (ValueError, TypeError, BadRequestError) as e:
            logger.info("Error in processing the request in agent " + str(e))
            success = False
            confidence = 0
            tokens += 0
            response = "Error in processing the request " + str(e)
            
        # Check and save metrics in the report file
        end_time = time.time()             
        latency = end_time - start_time   
        report_metrics.add_report_metrics(df_metrics, datetime_request, input_prompt, step, tool, "", success, latency, confidence, tokens, calls_api, response) 

        start_time = time.time()  
        # Call the synthesizer to consolidate the information for user response            
        synthesized_result, tokens_synthesized = self.handle_synthesized_response(investigation_result, action_result)
        
        end_time = time.time()
        latency = end_time - start_time       
        # Add the metrics for the synthesized result
        report_metrics.add_report_metrics(df_metrics, datetime_request, input_prompt, "synthesized_result", tool, "", True, latency, 1, tokens_synthesized, calls_api, synthesized_result) 

        total_time_request = time.time() - datetime_request

        report_metrics.update_total_time(df_metrics,total_time_request)
        # Save the report file with the metrics
        report_metrics.save_file_df(df_metrics) 

        logger.info(f"Executed agent with total time {total_time_request} seconds and {tokens} tokens")            

        return synthesized_result  

    

# %% [markdown]
# ##### Test 

# %%
def agent_process_request(prompt_text: str,
    file_content: str = None) -> str:

    clean_agent_memory()
    input = prompt_text 
    
    if file_content:        
        input += " analyze also the below content attached " + file_content
    orchestrator = Orchestrator()
    return orchestrator.process_agent(
        input=input

    )


