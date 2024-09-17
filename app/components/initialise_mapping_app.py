import streamlit as st
import fsspec

from .get_recommendations import get_embeddings, get_recommendations
from .generate_descriptions import generate_descriptions, convert_pdf_to_txt

from dotenv import dotenv_values

fs = fsspec.filesystem("")

results_path = "results"
input_path = "input"
preprocess_path = "preprocess"

def delete_files_and_folders(directory_path):
    files_and_dirs = fs.ls(directory_path)
    for item in files_and_dirs:
        if fs.isdir(item):
            fs.rm(item, recursive=True)
        else:
            fs.rm(item)

def modify_env(key,value=None, delete = False):
    if not fs.exists(".env"):
        with open(".env", 'w'):
            pass 
    with open(".env", 'r') as file:
        lines = file.readlines()
    if not delete:
        line_replaced = False
        for i in range(len(lines)):
            if lines[i].startswith(key):
                lines[i] = key + '=' + value + '\n'
                line_replaced = True
                break
        if not line_replaced:
            lines.append(key + '=' + value + '\n')
    else:
        for i in range(len(lines)):
            if lines[i].startswith(key):
                lines[i] = ""
    with open(".env", 'w') as file:
        file.writelines(lines)

def initialise_mapping_recommendations():
    config = dotenv_values(".env")

    use_local_model = st.checkbox("Use Local Model", value='local_model' in config)

    if use_local_model:
        st.write(":green[Local model option enabled]")
        local_model_path = st.text_input("Enter the path to your local model (.gguf file)", value=config.get('local_model', ''))
        if st.button("Set Local Model", key='set_local_model'):
            modify_env('local_model', local_model_path)
            del st.session_state['set_local_model']
            st.rerun()
        if 'local_model' in config:
            st.write(f":green[Local model already set: {config['local_model']} :white_check_mark:]")
    else:
        if 'OpenAI_api_key' not in config:
            st.write(":red[No OpenAI key detected, please insert a key below]")
            OpenAI_api_key = st.text_input("OpenAI_api_key", value="", type="password")
            if st.button("Add Key", key='submit'):
                modify_env('OpenAI_api_key', OpenAI_api_key)
                del st.session_state['submit']
                st.rerun()
        else:
            st.write(f":green[OpenAI_api_key detected :white_check_mark:]")

    reset = st.button(":red[Reset LLM Configuration]", key='reset')
    if reset:
        modify_env('OpenAI_api_key', delete=True)
        modify_env('local_model', delete=True)
        del st.session_state['reset']
        st.rerun()
    
    st.divider()

    defailt_init_prompt = "As an AI, you're given the task of translating short variable names from a public health study into the most likely full variable name."

    init_prompt = st.text_input('Initialisation Prompt', value="As an AI, you're given the task of translating short variable names from a public health study into the most likely full variable name.")
    
    if 'init_prompt' not in list(config):
        modify_env('init_prompt',init_prompt)
    elif list(config) != defailt_init_prompt:
        modify_env('init_prompt',init_prompt)
    else:
        pass
    
    st.divider()
    
    if fs.exists(f'{input_path}/target_variables.csv'):
        if fs.exists(f'{input_path}/target_variables_with_embeddings.csv'):
            st.write(":green[Codebook Uploaded and Embeddings Fetched :white_check_mark:]")
        else:
            st.write(":green[Codebook Uploaded, ] :red[Embeddings Not Fetched]")
    else:
        st.write(":red[Please Upload a Codebook]")

    avail_studies = []
    avail_studies = [f for f in fs.ls(f"{input_path}/") if fs.isdir(f)]
    avail_studies = [f.split('/')[-1] for f in avail_studies if f.split('/')[-1][0] != '.']
    uploaded = [x for x in avail_studies if fs.exists(f"{input_path}/{x}/dataset_variables.csv")]
    mapped = [x for x in avail_studies if fs.exists(f'{input_path}/{x}/dataset_variables_with_recommendations')]

    if len(uploaded) > 0 :
        if len(uploaded) == len(mapped):
            st.write(f":green[{len(uploaded)} studies have been uploaded and recommendations created for all of them. :white_check_mark:]")
        else:
            st.write(f":green[{len(uploaded)} studies have been uploaded.] :red[{len(mapped)} studies have had recommendations created for them.]")
    else:
         st.write(":red[Please upload a study to map]")

    run = st.button("Run Recommendation Engine", key = 'run')
    if run:
        with st.spinner('Phoning a friend :coffee:...'):
            convert_pdf_to_txt()
            generate_descriptions()
            get_embeddings()
            get_recommendations()
            del st.session_state['run'] 
            # I need to use session states the above is a hack to fix death looping 
            # see https://discuss.streamlit.io/t/how-should-st-rerun-behave/54153/2
            st.rerun()

    st.divider()

    clear = st.button(":red[Clear Workspace]", key = 'clear')
    if clear:
        delete_files_and_folders("input/")
        delete_files_and_folders("results/")
        del st.session_state['clear'] 
        # I need to use session states the above is a hack to fix death looping 
        # see https://discuss.streamlit.io/t/how-should-st-rerun-behave/54153/2
        st.rerun()



