# required imports
from flask import Flask, request, render_template
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename
import os
from wtforms.validators import InputRequired
import PyPDF2

# setup variables
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mykey'
app.config['UPLOAD_FOLDER'] = 'static/files'
global keywords, filePath
keywords, matches = [], []
filePath, score = '', ''
# results = open('Resume Parser/results.txt', 'w+')

# UploadFileForm class used to upload file from HTML
class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    submit = SubmitField("Upload File")


# url schema
@app.route('/', methods=['GET', 'POST'])
@app.route('/submit', methods=['GET', 'POST'])
def submit():
    global keywords, score, matches, filePath
    errorMessage, scoreMessage, matchesMessage, uploadResult = '', '', '', ''

    if request.method == "POST":

        # when the submit keyword button is clicked
        if 'kw' in request.form:
            keyword = request.form['kw']
            if keyword != '' and not keyword.isspace() and " " not in list(keyword):
                keywords.append(keyword)
            elif " " in list(keyword):
                splitWord = keyword.split(' ')
                for i in splitWord:
                    if i.isspace() == False and i != '':
                        keywords.append(i)

        # when the reset button is  clicked
        elif 'r' in request.form:
            keywords = []

    # when the upload file button is clicked
    form = UploadFileForm()
    if form.validate_on_submit():
        file = form.file.data
        # check if file is a pdf
        if file.filename.rsplit('.', 1)[1].lower() == 'pdf':
            # generate path and filename
            filePath = os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename))
            file.save(filePath)
            uploadResult = "File uploaded successfully."
        else:
            uploadResult = "Invalid file type (.pdf only)."

    # when the parse button is clicked
    if 'p' in request.form and filePath != '' and len(keywords) > 0:
        resumewords = pdfToText(filePath)
        score, matches = matchKeywords(keywords, resumewords)
        score = round(score*100, 2)
        scoreMessage = 'Score: ' + str(score) + '%'
        matchesMessage = 'Matching words: ' + str(matches)
        with open("results.txt", "a") as fo:
            fo.write(str(score) + '%\t\t\n\tFILEPATH: ' + str(filePath) + '\t\t\n\tKEYWORDS: ' + str(keywords) + '\t\t\n\tMATCHES: ' + str(matches) + '\t\t\n\n')
    elif filePath == '':
        errorMessage = 'Please upload a file.'
    elif len(keywords) == 0:
        errorMessage = 'Please enter keywords.'

    keywords = formatWordlist(keywords)

    # render HTML
    return render_template('submit.html', form=form, keywords=keywords, scoreMessage=scoreMessage, matchesMessage=matchesMessage, uploadResult=uploadResult, errorMessage=errorMessage)


# page to review submitted resumes
@app.route('/review', methods=['GET', 'POST'])
def review():
    with open("results.txt", 'r') as fi:
        results = str(fi.read())
    # render HTML
    return render_template('review.html', results=results)


# format keywords to be lowercase and have no special characters or spaces
def formatWordlist(wordlist):
    # set all strings to lowercase
    wordlist = [x.lower() for x in wordlist]

    # remove all special characters
    removetable = str.maketrans('', '', " ~`!@#$%^&*()_-+=<>,.;:'?/\|{]}[•–\n")
    wordlist = [s.translate(removetable) for s in wordlist]

    return list(set(wordlist))


# convert pdf file to text understandable by python
def pdfToText(path):
    # creating a pdf file object
    pdfFileObj = open(path, 'rb')
    # creating a pdf reader object
    pdfReader = PyPDF2.PdfReader(pdfFileObj)
    # creating a page object
    pageObj = pdfReader.pages[0]
    # extracting text from page
    resumeText = pageObj.extract_text()
    # closing the pdf file object
    pdfFileObj.close()
    # split text by spaces and only store unique values
    textArray = set(resumeText.split(" "))
    # set all values to lowercase
    textArray = [x.lower() for x in textArray]
    # remove all special characters
    removetable = str.maketrans('', '', " ~`!@#$%^&*()_-+=<>,.;:'?/\|{]}[•–\n")
    textArray = [s.translate(removetable) for s in textArray]

    return list(set(textArray))


# match keywords with words in resume and score the resume based off of how many matches there were
def matchKeywords(keywords, resumewords):
    matches = 0
    matchedWords = []
    for word in keywords:
        if word in resumewords:
            matches += 1
            matchedWords.append(word)
    score = matches/len(keywords)
    return score, matchedWords


if __name__ == '__main__':
    app.run(debug=False)
