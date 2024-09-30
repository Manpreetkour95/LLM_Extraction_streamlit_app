import logging
import requests
import streamlit as st

# Set up logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Set page title
st.title("💬 PDF QA")

# Initialize session state variables
if 'file_uploaded' not in st.session_state:
    st.session_state['file_uploaded'] = False

if 'summary' not in st.session_state:
    st.session_state['summary'] = ''

# Create a file uploader in the sidebar
st.sidebar.title("Upload a PDF file")
uploaded_file = st.sidebar.file_uploader(
    label="Choose a file", type="pdf", accept_multiple_files=False
)

if uploaded_file is not None and not st.session_state['file_uploaded']:
    # Send the file to the API's '/upload' endpoint
    with st.spinner('Processing the uploaded PDF file...'):
        files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        try:
            response = requests.post('http://localhost:5000/upload', files=files)
            if response.status_code == 200:
                st.session_state['file_uploaded'] = True
                st.session_state['summary'] = response.text
                st.success('File uploaded and processed successfully.')
                st.write('Summary of the document:')
                st.write(st.session_state['summary'])
            else:
                st.error(f'Failed to upload and process the file. Error {response.status_code}: {response.text}')
        except Exception as e:
            st.error(f'Failed to connect to the backend: {e}')

# Create a chat interface
message = st.chat_message("assistant")
message.write("Ask a question about your document.")

# Once file and question received
prompt = st.chat_input("Ask something")
if prompt:
    if st.session_state['file_uploaded']:
        # Update user with messages
        message = st.chat_message("user")
        logger.info(f"User message received: {prompt}")
        message.write(prompt)
        message = st.chat_message("assistant")
        message.write("Thinking...")

        # Send the query to the API's '/query' endpoint
        logger.info("Sending query to backend")
        json_payload = {'query': prompt}
        try:
            response = requests.post('http://localhost:5000/query', json=json_payload)
            if response.status_code == 200:
                answer = response.text
                logger.info("Showing response from backend")
                message.write(answer)
            else:
                st.error(f'Failed to get response from the backend. Error {response.status_code}: {response.text}')
        except Exception as e:
            st.error(f'Failed to connect to the backend: {e}')
    else:
        st.error('Please upload a PDF file first.')
