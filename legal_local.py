from langchain_openai import ChatOpenAI
from langchain.chains import llm
from langchain_core.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from dotenv import load_dotenv
import PyPDF2
from pdfquery import PDFQuery
import torch

load_dotenv()


class LegalExpert:
    def __init__(self):

        # falcon model
        model_name = "tiiuae/falcon-11B"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.falcon_llm = pipeline("text-generation",
                                   model=model_name,
                                   tokenizer=tokenizer,
                                   torch_dtype=torch.float16,
                                   trust_remote_code=True,
                                   device_map="auto")

        print(f'Model {model_name} is set.')

    def get_system_prompt(self, language, context):
        system_prompt = """
        You are a Canadian Legal Expert.
        Under no circumstances do you give legal advice.

        You are adept at explaining the law in laymans terms, and you are able to provide context to legal questions.
        While you can add context outside of the provided context, please do not add any information that is not directly relevant to the question, or the provided context.
        You speak {language}.
        ### CONTEXT
        {context}
        ### END OF CONTEXT
        """

        return SystemMessagePromptTemplate.from_template(system_prompt)

    def run_chain(self, language, context, question):
        # Create the user and system prompts
        self.user_prompt = HumanMessagePromptTemplate.from_template('{question}')
        self.system_prompt = self.get_system_prompt(language, context)

        # Use ChatPromptTemplate to combine prompts
        self.full_prompt_template = ChatPromptTemplate.from_messages(
            [self.system_prompt, self.user_prompt]
        )

        # Get the prompt string
        prompt_value = self.full_prompt_template.invoke({'context': context, 'language': language, 'question': question})

        # Pass the prompt string to the Falcon LLM and get the response
        response = self.falcon_llm(str(prompt_value))
        return response[0]['generated_text']  # Modify to extract the text from the Falcon pipeline output

pdf_file_loc = "Legal documentation/Contract_of_PurchaseSale.pdf"

def retrieve_pdf_text(pdf_file_loc):

    pdf_file = PDFQuery(pdf_file_loc)
    pdf_file.load()
    text_elements = pdf_file.pq('LTTextLineHorizontal')
    return "".join([t.text for t in text_elements if t.text.strip() != ''])


# create a streamlit app
print("Starting Document Explainer (that does not give advice)")

machine_reader = LegalExpert()



language = input("1.French\n2.English\n")
#question = input("Ask a question? ")
question = 'what is about the document?'


# run the model
legal_response = machine_reader.run_chain(
    language=language, context=retrieve_pdf_text(pdf_file_loc), question=question
)
#Output the answer
print(f"legal_response: {legal_response}")
