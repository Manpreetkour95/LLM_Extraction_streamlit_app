import streamlit as st
import fitz
import openai
import json


# Cache the PDF text extraction to avoid reprocessing
@st.cache_data
def get_text(pdf_stream):
    all_pages_text = []
    pdf_document = fitz.open(stream=pdf_stream, filetype="pdf")
    
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text = page.get_text()
        all_pages_text.append(text)
        
    pdf_document.close()
    return all_pages_text

# Cache the PDF image extraction to avoid reprocessing
@st.cache_data
def get_images(pdf_stream):
    pdf_document = fitz.open(stream=pdf_stream, filetype="pdf")
    images = []
    
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap()
        image_bytes = pix.tobytes("png")
        images.append(image_bytes)
        
    pdf_document.close()
    return images

# Cache the OpenAI client initialization to avoid re-initialization
@st.cache_resource
def load_openai_client(api_key):
    return openai.OpenAI(api_key=api_key)

# Cache the GPT-4 response to avoid redundant API calls
@st.cache_data
def process_pdf_with_gpt(_client_openai, text):
    prompt_text='''Extract the following donation information into a JSON format with the structure:
    {
    "data": [
        {
        "donor_names_group": ["donor_1", "donor_2", ...],
        "amount_donated_by_group": ["min_amount", "max_amount"],
        "gift_type": "type_of_gift"
        },
        ...
    ]
    }
    e.g

    [
        {
            'data': [
                {
                    'donor_names_group': [
                        'Anonymous (4)', 'Family Foundation'
                    ],
                    'amount_donated_by_group': ['1000', ''],
                    'gift_type': 'Annual'
                },
                {
                    'donor_names_group': ['JD GROUP','Bill Gates'
                    ],
                    'amount_donated_by_group': ['1000', '2000'],
                    'gift_type': 'Annual'
                }
            ],
            'page':'0'
        },
        {
            'data': [
                {
                    'donor_names_group': [
                        'Anonymous'
                    ],
                    'amount_donated_by_group': ['10000', ''],
                    'gift_type': 'Annual'
                },
                {
                    'donor_names_group': ['some org'
                    ],
                    'amount_donated_by_group': ['5000', '9999'],
                    'gift_type': 'Annual'
                }
            ],
            'page':'1'

        }
    ]'''


    response = _client_openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": text + prompt_text}
        ],
        temperature=0,
        max_tokens=1000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return json.loads(response.choices[0].message.content)
