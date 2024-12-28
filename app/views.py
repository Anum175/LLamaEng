import csv
import os
# hasnain Muavia author
import pandas as pd
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from docx import Document
import re
from groq import Groq
import csv
from io import StringIO
from django.http import HttpResponse
import nltk
import json
import dotenv
import preprocessor as p
from nltk import sent_tokenize

nltk_data_dir = './static/nltk_data'

dotenv.load_dotenv()
api = os.environ.get("API_KEY")
client = Groq(api_key=api)

def picture_labelling(request):
    return render(request, 'labelling.html')


# 1. Function to extract text from a file (supports .txt, .doc, .docx)
def extract_text_from_file(file):
    if file.name.endswith('.txt'):
        return file.read().decode('utf-8')
    elif file.name.endswith('.doc') or file.name.endswith('.docx'):
        doc = Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        raise ValueError("Unsupported file format. Only .txt, .doc, and .docx are supported.")


# 2. Function to split text by newline
def split_text_by_newline(text):
    return [line.strip() for line in text.splitlines() if line.strip()]


# 1. Split text into sentences or lines dynamically
def split_text(input_text):
    """
    Splits the input into sentences or lines based on input format.
    Handles both paragraphs and separated lines.
    """
    if '\n' in input_text:  # If newlines are present, treat as separated lines
        return [line.strip() for line in input_text.splitlines() if line.strip()]
    else:  # Otherwise, treat as paragraph and split into sentences
        return sent_tokenize(input_text)

# 2. Generate labels for a batch of sentences
def generate_labels_for_batch(sentences, labels):
    """
    Sends a batch of sentences to the LLM API for labeling.
    """
    input_text = "\n".join(sentences)
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are a data labeling tool. Classify each sentence strictly according to the provided labels. "
                    f"If no label matches, classify as 'Other'. Do not provide explanations or comments. "
                    f"Here are the labels: {labels}"
                ),
            },
            {
                "role": "user",
                "content": input_text,
            },
        ],
        model="llama3-8b-8192",
        temperature=0.2,
        max_tokens=len(sentences) * 10,
        top_p=1,
        stream=False,
    )
    # Parse the response to extract labels for each sentence
    labels_output = response.choices[0].message.content.splitlines()
    return [{"Text": sent, "Label": lbl} for sent, lbl in zip(sentences, labels_output)]

# 3. Extract text from uploaded file
def extract_text_from_file(file):
    """
    Extracts text content from an uploaded file.
    """
    return file.read().decode('utf-8')

# Main View Function
def text_labelling(request):
    """
    Handles the text labeling view logic.
    """
    if request.method == 'POST':
        # Step 1: Get input labels and text
        labels = request.POST.get('labels').split(',')  # Example: ['Label1', 'Label2', 'Other']
        print('labels',labels)
        file = request.FILES.get('textFile')  # Uploaded file
        raw_text = request.POST.get('textInput')  # Raw text input

        # Step 2: Extract and preprocess text
        if file:
            text = extract_text_from_file(file)
        elif raw_text:
            text = raw_text
        else:
            return JsonResponse({"error": "No text input or file provided."}, status=400)

        # Step 3: Split text into sentences or lines
        sentences = split_text(text)

        # Step 4: Batch process sentences
        batch_size = 10  # Define batch size
        results = []
        for i in range(0, len(sentences), batch_size):
            batch = sentences[i:i + batch_size]  # Slice batch
            batch_labels = generate_labels_for_batch(batch, labels)  # Call LLM API
            results.extend(batch_labels)

        # Step 5: Convert results to DataFrame
        df = pd.DataFrame(results)

        # Step 6: Write DataFrame to CSV
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)

        # Step 7: Create HTTP response with CSV content
        response = HttpResponse(
            content=csv_buffer.getvalue(),
            content_type='text/csv; charset=utf-8-sig'
        )
        response['Content-Disposition'] = 'attachment; filename="labeled_data.csv"'
        return response

    # Render the HTML page for text labeling
    return render(request, 'labelling.html')
# data pre processing code starts from here


# Define a manual list of common English stopwords
STOP_WORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
    "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an",
    "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about",
    "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up",
    "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should",
    "now"
}


def data_preprocessing(request):
    if request.method == 'POST':
        try:
            # Fetch file and options from request
            uploaded_file = request.FILES.get('file')
            remove_duplicates = request.POST.get('checkbox_duplicates') == 'true'
            clean_text = request.POST.get('checkbox_clean') == 'true'
            remove_stopwords = request.POST.get('checkbox_stopwords') == 'true'
            context_mode = request.POST.get('checkbox_context') == 'true'

            # Validate and read the file with explicit encoding
            if uploaded_file and uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            elif uploaded_file and uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                return JsonResponse({'error': 'Unsupported file format.'}, status=400)

            # Identify the sentence column
            sentence_column, _ = identify_columns(df)
            if not sentence_column:
                return JsonResponse({'error': 'Could not identify the sentence column.'}, status=400)

            # Apply preprocessing options
            if remove_duplicates:
                df = remove_duplicates_func(df)
            if clean_text:
                df[sentence_column] = df[sentence_column].apply(
                    lambda x: clean_text_func(str(x)) if pd.notnull(x) else x
                )
            if remove_stopwords:
                df[sentence_column] = df[sentence_column].apply(remove_stopwords_func)
            if context_mode:
                df[sentence_column] = df[sentence_column] = df[sentence_column].apply(
                    lambda x: find_unknown_words(str(x)) if pd.notnull(x) else x
                )

            # Create the CSV response with explicit encoding
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="processed_data.csv"'

            # Add BOM for Excel compatibility
            response.write(u'\ufeff')

            # Write CSV with explicit encoding
            df.to_csv(response, index=False, encoding='utf-8')
            return response

        except Exception as e:
            return JsonResponse({'error': f"An error occurred: {str(e)}"}, status=500)

    return render(request, 'preprocessing.html')

# Helper Functions

def identify_columns(df):
    """
    Identify sentence and label columns by comparing text length of first row.
    Longer text is considered the sentence column, shorter text is the label column.
    """
    sentence_column = None
    label_column = None

    # Get first row text lengths for each column
    lengths = {}
    for col in df.columns:
        if df[col].dtype == 'O':  # Only check string columns
            first_value = str(df[col].iloc[0])
            lengths[col] = len(first_value)

    # If we found text columns, assign based on length
    if lengths:
        # Get column with max length as sentence column
        sentence_column = max(lengths, key=lengths.get)
        # Get column with min length as label column
        label_column = min(lengths, key=lengths.get)

        # If only one column found, it's the sentence column
        if len(lengths) == 1:
            label_column = None

    return sentence_column, label_column


def remove_duplicates_func(df):
    """Remove duplicate rows."""
    return df.drop_duplicates()


def clean_text_func(text):
    """Clean text by removing emojis, usernames, URLs, and special characters."""
    p.set_options(p.OPT.URL, p.OPT.EMOJI, p.OPT.MENTION, p.OPT.HASHTAG)
    return p.clean(text)


def remove_stopwords_func(text):
    """Remove stopwords from text."""
    words = text.split()
    return ' '.join([word for word in words if word.lower() not in STOP_WORDS])


def find_unknown_words(text):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a data cleaner tool. Your task is to identify words within a sentence that are meaningless or incorrect in context. "
                    "Replace only those words, ensuring that the overall sentence structure and intended meaning remain intact. "
                    "Do not alter any words that fit well within the sentence context. just provide the whole sentence witth the altered words without any additional speech or comments"
                )
            },
            {
                "role": "user",
                "content": f"{text}"
            }
        ],
        model="llama3-8b-8192",
        temperature=0.2,
        max_tokens=128,
        top_p=1,
        stop=None,
        stream=False,
    )
    return chat_completion.choices[0].message.content
