import openai
import chromadb
from flask import Flask, request, Response
from chat_doc_f import get_text, get_images, save_images, create_embeddings, create_all_embeddings, create_collection, retrieve_chunk, generate_summary, encode_image, generate_response

import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PDF_FOLDER = os.path.join(UPLOAD_FOLDER, 'pdf_file')
PDF_IMAGES_FOLDER = os.path.join(UPLOAD_FOLDER, 'pdf_images')
CHROMA_EMBEDDINGS_FOLDER = os.path.join(UPLOAD_FOLDER, 'chroma_embeddings')

# Create directories if they do not exist
os.makedirs(PDF_FOLDER, exist_ok=True)
os.makedirs(PDF_IMAGES_FOLDER, exist_ok=True)
os.makedirs(CHROMA_EMBEDDINGS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PDF_FOLDER'] = PDF_FOLDER
app.config['PDF_IMAGES_FOLDER'] = PDF_IMAGES_FOLDER
app.config['CHROMA_EMBEDDINGS_FOLDER'] = CHROMA_EMBEDDINGS_FOLDER

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return Response('No file part in the request', status=400)
    file = request.files['file']
    if file.filename == '':
        return Response('No selected file', status=400)
    if file:
        document_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(document_path)
        openai_api_key = os.environ.get('OPENAI_API_KEY')

        client_openai=openai.OpenAI(api_key=openai_api_key)
        #client_cdb = chromadb.Client()
        client_cdb = chromadb.PersistentClient(path=app.config['CHROMA_EMBEDDINGS_FOLDER'])
        col_name='doc1'
        text_list=get_text(document_path)
        images=get_images(document_path)
        save_images(images, app.config['PDF_IMAGES_FOLDER'])
        embeddings_list=create_all_embeddings(client_openai,text_list)
        create_collection(client_cdb,embeddings_list,text_list,col_name)
        summary=generate_summary(client_openai,text_list)
        
        return Response(summary, mimetype='text/plain')
    
    
@app.route('/query', methods=['POST'])

def query():
    data = request.get_json()
    if 'query' not in data:
        return Response('No query found in the request', status=400)
    query = data['query']
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    client_openai=openai.OpenAI(api_key=openai_api_key)
    client_cdb = chromadb.PersistentClient(path=app.config['CHROMA_EMBEDDINGS_FOLDER'])
    col_name='doc1'
    match_results=retrieve_chunk(client_cdb,client_openai, col_name, query, k=1)
    match_page_list=[int(pageno) for pageno in match_results['ids'][0]]
    retrieved_chunks=[text for text in match_results['ids'][0]]
    base_path = app.config['PDF_IMAGES_FOLDER']
    image_paths = [f'{base_path}\\image_{i}.png' for i in match_page_list]
    response = generate_response(client_openai, retrieved_chunks, query, image_paths)
    return Response(response, mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True,use_reloader=False)