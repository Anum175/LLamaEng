import csv

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

client = Groq(api_key='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')
import preprocessor as p


def index(request):
    return render(request, 'labelling.html')


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


# 3. Function to generate label
def generate_label_for_text(text, labels):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"You are a data labeling tool. Classify each sentence strictly according to the provided labels. If no label matches, classify as 'Other'. Do not provide explanations or comments. Here are the labels: {labels}"
            },
            {
                "role": "user",
                "content": f"{text}"
            }
        ],
        model="llama3-8b-8192",
        temperature=0.2,
        max_tokens=4,
        top_p=1,
        stop=None,
        stream=False,
    )
    return chat_completion.choices[0].message.content


# 4. Function to add labeled data to DataFrame
def add_to_dataframe(df, text, label):
    new_row = {"Text": text, "Label": label}
    return pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)


# Main View Function


def text_labelling(request):
    if request.method == 'POST':
        labels = request.POST.get('labels').split(',')
        file = request.FILES.get('textFile')
        raw_text = request.POST.get('textInput')

        # Step 1: Extract text from file if provided, else use input text
        if file:
            text = extract_text_from_file(file)
        elif raw_text:
            text = raw_text
        else:
            return JsonResponse({"error": "No text input or file provided."}, status=400)

        # Step 2: Split text into chunks
        split_texts = split_text_by_newline(text)

        # Create CSV in memory
        csv_buffer = StringIO()
        csv_writer = csv.writer(csv_buffer, quoting=csv.QUOTE_ALL)

        # Write header
        csv_writer.writerow(['Text', 'Label'])

        # Write data rows
        for split_text in split_texts:
            label = generate_label_for_text(split_text, labels=labels)
            csv_writer.writerow([split_text, label])

        # Create the HTTP response with CSV content
        response = HttpResponse(
            content=csv_buffer.getvalue().encode('utf-8-sig'),
            content_type='text/csv; charset=utf-8-sig'
        )
        response['Content-Disposition'] = 'attachment; filename="labeled_data.csv"'

        return response

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

            # Determine file type and load data
            if uploaded_file and uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file and uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                return JsonResponse({'error': 'Unsupported file format.'})

            # Identify the sentence column
            sentence_column, _ = identify_columns(df)
            if not sentence_column:
                return JsonResponse({'error': 'Could not identify the sentence column.'})

            # Apply preprocessing options
            if remove_duplicates:
                df = remove_duplicates_func(df)

            if clean_text:
                df[sentence_column] = df[sentence_column].apply(
                    lambda x: find_unknown_words(str(x)) if pd.notnull(x) else x
                )

            if remove_stopwords:
                df[sentence_column] = df[sentence_column].apply(remove_stopwords_func)

            # Create the CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="processed_data.csv"'

            # Convert DataFrame to CSV without index
            csv_data = df.to_csv(index=False, encoding='utf-8-sig')
            response.write(csv_data)

            return response

        except Exception as e:
            return JsonResponse({'error': str(e)})

    return render(request, 'preprocessing.html')

# Helper Functions

def identify_columns(df):
    """Identify sentence and label columns by analyzing text data."""
    sentence_column = None
    label_column = None

    for col in df.columns:
        unique_ratio = df[col].nunique() / len(df)
        if df[col].dtype == 'O' and unique_ratio < 0.9:  # Likely explanatory
            sentence_column = col
        elif unique_ratio >= 0.9:  # Likely output/label
            label_column = col

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
