
import os
import pymupdf
import base64

def get_text(document_path):
    """
    Extract text from each page of a PDF document.

    Args:
    - document_path (str): Path to the PDF document.

    Returns:
    - list: List of text extracted from each page of the PDF.
    """
    all_pages_text = []
    pdf_document = pymupdf.open(document_path)
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text = page.get_text()
        all_pages_text.append(text)
    pdf_document.close()
    return all_pages_text


def get_images(document_path):
    """
    Extract images from each page of a PDF document.

    Args:
    - document_path (str): Path to the PDF document.

    Returns:
    - list: List of image bytes extracted from each page of the PDF.
    """
    pdf_document = pymupdf.open(document_path)
    images = []
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap()
        image_bytes = pix.tobytes("png")
        images.append(image_bytes)
    pdf_document.close()
    return images

def save_images(images, output_folder):
    """
    Save extracted images to the specified output folder.

    Args:
    - images (list): List of image bytes to save.
    - output_folder (str): Path to the output folder where images will be saved.

    Returns:
    - list: List of paths to saved images.
    """
    image_paths = []
    for i, image_bytes in enumerate(images):
        image_path = os.path.join(output_folder, f'image_{i}.png')  # Use 'png' as the extension
        with open(image_path, 'wb') as image_file:
            image_file.write(image_bytes)
        image_paths.append(image_path)
    return image_paths

def create_embeddings(client_openai,text):
    """
    Create embeddings for a given text using OpenAI API.

    Args:
    - client_openai (OpenAI Client): Instance of OpenAI client.
    - text (str): Text for which embeddings are to be created.

    Returns:
    - str: Embedding generated for the text.
    """
    response = client_openai.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def create_all_embeddings(client_openai,text_list):
    """
    Create embeddings for a list of text chunks using OpenAI API.

    Args:
    - client_openai (OpenAI Client): Instance of OpenAI client.
    - text_list (list): List of text chunks for which embeddings are to be created.

    Returns:
    - list: List of embeddings generated for each text chunk.
    """
    return [create_embeddings(client_openai,chunk) for chunk in text_list]

def create_collection(client_cdb,embeddings_list,text_list,col_name):
    """
    Create a collection in ChromaDB and add documents with embeddings.

    Args:
    - client_cdb (ChromaDB Client): Instance of ChromaDB client.
    - embeddings_list (list): List of embeddings corresponding to each document.
    - text_list (list): List of documents/texts to be added to the collection.
    - col_name (str): Name of the collection to be created or retrieved.

    Returns:
    - None
    """
    collection = client_cdb.get_or_create_collection(col_name)
    for i, embedding in enumerate(embeddings_list):
        collection.add(
            documents=[text_list[i]],
            embeddings=[embedding],
            ids=[str(i)]
        )
    #return collection

def retrieve_chunk(client_cdb,client_openai, col_name, query, k=5):
    """
    Retrieve matching chunks of text from the collection based on a query.

    Args:
    - client_cdb (ChromaDB Client): Instance of ChromaDB client.
    - client_openai (OpenAI Client): Instance of OpenAI client.
    - col_name (str): Name of the collection to query.
    - query (str): Query to search for in the collection.
    - k (int, optional): Number of results to retrieve. Defaults to 10.

    Returns:
    - dict: Results containing matching chunks of text.
    """

    collection = client_cdb.get_or_create_collection(col_name)

    query_embedding = create_embeddings(client_openai,query)
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k
    )
    #return [doc for doc in results['documents'][0]]
    return results

def generate_summary(client_openai,text_list):
    """
    Generate a summary of the document using OpenAI API.

    Args:
    - client_openai (OpenAI Client): Instance of OpenAI client.
    - text_list (list): List of text chunks representing the document.

    Returns:
    - str: Generated summary of the document.
    """

    input_text=''
    for text in text_list[0:4]:
        input_text=input_text+'/n/n'+text

    prompt_text = 'Generate summary of the document'
    response = client_openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "user",
                "content": prompt_text + input_text
            }
        ],
        temperature=0,
        max_tokens=200,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response.choices[0].message.content

def encode_image(image_path):
    """
    Encode an image to base64 format.

    Args:
    - image_path (str): Path to the image file.

    Returns:
    - str: Base64 encoded representation of the image.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')



def generate_response_text(client_openai, retrieved_chunks, query):
    """
    Generate a summary of the document using OpenAI API.

    Args:
    - client_openai (OpenAI Client): Instance of OpenAI client.
    - text_list (list): List of text chunks representing the document.

    Returns:
    - str: Generated summary of the document.
    """
    context = " ".join(retrieved_chunks)

    input_text = f"{context}\n\nUser: {query}\nAI:"

    prompt_text = """"Use the following pieces of context to answer the question at the end.
       If you don't know the answer, respond with {please elaborate your question; it seems unrelated to the context}
       In many documents heading is mentioned on the top of the page please refer to the heading while finding the
       relevant context."
       """
    response = client_openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {
                "role": "user",
                "content": prompt_text + input_text
            }
        ],
        temperature=0,
        max_tokens=200,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    #return response
    return response.choices[0].message.content

def generate_response(client_openai, retrieved_chunks, query, image_paths):
    """
    Generate a response based on retrieved chunks, query, and image paths using OpenAI API.

    Args:
    - client_openai (OpenAI Client): Instance of OpenAI client.
    - retrieved_chunks (list): List of retrieved text chunks.
    - query (str): Query used to retrieve chunks.
    - image_paths (list): List of paths to images related to the retrieved chunks.


    Returns:
    - str: Generated response combining text and images.
    """
    #context = " ".join(retrieved_chunks)

    input_text = f"User: {query}\nAI:"

    prompt_text = """"Use the following pieces of context to answer the question at the end.
       If you don't know the answer, respond with {please elaborate your question; it seems unrelated to the context}
       In many documents heading is mentioned on the top of the page please refer to the heading while finding the
       relevant context."
       """

    # Encode all images and create image content entries
    image_contents = [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(image_path)}"}} for image_path in image_paths]

    # Combine text and images into messages
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_text + input_text},
                *image_contents
            ]
        }
    ]

    response = client_openai.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.4,
        max_tokens=200,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    #return response
    return response.choices[0].message.content
