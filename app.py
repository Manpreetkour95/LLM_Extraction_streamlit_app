import streamlit as st
import os
from dotenv import load_dotenv
from io import BytesIO
from pdf_processing import get_text, get_images, process_pdf_with_gpt, load_openai_client
load_dotenv()

# Streamlit configuration
st.set_page_config(layout="wide")

# Initialize session state for current dataset and group index
if 'current_dataset' not in st.session_state:
    st.session_state.current_dataset = 0
if 'datasets' not in st.session_state:
    st.session_state.datasets = []

# Create a file uploader in the sidebar
st.sidebar.title("Upload a PDF file")
uploaded_file = st.sidebar.file_uploader(label="Choose a file", type="pdf", accept_multiple_files=False)

if uploaded_file:
    # Read the uploaded file once and reuse the content
    file_contents = uploaded_file.read()

    # Cache the processing of images and text
    images = get_images(BytesIO(file_contents))
    text_l = get_text(BytesIO(file_contents))
    
    # Combine the extracted text from all pages
    text = '\n'.join([f'page {i}: {txt}' for i, txt in enumerate(text_l)])
    
    # OpenAI API call
    openai_api_key = os.getenv('OPENAI_API_KEY')
    client_openai = load_openai_client(openai_api_key)
    datasets = process_pdf_with_gpt(client_openai, text)
    
    # Save datasets to session state
    st.session_state.datasets = datasets

    # Adjust for the actual number of datasets
    MAX_DATASETS = len(datasets) if datasets else 0

    # Display a message if no dataset is available
    if MAX_DATASETS == 0:
        st.write("No dataset available. Please upload a PDF file to process.")
    else:
        # Function to navigate to the previous dataset
        def prev_dataset():
            if st.session_state.current_dataset > 0:
                st.session_state.current_dataset -= 1

        # Function to navigate to the next dataset
        def next_dataset():
            if st.session_state.current_dataset < MAX_DATASETS - 1:
                st.session_state.current_dataset += 1

        # Get current dataset and image
        current_dataset = st.session_state.datasets[st.session_state.current_dataset]
        data = current_dataset['data']
        
        # Optional: View images only when needed
        if st.sidebar.button("View Images for Current Dataset"):
            image = images[st.session_state.current_dataset]
            st.image(image, caption=f"Image for Dataset {st.session_state.current_dataset + 1}", use_column_width=True)

        # Layout for donor group information
        group_index = st.radio("Select Donor Group", range(len(data)), format_func=lambda x: f"Group {x + 1}")

        # Extract selected group's information
        selected_group = data[group_index]
        donor_names = '\n'.join(selected_group['donor_names_group'])
        amount_donated = selected_group['amount_donated_by_group']
        gift_type = selected_group['gift_type']

        # Prepopulate form for the selected donor group
        with st.form(key='donor_form'):
            st.write(f"Confirm the information for Donor Group {group_index + 1} in Dataset {st.session_state.current_dataset + 1}")

            # Donation date range
            st.markdown("**Donation date range**")
            no_range = st.checkbox("No range available, select assumed donation year")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                month_from = st.selectbox("Month From", range(1, 13), index=0)
            with col2:
                year_from = st.number_input("Year From", value=2024, min_value=1900, max_value=2100)
            with col3:
                month_to = st.selectbox("Month To", range(1, 13), index=11)
            with col4:
                year_to = st.number_input("Year To", value=2024, min_value=1900, max_value=2100)

            # Donation amount
            st.markdown("**Donation amount**")
            col1, col2 = st.columns(2)
            with col1:
                low_amount = st.number_input("Low", min_value=0, value=int(amount_donated[0]) if amount_donated[0] else 0)
            with col2:
                high_amount = st.number_input("High", min_value=0, value=int(amount_donated[1]) if amount_donated[1] else 0)

            # Gift Type
            gift_type = st.selectbox("Gift Type", ["Annual", "Directed", "General Gift"], index=0 if gift_type == 'Annual' else 1 if gift_type == 'Directed' else 2)

            # Donors
            st.markdown("**Donors**")
            donors = st.text_area("Donors", value=donor_names, height=100)

            # Form submission
            submit_button = st.form_submit_button(label='Save Group')

        # Display submitted form data and save to JSON
        if submit_button:
            st.session_state.datasets[st.session_state.current_dataset]['data'][group_index]['donor_names_group'] = donors.splitlines()
            st.session_state.datasets[st.session_state.current_dataset]['data'][group_index]['amount_donated_by_group'] = [low_amount, high_amount]
            st.session_state.datasets[st.session_state.current_dataset]['data'][group_index]['gift_type'] = gift_type

            # Save to a JSON file once changes are completed
            if st.sidebar.button('Save All Changes'):
                with open('donation_information.json', 'w') as json_file:
                    json.dump(st.session_state.datasets, json_file, indent=4)
                st.write("Data saved successfully!")

        # Layout for navigating between datasets
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            st.button("Previous Dataset", on_click=prev_dataset)
        with col2:
            st.write(f"Dataset {st.session_state.current_dataset + 1} of {MAX_DATASETS}")
        with col3:
            st.button("Next Dataset", on_click=next_dataset)